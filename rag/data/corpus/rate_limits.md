# Rate Limits

The Acme API enforces per-key rate limits. The default limit is 60 requests per
minute and 10,000 requests per day. Enterprise customers have higher limits;
contact sales to negotiate.

Every response includes three rate-limit headers:
- `X-RateLimit-Limit`: the request quota for the current window
- `X-RateLimit-Remaining`: how many requests remain in the current window
- `X-RateLimit-Reset`: the unix timestamp at which the window resets

When you exceed the limit, the API returns HTTP 429 with a `Retry-After` header
indicating how many seconds to wait before retrying. Clients should implement
exponential backoff on 429 responses.
