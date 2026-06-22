from fastapi.testclient import TestClient

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
    def calculate(self, arguments):
        assert arguments["eightCharProviderSect"] == 1
        return RAW_CHART


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


def test_chart_calculate_search_detail_and_delete(data_dir):
    client = make_client(data_dir)
    created = client.post(
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
    assert created.status_code == 200
    payload = created.json()
    assert payload["record"]["bazi"] == "庚午 辛巳 庚辰 癸未"
    chart_id = payload["record"]["id"]
    assert client.get("/api/charts", params={"query": "林"}).json()["items"][0]["id"] == chart_id
    assert client.get(f"/api/charts/{chart_id}").json()["chart"]["day_master"] == "庚"
    assert client.delete(f"/api/charts/{chart_id}").status_code == 204


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
