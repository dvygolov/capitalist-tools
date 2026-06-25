# Capitalist Tools

Small Python toolkit for the Capitalist Integration API:

- signed API client;
- CLI for accounts, rates, payment status, whitelist, and deposit addresses;
- Telegram bot that returns the current USDT TRC-20 deposit address only to allowed users;
- optional Codex skill under `codex-skills/capitalist-api`.

The implementation uses only the Python standard library.

## API Coverage

The client signs requests according to the Capitalist Integration API docs:

```text
Signature = sha256(X-Request-Timestamp + request_body + API-secret)
```

Default API base URL:

```text
https://api2.capitalist.net
```

For USDT TRC-20 autoconversion addresses, the CLI and bot call:

```text
GET /v1/depositAddressAutoUSDTt/{account}
```

Those addresses are fetched fresh on every request and are not cached.

## Configuration

Create a local `.env` file or export variables in the shell:

```env
CAPITALIST_API_KEY=your_api_key
CAPITALIST_API_SECRET=your_api_secret
CAPITALIST_ACCOUNT=your_capitalist_account
CAPITALIST_BASE_URL=https://api2.capitalist.net

TELEGRAM_BOT_TOKEN=your_telegram_bot_token
CAPITALIST_ALLOWED_USERS=your_numeric_telegram_user_id,@telegram_username
```

Prefer numeric Telegram user IDs in `CAPITALIST_ALLOWED_USERS`. Usernames are supported as a convenience but can change.

## CLI

```powershell
python -m capitalist_tools.cli usdt-trc20-address --account your_capitalist_account
python -m capitalist_tools.cli accounts --currency USDTt
python -m capitalist_tools.cli rate --from USD --to EUR
python -m capitalist_tools.cli whitelist list
```

## Telegram Bot

```powershell
python -m capitalist_tools.telegram_bot
```

Unauthorized users receive no reply and no keyboard. Allowed users receive a persistent button named:

```text
Текущий адрес USDT TRC20
```

On `/start` or button press, the bot fetches the current Capitalist USDT TRC-20 address and sends it.

## Tests

```powershell
python -m unittest discover -s tests -v
python -m compileall -q capitalist_tools tests
```
