# Capitalist Integration API Summary

Source documentation: https://docs.capitalist.net/api/integration-api.html, checked 2026-06-22. The page reports "Last updated 2026-06-16 08:42:34 UTC".

## Base URL

Use `https://api2.capitalist.net/`.

## Authentication

Send these headers on every API request:

- `API-Key`: API key from the Capitalist account security settings.
- `X-Request-Timestamp`: current epoch timestamp in milliseconds.
- `Signature`: SHA-256 hex digest of `X-Request-Timestamp + request body + API-secret`.

For GET requests with no body, sign the empty body string. For JSON requests, sign exactly the bytes being sent; use compact JSON without extra spaces for deterministic signatures.

API access requires enabled API access and Google 2FA in the Capitalist account. API methods may also be restricted by IP whitelist.

## Common Endpoints

- `GET /v1/account/list?currency=<code>`: list accounts by currency.
- `GET /v1/rate?from=<code>&to=<code>`: get exchange rate.
- `GET /v1/payment/document/{documentId}`: payment status by document ID.
- `GET /v1/payment/{userRequestId}`: payment status by caller-provided request ID.
- `GET /v1/whitelist`: read API IP whitelist.
- `POST /v1/whitelist` with `{"ip":["1.2.3.4"]}`: add IPs or wildcard patterns.
- `POST /v1/whitelist/remove` with `{"ip":["1.2.3.4"]}`: remove IPs or wildcard patterns.

## Deposit Addresses

- `GET /v1/depositAddress/{currency}`: get a cryptocurrency deposit address for the currency.
- `GET /v1/depositAddressAutoUSDTt/{account}`: get a USDT TRC-20 deposit address that will automatically convert and credit the given account.

Deposit addresses are not permanent. The docs warn not to save or cache them; the maximum validity guarantee is 8 hours. Use `GET /v1/depositAddress/USDTt` when the user needs a plain USDT TRC-20 address without conversion. Use `depositAddressAutoUSDTt` only when the user explicitly wants automatic conversion to a Capitalist account.

Currency codes relevant to USDT:

- `USDT`: USDT ERC-20.
- `USDTt`: USDT TRC-20.
- `USDTb`: USDT BEP-20.

Payment payload type for outgoing USDT TRC-20 crypto payments is `USDTTRC20`.

## Error Handling

Capitalist returns JSON error responses like `{"error":"..."}`. Surface the error text to the operator, and include raw JSON only in logs or debug output.

For polling payment statuses more than 20 times per minute, use callbacks instead. Excessive API calls may be throttled.
