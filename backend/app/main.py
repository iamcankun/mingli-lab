import json
from datetime import date, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .adapters.node_bazi import BaziEngineError, NodeBaziAdapter
from .adapters.openai_compatible import ModelAdapterError, OpenAICompatibleAdapter
from .database import Database
from .models import ChartCalculateRequest, InferenceRequest, LifeKlineQuery, ModelSettingsRequest
from .prompts import PROMPTS
from .repositories import ChartRepository, InferenceRepository, ModelSettingsRepository
from .security import SecretCipher
from .services.bazi import build_engine_arguments, normalize_chart
from .services.inference import PromptRenderError, render_prompt
from .services.life_kline import build_life_kline


def create_app(data_dir: Path | None = None, bazi_adapter=None, model_adapter=None) -> FastAPI:
    root = Path(data_dir or Path(__file__).resolve().parents[2] / "data")
    app = FastAPI(title="Mingli Lab")
    app.state.data_dir = root
    app.state.database = Database(root / "mingli.sqlite3")
    app.state.charts = ChartRepository(app.state.database)
    app.state.settings = ModelSettingsRepository(app.state.database)
    app.state.inferences = InferenceRepository(app.state.database)
    app.state.cipher = SecretCipher.from_data_dir(root)
    app.state.bazi_adapter = bazi_adapter or NodeBaziAdapter()
    app.state.model_adapter = model_adapter or OpenAICompatibleAdapter()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health():
        return {"status": "ok", "mode": "local"}

    @app.post("/api/charts/calculate")
    def calculate_chart(body: ChartCalculateRequest):
        try:
            raw = app.state.bazi_adapter.calculate(
                build_engine_arguments(body.birth_date, body.birth_time, body.gender)
            )
        except BaziEngineError as exc:
            raise HTTPException(503, detail={"code": "BAZI_ENGINE_UNAVAILABLE", "message": str(exc)})
        chart = normalize_chart(raw)
        record = None
        if body.persist:
            record = app.state.charts.create(
                {
                    "name": body.name,
                    "gender": body.gender,
                    "birth_date": body.birth_date,
                    "birth_time": body.birth_time,
                    "birth_place": " ".join(x for x in [body.province, body.city] if x),
                    "bazi": chart["bazi"],
                    "day_master": chart["day_master"],
                    "chart": chart,
                }
            )
        return {"chart": chart, "record": record}

    @app.get("/api/charts")
    def list_charts(query: str = ""):
        return {"items": app.state.charts.list(query)}

    @app.get("/api/charts/{chart_id}")
    def get_chart(chart_id: int):
        item = app.state.charts.get(chart_id)
        if not item:
            raise HTTPException(404, "Chart not found")
        return item

    @app.get("/api/charts/{chart_id}/life-kline")
    def get_life_kline(chart_id: int, start: date | None = None, end: date | None = None, dimension: str = "overall"):
        item = app.state.charts.get(chart_id)
        if not item:
            raise HTTPException(404, "Chart not found")
        if dimension != "overall":
            raise HTTPException(400, detail={"code": "LIFE_KLINE_INVALID_DIMENSION"})
        today = date.today()
        query = LifeKlineQuery(start=start or today, end=end or today + timedelta(days=1095), dimension=dimension)
        if query.end < query.start:
            raise HTTPException(400, detail={"code": "LIFE_KLINE_INVALID_RANGE"})
        try:
            payload = build_life_kline(
                item["chart"],
                item["gender"],
                app.state.bazi_adapter,
                query.start,
                query.end,
                query.dimension,
            )
        except ValueError as exc:
            raise HTTPException(400, detail={"code": "LIFE_KLINE_INVALID_RANGE", "message": str(exc)})
        except BaziEngineError as exc:
            raise HTTPException(503, detail={"code": "BAZI_ENGINE_UNAVAILABLE", "message": str(exc)})
        return {"chart_id": chart_id, **payload}

    @app.delete("/api/charts/{chart_id}", status_code=204)
    def delete_chart(chart_id: int):
        if not app.state.charts.delete(chart_id):
            raise HTTPException(404, "Chart not found")
        return Response(status_code=204)

    def public_settings(item):
        if not item:
            return {
                "base_url": "",
                "model_id": "",
                "temperature": 0.2,
                "max_tokens": 1600,
                "top_p": 1.0,
                "api_key_configured": False,
            }
        return {
            "base_url": item["base_url"],
            "model_id": item["model_id"],
            "temperature": item["temperature"],
            "max_tokens": item["max_tokens"],
            "top_p": item["top_p"],
            "api_key_configured": bool(item["api_key_encrypted"]),
        }

    def decrypted_settings():
        item = app.state.settings.get()
        if not item:
            raise HTTPException(400, detail={"code": "MODEL_NOT_CONFIGURED"})
        result = dict(item)
        result["api_key"] = (
            app.state.cipher.decrypt(result["api_key_encrypted"]) if result["api_key_encrypted"] else ""
        )
        return result

    @app.get("/api/settings/model")
    def get_settings():
        return public_settings(app.state.settings.get())

    @app.put("/api/settings/model")
    def save_settings(body: ModelSettingsRequest):
        existing = app.state.settings.get()
        encrypted = existing["api_key_encrypted"] if existing else ""
        if body.api_key:
            encrypted = app.state.cipher.encrypt(body.api_key)
        saved = app.state.settings.save(
            {**body.model_dump(exclude={"api_key"}), "api_key_encrypted": encrypted}
        )
        return public_settings(saved)

    @app.post("/api/settings/model/test")
    def test_settings():
        try:
            return app.state.model_adapter.test_connection(decrypted_settings())
        except ModelAdapterError as exc:
            raise HTTPException(502, detail={"code": "MODEL_CONNECTION_FAILED", "message": str(exc)})

    @app.get("/api/prompts")
    def prompts():
        return {"items": [{"analysis_type": key, **value} for key, value in PROMPTS.items()]}

    @app.post("/api/inferences")
    def infer(body: InferenceRequest):
        if body.chart_id:
            record = app.state.charts.get(body.chart_id)
            if not record:
                raise HTTPException(404, "Chart not found")
            chart_id = record["id"]
            chart = record["chart"]
            bazi = record["bazi"]
            day_master = record["day_master"]
        else:
            chart_id = None
            chart = body.temporary_chart.chart
            bazi = body.temporary_chart.bazi
            day_master = body.temporary_chart.day_master
        defaults = PROMPTS.get(body.analysis_type) or PROMPTS["自定义"]
        variables = {
            "analysis_type": body.analysis_type,
            "bazi": bazi,
            "day_master": day_master,
            "chart_json": json.dumps(chart, ensure_ascii=False),
            "custom_request": body.custom_request,
        }
        try:
            system_prompt = render_prompt(body.system_prompt or defaults["system"], variables)
            user_prompt = render_prompt(body.user_prompt or defaults["user"], variables)
            completion = app.state.model_adapter.complete(
                decrypted_settings(),
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
        except PromptRenderError as exc:
            raise HTTPException(400, detail={"code": "PROMPT_INVALID", "message": str(exc)})
        except ModelAdapterError as exc:
            raise HTTPException(502, detail={"code": "MODEL_REQUEST_FAILED", "message": str(exc)})
        return app.state.inferences.create(
            {
                "chart_id": chart_id,
                "analysis_type": body.analysis_type,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "response": completion["content"],
                "reasoning": completion.get("reasoning"),
                "token_usage": completion.get("token_usage", {}),
            }
        )

    @app.get("/api/inferences")
    def list_inferences(chart_id: int | None = None):
        return {"items": app.state.inferences.list(chart_id)}

    return app


app = create_app()
