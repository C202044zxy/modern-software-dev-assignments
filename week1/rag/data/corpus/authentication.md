# Authentication

All requests to the Acme API must be authenticated using an API key. You can
generate a key from the developer dashboard at https://dashboard.acme.example/.

Pass the key in the `X-API-Key` header on every request. Requests without a key
return HTTP 401. Requests with an invalid or revoked key return HTTP 403.

API keys are scoped: a `read` key can only call GET endpoints, while a `write`
key can call POST, PATCH, and DELETE endpoints. The scope of a key cannot be
changed after creation; generate a new key with the desired scope instead.

Keys do not expire automatically but can be revoked from the dashboard. Revoking
a key takes effect within 60 seconds. Always store keys in environment variables
and never commit them to source control.
