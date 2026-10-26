import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response

from app.db import DATABASE, connect, init_db
from app.schemas import User, UserCreate, UserUpdate


def get_db(request: Request):
    connection = connect(request.app.state.database)
    try:
        with connection:
            yield connection
    finally:
        connection.close()


Database = Annotated[sqlite3.Connection, Depends(get_db, scope="function")]


def find_user(db: sqlite3.Connection, user_id: int) -> dict:
    row = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return dict(row)


def create_app(database: Path = DATABASE) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db(database)
        yield

    app = FastAPI(title="Users CRUD API", lifespan=lifespan)
    app.state.database = database

    @app.post("/users", response_model=User, status_code=201)
    def create_user(user: UserCreate, db: Database):
        try:
            cursor = db.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (user.name, str(user.email)),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=409, detail="Email already exists"
            ) from error
        return find_user(db, cursor.lastrowid)

    @app.get("/users", response_model=list[User])
    def list_users(
        db: Database,
        limit: Annotated[int, Query(ge=1, le=100)] = 20,
        offset: Annotated[int, Query(ge=0)] = 0,
    ):
        rows = db.execute(
            "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?", (limit, offset)
        ).fetchall()
        return [dict(row) for row in rows]

    @app.get("/users/{user_id}", response_model=User)
    def get_user(user_id: int, db: Database):
        return find_user(db, user_id)

    @app.patch("/users/{user_id}", response_model=User)
    def update_user(user_id: int, changes: UserUpdate, db: Database):
        user = find_user(db, user_id)
        user.update(changes.model_dump(exclude_unset=True))
        try:
            db.execute(
                "UPDATE users SET name = ?, email = ? WHERE id = ?",
                (user["name"], str(user["email"]), user_id),
            )
        except sqlite3.IntegrityError as error:
            raise HTTPException(
                status_code=409, detail="Email already exists"
            ) from error
        return find_user(db, user_id)

    @app.delete("/users/{user_id}", status_code=204)
    def delete_user(user_id: int, db: Database):
        cursor = db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return Response(status_code=204)

    return app


app = create_app()
