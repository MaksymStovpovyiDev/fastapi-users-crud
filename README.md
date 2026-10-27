# Users CRUD API

A small learning project built with Python, FastAPI, and local SQLite.
It supports creating, listing, updating, and deleting users.

## Run

Requires Python 3.11 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs to try the API.

The application creates `data/app.db` on first startup using `schema.sql`.
The SQL file defines the table; the database file stores the actual users.
The database is local and excluded from Git. No database server is needed.

## Endpoints

| Method | Path | Result |
| --- | --- | --- |
| POST | /users | Create a user (201) |
| GET | /users | List users; limit defaults to 20, maximum 100; offset defaults to 0 |
| GET | /users/{id} | Get a user |
| PATCH | /users/{id} | Update name or email |
| DELETE | /users/{id} | Delete a user (204) |

```sh
curl -X POST http://127.0.0.1:8000/users \
  -H 'Content-Type: application/json' \
  -d '{"name": "Alice", "email": "alice@example.com"}'
curl http://127.0.0.1:8000/users
curl -X PATCH http://127.0.0.1:8000/users/1 \
  -H 'Content-Type: application/json' -d '{"name": "Alice Smith"}'
curl -X DELETE http://127.0.0.1:8000/users/1
```

Names are stripped of surrounding whitespace and must contain 1–100 characters.
Email addresses are validated and unique without regard to ASCII letter case.
Missing users return 404, duplicate emails return 409, invalid input returns 422.
PATCH requires at least one field and rejects null values.

## Checks

```sh
pytest
ruff check .
ruff format --check .
```

Tests use temporary SQLite files and do not touch the application database.

## Design

SQL statements use parameters. SQLite enforces email uniqueness. Each request
uses its own connection and transaction, committed on success and rolled back
on failure. Pydantic handles request validation and response schemas.

The built-in sqlite3 module keeps the project small and makes the queries visible.
There is no authentication: this is a local learning example, not a public service.
The schema script initializes new databases; versioned schema migrations would
be needed if the database structure evolves.
