from app.database import Database
from app.repositories import ChartRepository, InferenceRepository


def test_chart_repository_crud_and_search(data_dir):
    database = Database(data_dir / "test.sqlite3")
    repo = ChartRepository(database)
    first = repo.create(
        {
            "name": "林默",
            "gender": "male",
            "birth_date": "1990-01-01",
            "birth_time": "08:30",
            "birth_place": "浙江 杭州",
            "bazi": "甲子 乙丑 丙寅 丁卯",
            "day_master": "丙",
            "chart": {"bazi": "甲子 乙丑 丙寅 丁卯"},
        }
    )
    repo.create(
        {
            "name": "周宁",
            "gender": "female",
            "birth_date": "1991-02-02",
            "birth_time": "09:40",
            "birth_place": "江苏 南京",
            "bazi": "戊辰 己巳 庚午 辛未",
            "day_master": "庚",
            "chart": {},
        }
    )
    assert [item["id"] for item in repo.list("林")] == [first["id"]]
    assert repo.get(first["id"])["chart"]["bazi"] == "甲子 乙丑 丙寅 丁卯"
    assert repo.delete(first["id"]) is True
    assert repo.get(first["id"]) is None


def test_inference_repository_records_diagnostics(data_dir):
    database = Database(data_dir / "test.sqlite3")
    repo = InferenceRepository(database)
    item = repo.create(
        {
            "chart_id": None,
            "analysis_type": "事业分析",
            "system_prompt": "system",
            "user_prompt": "user",
            "response": "result",
            "reasoning": None,
            "token_usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )
    assert repo.list()[0]["id"] == item["id"]
    assert item["token_usage"]["total_tokens"] == 30

