from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .client import CapitalistClient, CapitalistError
from .env import load_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="capitalist", description="CLI for the Capitalist Integration API.")
    parser.add_argument("--base-url", help="Override API base URL. Defaults to CAPITALIST_BASE_URL or api2.capitalist.net.")
    parser.add_argument("--env-file", help="Load environment variables from this file. Defaults to .env if present.")
    parser.add_argument("--raw", action="store_true", help="Print raw JSON scalars without pretty formatting.")
    sub = parser.add_subparsers(dest="command", required=True)

    accounts = sub.add_parser("accounts", help="List accounts by currency.")
    accounts.add_argument("--currency", required=True, help="Currency code, for example USD, RUR, USDTt.")

    rate = sub.add_parser("rate", help="Get exchange rate.")
    rate.add_argument("--from", dest="currency_from", required=True, help="Source currency.")
    rate.add_argument("--to", dest="currency_to", required=True, help="Target currency.")

    deposit = sub.add_parser("deposit-address", help="Get a crypto deposit address for an account and currency.")
    deposit.add_argument("--account", required=True, help="Capitalist account code.")
    deposit.add_argument("--currency", required=True, help="Currency code, for example USDTt for USDT TRC-20.")

    usdt = sub.add_parser(
        "usdt-trc20-address",
        help="Get current USDT TRC-20 deposit address with autoconversion to the account.",
    )
    usdt.add_argument("--account", required=True, help="Capitalist account code to credit.")

    status_doc = sub.add_parser("payment-document", help="Get payment status by document ID.")
    status_doc.add_argument("document_id")

    status_req = sub.add_parser("payment-request", help="Get payment status by userRequestId.")
    status_req.add_argument("user_request_id")

    whitelist = sub.add_parser("whitelist", help="Manage Capitalist API IP whitelist.")
    whitelist_sub = whitelist.add_subparsers(dest="whitelist_command", required=True)
    whitelist_sub.add_parser("list", help="List whitelisted IPs.")
    whitelist_add = whitelist_sub.add_parser("add", help="Add IPs to whitelist.")
    whitelist_add.add_argument("ips", nargs="+")
    whitelist_remove = whitelist_sub.add_parser("remove", help="Remove IPs from whitelist.")
    whitelist_remove.add_argument("ips", nargs="+")

    return parser


def run(args: argparse.Namespace) -> Any:
    client = CapitalistClient(base_url=args.base_url)

    if args.command == "accounts":
        return client.list_accounts(args.currency)
    if args.command == "rate":
        return client.exchange_rate(args.currency_from, args.currency_to)
    if args.command == "deposit-address":
        return client.deposit_address(args.account, args.currency)
    if args.command == "usdt-trc20-address":
        return client.usdt_trc20_autoconvert_address(args.account)
    if args.command == "payment-document":
        return client.payment_status_by_document(args.document_id)
    if args.command == "payment-request":
        return client.payment_status_by_request(args.user_request_id)
    if args.command == "whitelist":
        if args.whitelist_command == "list":
            return client.whitelist()
        if args.whitelist_command == "add":
            return client.add_whitelist_ips(args.ips)
        if args.whitelist_command == "remove":
            return client.remove_whitelist_ips(args.ips)

    raise CapitalistError(f"Unknown command: {args.command}")


def print_result(result: Any, *, raw: bool) -> None:
    if isinstance(result, str):
        print(result)
        return
    if raw:
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        return
    print(json.dumps(result, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    load_env_file(args.env_file)
    try:
        print_result(run(args), raw=args.raw)
        return 0
    except CapitalistError as exc:
        print(f"capitalist: error: {exc}", file=sys.stderr)
        if exc.payload is not None:
            print(json.dumps(exc.payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
