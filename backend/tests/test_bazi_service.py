from app.services.bazi import build_engine_arguments, normalize_chart


def test_build_engine_arguments_uses_solar_time_and_fixed_sect():
    arguments = build_engine_arguments(
        birth_date="1990-05-15",
        birth_time="14:30",
        gender="female",
    )
    assert arguments == {
        "solarDatetime": "1990-05-15T14:30:00+08:00",
        "gender": 0,
        "eightCharProviderSect": 1,
    }


def test_normalize_chart_exposes_stable_four_pillars():
    chart = normalize_chart(
        {
            "八字": "甲戌 丁丑 乙卯 甲申",
            "日主": "乙",
            "生肖": "狗",
            "年柱": {"天干": {"天干": "甲"}, "地支": {"地支": "戌"}},
            "月柱": {"天干": {"天干": "丁"}, "地支": {"地支": "丑"}},
            "日柱": {"天干": {"天干": "乙"}, "地支": {"地支": "卯"}},
            "时柱": {"天干": {"天干": "甲"}, "地支": {"地支": "申"}},
        }
    )
    assert chart["bazi"] == "甲戌 丁丑 乙卯 甲申"
    assert chart["day_master"] == "乙"
    assert [pillar["label"] for pillar in chart["pillars"]] == ["年柱", "月柱", "日柱", "时柱"]
    assert chart["pillars"][0]["stem"]["char"] == "甲"

