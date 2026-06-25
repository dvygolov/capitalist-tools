---
name: capitalist-api
description: "Work with Capitalist Integration API from Codex: signed API calls, account listing, exchange rates, payment status checks, API whitelist operations, and current cryptocurrency deposit addresses including USDT TRC-20 autoconversion. Use when the user asks about Capitalist, api2.capitalist.net, Capitalist accounts, Capitalist deposit addresses, USDT TRC20/TRC-20 addresses, Capitalist Telegram bots, or Capitalist API automation."
---

# Capitalist API

## Quick Start

Use the repository CLI first when it is available:

```powershell
python -m capitalist_tools.cli usdt-trc20-address --account your_capitalist_account
```

Or run the bundled skill wrapper from the repository root:

```powershell
python codex-skills\capitalist-api\scripts\capitalist_cli.py usdt-trc20-address --account your_capitalist_account
```

The CLI expects credentials in environment variables or a local `.env` file:

- `CAPITALIST_API_KEY`
- `CAPITALIST_API_SECRET`
- Optional `CAPITALIST_BASE_URL`, default `https://api2.capitalist.net`

For the Telegram bot, also require:

- `TELEGRAM_BOT_TOKEN`
- `CAPITALIST_ACCOUNT`
- `CAPITALIST_ALLOWED_USERS`, comma-separated Telegram numeric IDs and/or usernames

## Workflows

For current USDT TRC-20 deposit address with autoconversion, call:

```powershell
python -m capitalist_tools.cli usdt-trc20-address --account <capitalist-account>
```

Do not cache Capitalist autoconversion deposit addresses. Fetch a fresh value for each user-facing request.

For account discovery:

```powershell
python -m capitalist_tools.cli accounts --currency USDTt
```

For payment status:

```powershell
python -m capitalist_tools.cli payment-document <document-id>
python -m capitalist_tools.cli payment-request <user-request-id>
```

For API whitelist:

```powershell
python -m capitalist_tools.cli whitelist list
python -m capitalist_tools.cli whitelist add 203.0.113.10
python -m capitalist_tools.cli whitelist remove 203.0.113.10
```

## Implementation Notes

Read [references/api-summary.md](references/api-summary.md) when implementing or changing API behavior.

Never commit real API keys, API secrets, Telegram bot tokens, account numbers tied to a private wallet flow, or allowlist contents. Use `.env`, process environment, KeePass, or another local secret store.

For Telegram bots, treat numeric Telegram user IDs as the reliable allowlist mechanism. Usernames may change; support them only as a convenience when explicitly configured.
