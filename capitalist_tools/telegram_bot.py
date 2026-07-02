from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .client import CapitalistClient, CapitalistError
from .env import is_placeholder, load_env_file


BUTTON_TEXT = "Текущий адрес USDT TRC20"


@dataclass(frozen=True)
class BotConfig:
    token: str
    allowed_ids: frozenset[int]
    allowed_usernames: frozenset[str]
    poll_timeout: int = 30

    @classmethod
    def from_env(cls) -> "BotConfig":
        load_env_file()
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if is_placeholder(token):
            raise RuntimeError("Set TELEGRAM_BOT_TOKEN.")
        allowed_ids, allowed_usernames = parse_allowed_users(os.environ.get("CAPITALIST_ALLOWED_USERS", ""))
        return cls(
            token=token,
            allowed_ids=frozenset(allowed_ids),
            allowed_usernames=frozenset(allowed_usernames),
        )


def parse_allowed_users(value: str) -> tuple[set[int], set[str]]:
    ids: set[int] = set()
    usernames: set[str] = set()
    for item in (part.strip() for part in value.split(",")):
        if not item:
            continue
        if item.lstrip("-").isdigit():
            ids.add(int(item))
        else:
            usernames.add(item.removeprefix("@").lower())
    return ids, usernames


class TelegramApi:
    def __init__(self, token: str) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"

    def get_updates(self, *, offset: int | None, timeout: int) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"timeout": timeout, "allowed_updates": json.dumps(["message"])}
        if offset is not None:
            params["offset"] = offset
        data = self._request("getUpdates", params)
        return data if isinstance(data, list) else []

    def send_message(self, chat_id: int, text: str, *, show_keyboard: bool) -> None:
        payload: dict[str, Any] = {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
        if show_keyboard:
            payload["reply_markup"] = json.dumps(
                {
                    "keyboard": [[{"text": BUTTON_TEXT}]],
                    "resize_keyboard": True,
                    "one_time_keyboard": False,
                    "is_persistent": True,
                },
                ensure_ascii=False,
            )
        self._request("sendMessage", payload)

    def _request(self, method: str, params: dict[str, Any]) -> Any:
        data = urllib.parse.urlencode(params).encode("utf-8")
        req = urllib.request.Request(f"{self.base_url}/{method}", data=data, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Telegram request failed: {exc}") from exc
        if not payload.get("ok"):
            raise RuntimeError(f"Telegram API error in {method}: {payload}")
        return payload.get("result")


def is_allowed(user: dict[str, Any], config: BotConfig) -> bool:
    user_id = user.get("id")
    username = str(user.get("username") or "").lower()
    if isinstance(user_id, int) and user_id in config.allowed_ids:
        return True
    return bool(username and username in config.allowed_usernames)


def should_answer(text: str) -> bool:
    return text == "/start" or text == BUTTON_TEXT


def handle_message(message: dict[str, Any], *, config: BotConfig, telegram: TelegramApi, capitalist: CapitalistClient) -> None:
    user = message.get("from") or {}
    if not is_allowed(user, config):
        return

    text = str(message.get("text") or "").strip()
    if not should_answer(text):
        return

    chat = message.get("chat") or {}
    chat_id = chat.get("id")
    if not isinstance(chat_id, int):
        return

    try:
        address = capitalist.usdt_trc20_address()
    except CapitalistError as exc:
        telegram.send_message(chat_id, f"Ошибка Capitalist API: {exc}", show_keyboard=True)
        return

    telegram.send_message(chat_id, address, show_keyboard=True)


def run_forever(config: BotConfig | None = None) -> None:
    config = config or BotConfig.from_env()
    telegram = TelegramApi(config.token)
    capitalist = CapitalistClient()
    offset: int | None = None

    while True:
        try:
            updates = telegram.get_updates(offset=offset, timeout=config.poll_timeout)
            for update in updates:
                update_id = update.get("update_id")
                if isinstance(update_id, int):
                    offset = update_id + 1
                message = update.get("message")
                if isinstance(message, dict):
                    handle_message(message, config=config, telegram=telegram, capitalist=capitalist)
        except Exception as exc:
            print(f"telegram bot loop error: {exc}", flush=True)
            time.sleep(5)


def main() -> int:
    run_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
