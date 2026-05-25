# Users API

Base URL: https://api.acme.example/v1

## GET /users/{id}
Returns the user with the given id. Response body is JSON of the form:
`{"id": "<string>", "name": "<string>", "email": "<string>", "created_at": "<iso8601>"}`.
Returns 404 if no user exists with that id.

## POST /users
Creates a new user. Request body must be JSON with `name` and `email` fields.
Returns 201 with the created user object, including the server-assigned `id`.
Returns 422 if `email` is not a valid email address.

## PATCH /users/{id}
Updates the name and/or email of an existing user. Only the supplied fields are
modified. Returns 200 with the updated user object.

## DELETE /users/{id}
Permanently deletes the user. Returns 204 on success. This action is
irreversible and also deletes all orders associated with the user.
