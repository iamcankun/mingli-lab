import json
from datetime import datetime, timezone
from typing import Any

from .database import Database


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChartRepository:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _decode(row) -> dict[str, Any] | None:
        if row is None:
            return None
        item = dict(row)
        item["chart"] = json.loads(item.pop("chart_json"))
        return item

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO chart_records
                (name, gender, birth_date, birth_time, birth_place, bazi, day_master, chart_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["name"],
                    data["gender"],
                    data["birth_date"],
                    data["birth_time"],
                    data.get("birth_place", ""),
                    data["bazi"],
                    data.get("day_master", ""),
                    json.dumps(data.get("chart", {}), ensure_ascii=False),
                    _now(),
                ),
            )
            chart_id = cursor.lastrowid
        return self.get(chart_id)

    def list(self, query: str = "") -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            rows = connection.execute(
                "SELECT * FROM chart_records WHERE name LIKE ? ORDER BY created_at DESC, id DESC",
                (f"%{query.strip()}%",),
            ).fetchall()
        return [self._decode(row) for row in rows]

    def get(self, chart_id: int) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM chart_records WHERE id = ?", (chart_id,)).fetchone()
        return self._decode(row)

    def delete(self, chart_id: int) -> bool:
        with self.database.connect() as connection:
            cursor = connection.execute("DELETE FROM chart_records WHERE id = ?", (chart_id,))
        return cursor.rowcount > 0


class ModelSettingsRepository:
    def __init__(self, database: Database):
        self.database = database

    def get(self) -> dict[str, Any] | None:
        with self.database.connect() as connection:
            row = connection.execute("SELECT * FROM model_settings WHERE id = 1").fetchone()
        return dict(row) if row else None

    def save(self, data: dict[str, Any]) -> dict[str, Any]:
        with self.database.connect() as connection:
            connection.execute(
                """INSERT INTO model_settings
                (id, base_url, api_key_encrypted, model_id, temperature, max_tokens, top_p, updated_at)
                VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                base_url=excluded.base_url,
                api_key_encrypted=excluded.api_key_encrypted,
                model_id=excluded.model_id,
                temperature=excluded.temperature,
                max_tokens=excluded.max_tokens,
                top_p=excluded.top_p,
                updated_at=excluded.updated_at""",
                (
                    data["base_url"].rstrip("/"),
                    data.get("api_key_encrypted", ""),
                    data["model_id"],
                    data.get("temperature", 0.2),
                    data.get("max_tokens", 1600),
                    data.get("top_p", 1.0),
                    _now(),
                ),
            )
        return self.get()


class InferenceRepository:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _decode(row) -> dict[str, Any]:
        item = dict(row)
        item["token_usage"] = json.loads(item.pop("token_usage_json"))
        return item

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        with self.database.connect() as connection:
            cursor = connection.execute(
                """INSERT INTO inference_logs
                (chart_id, analysis_type, system_prompt, user_prompt, response, reasoning, token_usage_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data.get("chart_id"),
                    data["analysis_type"],
                    data["system_prompt"],
                    data["user_prompt"],
                    data["response"],
                    data.get("reasoning"),
                    json.dumps(data.get("token_usage", {}), ensure_ascii=False),
                    _now(),
                ),
            )
            item_id = cursor.lastrowid
            row = connection.execute("SELECT * FROM inference_logs WHERE id = ?", (item_id,)).fetchone()
        return self._decode(row)

    def list(self, chart_id: int | None = None) -> list[dict[str, Any]]:
        with self.database.connect() as connection:
            if chart_id is None:
                rows = connection.execute("SELECT * FROM inference_logs ORDER BY id DESC").fetchall()
            else:
                rows = connection.execute(
                    "SELECT * FROM inference_logs WHERE chart_id = ? ORDER BY id DESC", (chart_id,)
                ).fetchall()
        return [self._decode(row) for row in rows]

