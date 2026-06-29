from fastapi.testclient import TestClient

from app.adapters.node_bazi import BaziEngineError
from app.main import create_app


RAW_CHART = {
    "阳历": "1990-05-15 14:30:00",
    "农历": "农历庚午年四月廿一未时",
    "八字": "庚午 辛巳 庚辰 癸未",
    "生肖": "马",
    "日主": "庚",
    "年柱": {"天干": {"天干": "庚"}, "地支": {"地支": "午"}},
    "月柱": {"天干": {"天干": "辛"}, "地支": {"地支": "巳"}},
    "日柱": {"天干": {"天干": "庚"}, "地支": {"地支": "辰"}},
    "时柱": {"天干": {"天干": "癸"}, "地支": {"地支": "未"}},
    "大运": {"起运年龄": 3, "起运日期": "1993-08-01", "大运": []},
}


class FakeBaziAdapter:
    fail_batch = False

    def calculate(self, arguments):
        assert arguments["eightCharProviderSect"] == 1
        return RAW_CHART

    def calculate_batch(self, arguments):
        if self.fail_batch:
            raise BaziEngineError("batch failed")
        return [
            {
                "年柱": {"天干": {"天干": "丙", "十神": "七杀"}, "地支": {"地支": "午", "藏干": {}}},
                "月柱": {"天干": {"天干": "甲", "十神": "偏财"}, "地支": {"地支": "午", "藏干": {}}},
                "日柱": {
                    "天干": {"天干": "乙", "十神": "正财"},
                    "地支": {"地支": "亥", "藏干": {"主气": {"天干": "壬", "十神": "食神"}}},
                },
            }
            for _ in arguments
        ]


class FailingBatchBaziAdapter(FakeBaziAdapter):
    fail_batch = True


class FakeModelAdapter:
    def complete(self, settings, messages):
        return {
            "content": "# 事业结构判断\n\n适合在专业体系中持续积累。",
            "reasoning": None,
            "token_usage": {"prompt_tokens": 12, "completion_tokens": 18, "total_tokens": 30},
        }

    def test_connection(self, settings):
        return {"ok": True, "message": "连接成功"}


def make_client(data_dir):
    return TestClient(
        create_app(
            data_dir=data_dir,
            bazi_adapter=FakeBaziAdapter(),
            model_adapter=FakeModelAdapter(),
        )
    )


def create_chart(client):
    response = client.post(
        "/api/charts/calculate",
        json={
            "name": "林默",
            "gender": "male",
            "birth_date": "1990-05-15",
            "birth_time": "14:30",
            "province": "浙江",
            "city": "杭州",
            "persist": True,
        },
    )
    assert response.status_code == 200
    return response.json()["record"]


def test_chart_calculate_search_detail_and_delete(data_dir):
    client = make_client(data_dir)
    record = create_chart(client)
    assert record["bazi"] == "庚午 辛巳 庚辰 癸未"
    chart_id = record["id"]
    assert client.get("/api/charts", params={"query": "林"}).json()["items"][0]["id"] == chart_id
    assert client.get(f"/api/charts/{chart_id}").json()["chart"]["day_master"] == "庚"
    assert client.delete(f"/api/charts/{chart_id}").status_code == 204


def test_life_kline_endpoint_returns_daily_series(data_dir):
    client = make_client(data_dir)
    record = create_chart(client)

    response = client.get(
        f"/api/charts/{record['id']}/life-kline",
        params={"start": "2026-06-30", "end": "2026-07-01", "dimension": "overall"},
    )

    assert response.status_code == 200
    result = response.json()
    assert result["range"]["days"] == 2
    assert result["method"]["version"] == "life-kline-v1"
    assert result["series"][0]["date"] == "2026-06-30"
    assert result["series"][0]["ganzhi"]["day"] == "乙亥"
    assert set(result["series"][0]["kline"]) == {"open", "high", "low", "close"}
    assert result["series"][0]["evidence"]


def test_life_kline_endpoint_validates_range_and_dimension(data_dir):
    client = make_client(data_dir)
    record = create_chart(client)

    reversed_range = client.get(
        f"/api/charts/{record['id']}/life-kline",
        params={"start": "2026-07-01", "end": "2026-06-30"},
    )
    unsupported_dimension = client.get(
        f"/api/charts/{record['id']}/life-kline",
        params={"start": "2026-06-30", "end": "2026-07-01", "dimension": "wealth"},
    )

    assert reversed_range.status_code == 400
    assert unsupported_dimension.status_code == 400


def test_life_kline_endpoint_returns_404_for_missing_chart(data_dir):
    client = make_client(data_dir)

    response = client.get("/api/charts/999/life-kline", params={"start": "2026-06-30", "end": "2026-07-01"})

    assert response.status_code == 404


def test_life_kline_endpoint_maps_engine_errors(data_dir):
    client = TestClient(
        create_app(data_dir=data_dir, bazi_adapter=FailingBatchBaziAdapter(), model_adapter=FakeModelAdapter())
    )
    record = create_chart(client)

    response = client.get(
        f"/api/charts/{record['id']}/life-kline",
        params={"start": "2026-06-30", "end": "2026-07-01"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "BAZI_ENGINE_UNAVAILABLE"


def test_model_settings_mask_key_and_test_connection(data_dir):
    client = make_client(data_dir)
    saved = client.put(
        "/api/settings/model",
        json={
            "base_url": "https://api.example.com/v1",
            "api_key": "secret-value",
            "model_id": "test-model",
            "temperature": 0.2,
            "max_tokens": 1200,
            "top_p": 1.0,
        },
    )
    assert saved.status_code == 200
    assert saved.json()["api_key_configured"] is True
    assert "secret-value" not in saved.text
    assert client.post("/api/settings/model/test").json()["ok"] is True


def test_inference_returns_prompts_and_token_diagnostics(data_dir):
    client = make_client(data_dir)
    client.put(
        "/api/settings/model",
        json={
            "base_url": "https://api.example.com/v1",
            "api_key": "secret-value",
            "model_id": "test-model",
            "temperature": 0.2,
            "max_tokens": 1200,
            "top_p": 1.0,
        },
    )
    response = client.post(
        "/api/inferences",
        json={
            "temporary_chart": {"bazi": "甲戌 丁丑 乙卯 甲申", "day_master": "乙"},
            "analysis_type": "事业分析",
            "custom_request": "关注职业转型",
        },
    )
    assert response.status_code == 200
    result = response.json()
    assert "事业结构判断" in result["response"]
    assert "甲戌 丁丑 乙卯 甲申" in result["user_prompt"]
    assert result["token_usage"]["total_tokens"] == 30
    assert client.get("/api/inferences").json()["items"][0]["analysis_type"] == "事业分析"
