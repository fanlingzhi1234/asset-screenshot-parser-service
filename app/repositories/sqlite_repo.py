from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from app.api.schemas.common import utc_now_iso


class SQLiteRepository:
    def __init__(self, database_url: str) -> None:
        self.db_path = self._resolve_sqlite_path(database_url)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def list_templates(self) -> list[dict[str, Any]]:
        return self._list("templates")

    def upsert_template(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._upsert("templates", "template_id", item["template_id"], item)

    def list_cases(self) -> list[dict[str, Any]]:
        return self._list("cases")

    def upsert_case(self, item: dict[str, Any]) -> dict[str, Any]:
        return self._upsert("cases", "case_id", item["case_id"], item)

    def create_snapshot(self, item: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        payload = {**item, "created_at": now, "updated_at": now}
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO snapshots (request_id, payload, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (payload["request_id"], json.dumps(payload, ensure_ascii=False), now, now),
            )
        return payload

    def _list(self, table: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(f"SELECT payload FROM {table} ORDER BY updated_at DESC").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def _upsert(self, table: str, key_column: str, key: str, item: dict[str, Any]) -> dict[str, Any]:
        now = utc_now_iso()
        with self._connect() as conn:
            existing = conn.execute(f"SELECT payload FROM {table} WHERE {key_column} = ?", (key,)).fetchone()
            created_at = now
            if existing:
                created_at = json.loads(existing["payload"]).get("created_at") or now
            payload = {**item, "created_at": created_at, "updated_at": now}
            conn.execute(
                f"""
                INSERT INTO {table} ({key_column}, payload, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT({key_column}) DO UPDATE SET
                  payload = excluded.payload,
                  updated_at = excluded.updated_at
                """,
                (key, json.dumps(payload, ensure_ascii=False), created_at, now),
            )
        return payload

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS templates (
                  template_id TEXT PRIMARY KEY,
                  payload TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cases (
                  case_id TEXT PRIMARY KEY,
                  payload TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                  request_id TEXT PRIMARY KEY,
                  payload TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  updated_at TEXT NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def _resolve_sqlite_path(database_url: str) -> Path:
        prefix = "sqlite:///"
        if database_url.startswith(prefix):
            return Path(database_url[len(prefix):]).expanduser()
        return Path(database_url).expanduser()

