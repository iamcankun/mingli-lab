from typing import Any

import httpx


class ModelAdapterError(RuntimeError):
    pass


class OpenAICompatibleAdapter:
    def __init__(self, timeout: float = 60):
        self.timeout = timeout

    @staticmethod
    def _headers(settings: dict[str, Any]) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {settings['api_key']}",
            "Content-Type": "application/json",
        }

    def _request(self, settings: dict[str, Any], payload: dict[str, Any]) -> dict[str, Any]:
        url = f"{settings['base_url'].rstrip('/')}/chat/completions"
        try:
            response = httpx.post(url, headers=self._headers(settings), json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise ModelAdapterError(str(exc)) from exc

    def complete(self, settings: dict[str, Any], messages: list[dict[str, str]]) -> dict[str, Any]:
        data = self._request(
            settings,
            {
                "model": settings["model_id"],
                "messages": messages,
                "temperature": settings["temperature"],
                "max_tokens": settings["max_tokens"],
                "top_p": settings["top_p"],
            },
        )
        try:
            message = data["choices"][0]["message"]
            usage = data.get("usage") or {}
            return {
                "content": message.get("content") or "",
                "reasoning": message.get("reasoning_content"),
                "token_usage": {
                    "prompt_tokens": usage.get("prompt_tokens", 0),
                    "completion_tokens": usage.get("completion_tokens", 0),
                    "total_tokens": usage.get("total_tokens", 0),
                },
            }
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelAdapterError("Malformed model response") from exc

    def test_connection(self, settings: dict[str, Any]) -> dict[str, Any]:
        self.complete(settings, [{"role": "user", "content": "请回复 OK"}])
        return {"ok": True, "message": "连接成功"}

