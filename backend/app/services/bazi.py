from typing import Any


PILLAR_KEYS = ("年柱", "月柱", "日柱", "时柱")


def build_engine_arguments(birth_date: str, birth_time: str, gender: str) -> dict[str, Any]:
    return {
        "solarDatetime": f"{birth_date}T{birth_time}:00+08:00",
        "gender": 1 if gender == "male" else 0,
        "eightCharProviderSect": 1,
    }


def _stem(data: Any) -> dict[str, Any]:
    data = data if isinstance(data, dict) else {}
    return {
        "char": data.get("天干", ""),
        "element": data.get("五行", ""),
        "yin_yang": data.get("阴阳", ""),
        "ten_god": data.get("十神", ""),
    }


def _branch(data: Any) -> dict[str, Any]:
    data = data if isinstance(data, dict) else {}
    hidden = data.get("藏干") if isinstance(data.get("藏干"), dict) else {}
    return {
        "char": data.get("地支", ""),
        "element": data.get("五行", ""),
        "yin_yang": data.get("阴阳", ""),
        "hidden_stems": [
            {
                "role": role,
                "char": value.get("天干", ""),
                "ten_god": value.get("十神", ""),
            }
            for role, value in hidden.items()
            if isinstance(value, dict)
        ],
    }


def normalize_chart(raw: dict[str, Any]) -> dict[str, Any]:
    pillars = []
    for label in PILLAR_KEYS:
        source = raw.get(label) if isinstance(raw.get(label), dict) else {}
        pillars.append(
            {
                "label": label,
                "stem": _stem(source.get("天干")),
                "branch": _branch(source.get("地支")),
                "nayin": source.get("纳音", ""),
                "xun": source.get("旬", ""),
                "kongwang": source.get("空亡", ""),
                "xingyun": source.get("星运", ""),
                "zizuo": source.get("自坐", ""),
            }
        )
    return {
        "solar": raw.get("阳历", ""),
        "lunar": raw.get("农历", ""),
        "bazi": raw.get("八字", ""),
        "zodiac": raw.get("生肖", ""),
        "day_master": raw.get("日主", ""),
        "pillars": pillars,
        "fetal_origin": raw.get("胎元", ""),
        "fetal_breath": raw.get("胎息", ""),
        "life_palace": raw.get("命宫", ""),
        "body_palace": raw.get("身宫", ""),
        "shensha": raw.get("神煞", {}),
        "dayun": raw.get("大运", {}),
        "relations": raw.get("刑冲合会", {}),
        "raw": raw,
    }

