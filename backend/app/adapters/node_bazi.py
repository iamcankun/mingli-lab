import json
import os
import subprocess
from pathlib import Path
from typing import Any


class BaziEngineError(RuntimeError):
    pass


class NodeBaziAdapter:
    def __init__(self, script_path: Path | None = None, timeout: float = 10):
        self.script_path = script_path or Path(__file__).resolve().parents[3] / "bazi-engine" / "bazi_local_node.mjs"
        self.timeout = timeout

    def calculate(self, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = self._run(arguments)
        if not payload.get("success") or not isinstance(payload.get("data"), dict):
            raise BaziEngineError(payload.get("error") or "Bazi engine failed")
        return payload["data"]

    def calculate_batch(self, arguments_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        payload = self._run({"mode": "batch", "items": arguments_list})
        data = payload.get("data")
        if not payload.get("success") or not isinstance(data, list):
            raise BaziEngineError(payload.get("error") or "Bazi engine batch failed")
        if len(data) != len(arguments_list):
            raise BaziEngineError("Bazi engine batch returned unexpected item count")
        charts = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("chart"), dict):
                raise BaziEngineError("Bazi engine batch returned invalid item")
            charts.append(item["chart"])
        return charts

    def _run(self, arguments: dict[str, Any]) -> dict[str, Any]:
        try:
            completed = subprocess.run(
                [os.getenv("NODE_BINARY", "node"), str(self.script_path)],
                input=json.dumps(arguments, ensure_ascii=False),
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BaziEngineError(str(exc)) from exc
        if completed.returncode != 0:
            raise BaziEngineError((completed.stderr or completed.stdout or "Bazi engine failed").strip())
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            raise BaziEngineError("Bazi engine returned invalid JSON") from exc
        return payload
