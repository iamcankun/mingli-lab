from datetime import date

import pytest

from app.adapters.node_bazi import BaziEngineError
from app.services.life_kline import (
    build_daily_engine_arguments,
    build_life_kline,
    normalize_transit_day,
    score_day,
    select_dayun_for_date,
)


BASE_CHART = {
    "bazi": "庚午 辛巳 庚辰 癸未",
    "day_master": "庚",
    "pillars": [
        {"label": "年柱", "stem": {"char": "庚"}, "branch": {"char": "午"}},
        {"label": "月柱", "stem": {"char": "辛"}, "branch": {"char": "巳"}},
        {"label": "日柱", "stem": {"char": "庚"}, "branch": {"char": "辰"}},
        {"label": "时柱", "stem": {"char": "癸"}, "branch": {"char": "未"}},
    ],
    "dayun": {
        "起运日期": "1997-8-5",
        "大运": [
            {"干支": "甲申", "开始年份": 2017, "结束": 2026, "天干十神": "偏财", "地支十神": ["比肩", "食神"]},
            {"干支": "乙酉", "开始年份": 2027, "结束": 2036, "天干十神": "正财", "地支十神": ["劫财"]},
        ],
    },
}


def transit(day_stem="乙", day_branch="亥", day_ten_god="正财", branch_ten_god="食神"):
    return {
        "年柱": {"天干": {"天干": "丙", "十神": "七杀"}, "地支": {"地支": "午", "藏干": {}}},
        "月柱": {"天干": {"天干": "甲", "十神": "偏财"}, "地支": {"地支": "午", "藏干": {}}},
        "日柱": {
            "天干": {"天干": day_stem, "十神": day_ten_god},
            "地支": {"地支": day_branch, "藏干": {"主气": {"天干": "壬", "十神": branch_ten_god}}},
        },
    }


class FakeBatchAdapter:
    def __init__(self, charts):
        self.charts = charts
        self.arguments = None

    def calculate_batch(self, arguments):
        self.arguments = arguments
        return self.charts


class FailingBatchAdapter:
    def calculate_batch(self, arguments):
        raise BaziEngineError("batch failed")


def test_build_daily_engine_arguments_uses_noon_and_inclusive_range():
    result = build_daily_engine_arguments(date(2026, 6, 30), date(2026, 7, 1), "male")

    assert result == [
        {"solarDatetime": "2026-06-30T12:00:00+08:00", "gender": 1, "eightCharProviderSect": 1},
        {"solarDatetime": "2026-07-01T12:00:00+08:00", "gender": 1, "eightCharProviderSect": 1},
    ]


def test_select_dayun_for_date_uses_exact_transition_boundary():
    dayun = [
        {"ganzhi": "癸亥", "start_year": 2016, "end_year": 2025},
        {"ganzhi": "甲子", "start_year": 2026, "end_year": 2035},
    ]

    before = select_dayun_for_date(dayun, "2006-5-28", date(2026, 5, 27))
    after = select_dayun_for_date(dayun, "2006-5-28", date(2026, 5, 28))

    assert before["ganzhi"] == "癸亥"
    assert before["end_date"] == "2026-05-27"
    assert after["ganzhi"] == "甲子"
    assert after["start_date"] == "2026-05-28"


def test_normalize_transit_day_extracts_daily_ganzhi_and_ten_gods():
    result = normalize_transit_day(transit(), "2026-06-30")

    assert result["date"] == "2026-06-30"
    assert result["ganzhi"] == {"year": "丙午", "month": "甲午", "day": "乙亥"}
    assert result["ten_gods"]["day_stem"] == "正财"
    assert result["ten_gods"]["day_branch"] == ["食神"]


def test_score_day_returns_clamped_kline_with_evidence():
    day = normalize_transit_day(transit(), "2026-06-30")
    result = score_day(BASE_CHART, day, {"ganzhi": "甲申", "stem_ten_god": "偏财", "branch_ten_gods": ["比肩"]})

    assert 0 <= result["kline"]["low"] <= result["kline"]["high"] <= 100
    assert result["kline"]["open"] != result["kline"]["close"]
    assert result["trend"] in {"bullish", "bearish", "neutral"}
    assert any(item["rule"] == "day_stem_ten_god" for item in result["evidence"])
    assert result["tags"]
    assert result["explanation"]


def test_score_day_preserves_negative_ten_god_evidence():
    day = normalize_transit_day(transit(day_stem="丙", day_branch="戌", day_ten_god="七杀", branch_ten_god="劫财"), "2026-07-01")
    result = score_day(BASE_CHART, day, None)

    assert any(item["rule"] == "day_stem_ten_god" and item["delta"] < 0 for item in result["evidence"])
    assert any(item["rule"] == "day_branch_clash" and item["delta"] < 0 for item in result["evidence"])


def test_build_life_kline_batches_transits_and_returns_series():
    adapter = FakeBatchAdapter([transit(), transit(day_stem="丙", day_branch="子", day_ten_god="七杀", branch_ten_god="伤官")])

    result = build_life_kline(BASE_CHART, "male", adapter, date(2026, 6, 30), date(2026, 7, 1))

    assert result["range"]["days"] == 2
    assert result["method"]["version"] == "life-kline-v1"
    assert [item["date"] for item in result["series"]] == ["2026-06-30", "2026-07-01"]
    assert adapter.arguments[0]["solarDatetime"] == "2026-06-30T12:00:00+08:00"


def test_build_life_kline_rejects_large_ranges():
    with pytest.raises(ValueError, match="1100"):
        build_life_kline(BASE_CHART, "male", FakeBatchAdapter([]), date(2026, 1, 1), date(2029, 1, 6))


def test_build_life_kline_rejects_unsupported_dimension():
    with pytest.raises(ValueError, match="dimension"):
        build_life_kline(BASE_CHART, "male", FakeBatchAdapter([]), date(2026, 1, 1), date(2026, 1, 1), "wealth")
