from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .bazi import build_engine_arguments


METHOD_VERSION = "life-kline-v1"
MAX_DAYS = 1100

TEN_GOD_DELTAS = {
    "正财": 6,
    "偏财": 5,
    "正官": 5,
    "正印": 4,
    "食神": 4,
    "偏印": 2,
    "伤官": 1,
    "比肩": 0,
    "七杀": -3,
    "劫财": -3,
}

TEN_GOD_TAGS = {
    "正财": "财星触发",
    "偏财": "财星触发",
    "正官": "官星显现",
    "七杀": "压力增强",
    "正印": "印星支撑",
    "偏印": "印星支撑",
    "食神": "产出顺畅",
    "伤官": "表达增强",
    "比肩": "同辈竞争",
    "劫财": "资源分夺",
}

BRANCH_CLASHES = {
    "子": "午",
    "丑": "未",
    "寅": "申",
    "卯": "酉",
    "辰": "戌",
    "巳": "亥",
    "午": "子",
    "未": "丑",
    "申": "寅",
    "酉": "卯",
    "戌": "辰",
    "亥": "巳",
}

BRANCH_COMBOS = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}


def build_daily_engine_arguments(start: date, end: date, gender: str) -> list[dict[str, Any]]:
    if end < start:
        raise ValueError("end must be on or after start")
    days = (end - start).days + 1
    if days > MAX_DAYS:
        raise ValueError(f"Life kline range cannot exceed {MAX_DAYS} days")
    return [
        build_engine_arguments((start + timedelta(days=offset)).isoformat(), "12:00", gender)
        for offset in range(days)
    ]


def normalize_transit_day(raw: dict[str, Any], day: str) -> dict[str, Any]:
    year = _pillar(raw.get("年柱"))
    month = _pillar(raw.get("月柱"))
    daily = _pillar(raw.get("日柱"))
    return {
        "date": day,
        "ganzhi": {
            "year": f"{year['stem']}{year['branch']}",
            "month": f"{month['stem']}{month['branch']}",
            "day": f"{daily['stem']}{daily['branch']}",
        },
        "stems": {"year": year["stem"], "month": month["stem"], "day": daily["stem"]},
        "branches": {"year": year["branch"], "month": month["branch"], "day": daily["branch"]},
        "ten_gods": {
            "year_stem": year["ten_god"],
            "month_stem": month["ten_god"],
            "day_stem": daily["ten_god"],
            "day_branch": daily["branch_ten_gods"],
        },
    }


def select_dayun_for_date(dayun_list: list[dict[str, Any]], start_date: Any, target: date) -> dict[str, Any] | None:
    normalized = _annotate_dayun_dates([dict(item) for item in dayun_list], start_date)
    for item in normalized:
        start = _parse_date(item.get("start_date"))
        end = _parse_date(item.get("end_date"))
        if start and end and start <= target <= end:
            return item
    for item in normalized:
        start_year = item.get("start_year")
        end_year = item.get("end_year")
        if isinstance(start_year, int) and isinstance(end_year, int) and start_year <= target.year <= end_year:
            return item
    return None


def score_day(base_chart: dict[str, Any], transit_day: dict[str, Any], dayun: dict[str, Any] | None) -> dict[str, Any]:
    evidence: list[dict[str, Any]] = []
    tags: list[str] = []
    open_score = 50

    if dayun:
        open_score += _add_evidence(evidence, tags, "dayun_stem_ten_god", "当前大运天干十神", dayun.get("stem_ten_god"), 0.9)
        for ten_god in _as_list(dayun.get("branch_ten_gods")):
            open_score += _add_evidence(evidence, tags, "dayun_branch_ten_god", "当前大运地支十神", ten_god, 0.5)

    open_score += _add_evidence(evidence, tags, "year_stem_ten_god", "流年天干十神", transit_day["ten_gods"].get("year_stem"), 0.7)
    open_score += _add_evidence(evidence, tags, "month_stem_ten_god", "流月天干十神", transit_day["ten_gods"].get("month_stem"), 0.5)

    day_delta = _add_evidence(evidence, tags, "day_stem_ten_god", "流日天干十神", transit_day["ten_gods"].get("day_stem"), 1.0)
    for ten_god in transit_day["ten_gods"].get("day_branch") or []:
        day_delta += _add_evidence(evidence, tags, "day_branch_ten_god", "流日地支藏干十神", ten_god, 0.6)

    base_day_branch = _base_day_branch(base_chart)
    transit_branch = transit_day["branches"].get("day")
    opportunity = 3
    risk = 3
    if base_day_branch and transit_branch and BRANCH_CLASHES.get(base_day_branch) == transit_branch:
        risk += 8
        tags.append("日支受冲")
        evidence.append({"rule": "day_branch_clash", "label": f"流日{transit_branch}冲日支{base_day_branch}", "delta": -8, "polarity": "negative"})
    if base_day_branch and transit_branch and frozenset((base_day_branch, transit_branch)) in BRANCH_COMBOS:
        opportunity += 6
        tags.append("日支相合")
        evidence.append({"rule": "day_branch_combo", "label": f"流日{transit_branch}合日支{base_day_branch}", "delta": 6, "polarity": "positive"})

    open_score = clamp_score(open_score)
    close = clamp_score(open_score + day_delta)
    high = clamp_score(max(open_score, close) + opportunity)
    low = clamp_score(min(open_score, close) - risk)
    if close > open_score + 2:
        trend = "bullish"
    elif close < open_score - 2:
        trend = "bearish"
    else:
        trend = "neutral"
    level = "high" if close >= 70 else "low" if close <= 40 else "medium"
    unique_tags = list(dict.fromkeys(tags))[:4]
    return {
        "date": transit_day["date"],
        "ganzhi": transit_day["ganzhi"],
        "kline": {"open": open_score, "high": high, "low": low, "close": close},
        "trend": trend,
        "level": level,
        "tags": unique_tags,
        "explanation": build_daily_explanation(evidence),
        "evidence": evidence,
    }


def build_life_kline(
    chart: dict[str, Any],
    gender: str,
    bazi_adapter,
    start: date,
    end: date,
    dimension: str = "overall",
) -> dict[str, Any]:
    if dimension != "overall":
        raise ValueError("dimension must be overall")
    arguments = build_daily_engine_arguments(start, end, gender)
    raw_days = bazi_adapter.calculate_batch(arguments)
    dates = [(start + timedelta(days=offset)).isoformat() for offset in range(len(raw_days))]
    dayun = normalize_dayun(chart)
    series = []
    for raw, day_text in zip(raw_days, dates):
        transit_day = normalize_transit_day(raw, day_text)
        selected_dayun = select_dayun_for_date(dayun["list"], dayun.get("start_date"), date.fromisoformat(day_text))
        series.append(score_day(chart, transit_day, selected_dayun))
    return {
        "range": {"start": start.isoformat(), "end": end.isoformat(), "days": len(series)},
        "method": {"version": METHOD_VERSION, "score_range": [0, 100], "dimension": dimension},
        "series": series,
    }


def normalize_dayun(chart: dict[str, Any]) -> dict[str, Any]:
    source = chart.get("dayun") if isinstance(chart.get("dayun"), dict) else {}
    rows = source.get("大运") or source.get("list") or []
    result = []
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            result.append(
                {
                    "ganzhi": row.get("干支") or row.get("ganzhi"),
                    "start_year": row.get("开始年份") or row.get("start_year"),
                    "end_year": row.get("结束") or row.get("end_year"),
                    "start_age": row.get("开始年龄") or row.get("start_age"),
                    "end_age": row.get("结束年龄") or row.get("end_age"),
                    "stem_ten_god": row.get("天干十神") or row.get("stem_ten_god"),
                    "branch_ten_gods": row.get("地支十神") or row.get("branch_ten_gods") or [],
                }
            )
    return {"start_date": source.get("起运日期") or source.get("start_date"), "list": result}


def build_daily_explanation(evidence: list[dict[str, Any]]) -> str:
    positives = [item["label"] for item in evidence if item.get("polarity") == "positive"]
    negatives = [item["label"] for item in evidence if item.get("polarity") == "negative"]
    parts = []
    if positives:
        parts.append("机会信号：" + "、".join(positives[:2]))
    if negatives:
        parts.append("波动信号：" + "、".join(negatives[:2]))
    return "；".join(parts) if parts else "当天未出现显著触发，趋势以原局与岁运底盘为主。"


def clamp_score(value: float) -> int:
    return max(0, min(100, round(value)))


def _pillar(raw: Any) -> dict[str, Any]:
    raw = raw if isinstance(raw, dict) else {}
    stem = raw.get("天干") if isinstance(raw.get("天干"), dict) else {}
    branch = raw.get("地支") if isinstance(raw.get("地支"), dict) else {}
    hidden = branch.get("藏干") if isinstance(branch.get("藏干"), dict) else {}
    return {
        "stem": stem.get("天干", ""),
        "branch": branch.get("地支", ""),
        "ten_god": stem.get("十神", ""),
        "branch_ten_gods": [
            value.get("十神", "")
            for value in hidden.values()
            if isinstance(value, dict) and value.get("十神")
        ],
    }


def _add_evidence(evidence: list[dict[str, Any]], tags: list[str], rule: str, label_prefix: str, ten_god: Any, factor: float) -> int:
    if not ten_god:
        return 0
    delta = round(TEN_GOD_DELTAS.get(str(ten_god), 0) * factor)
    if delta:
        evidence.append(
            {
                "rule": rule,
                "label": f"{label_prefix}为{ten_god}",
                "delta": delta,
                "polarity": "positive" if delta > 0 else "negative",
            }
        )
    tag = TEN_GOD_TAGS.get(str(ten_god))
    if tag:
        tags.append(tag)
    return delta


def _base_day_branch(chart: dict[str, Any]) -> str:
    for pillar in chart.get("pillars") or []:
        if isinstance(pillar, dict) and pillar.get("label") == "日柱":
            branch = pillar.get("branch") if isinstance(pillar.get("branch"), dict) else {}
            return branch.get("char", "")
    raw = chart.get("raw") if isinstance(chart.get("raw"), dict) else {}
    day = raw.get("日柱") if isinstance(raw.get("日柱"), dict) else {}
    branch = day.get("地支") if isinstance(day.get("地支"), dict) else {}
    return branch.get("地支", "")


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value:
        return [value]
    return []


def _annotate_dayun_dates(dayun_list: list[dict[str, Any]], start_date: Any) -> list[dict[str, Any]]:
    anchor = _parse_date(start_date)
    if not anchor:
        return dayun_list
    starts: list[tuple[dict[str, Any], date]] = []
    for item in dayun_list:
        start_year = item.get("start_year")
        if not isinstance(start_year, int):
            continue
        exact_start = _safe_date(start_year, anchor.month, anchor.day)
        item["start_date"] = exact_start.isoformat()
        starts.append((item, exact_start))
    for index, (item, _) in enumerate(starts):
        next_start = starts[index + 1][1] if index + 1 < len(starts) else None
        if not next_start and isinstance(item.get("end_year"), int):
            next_start = _safe_date(item["end_year"] + 1, anchor.month, anchor.day)
        if next_start:
            item["end_date"] = (next_start - timedelta(days=1)).isoformat()
    return dayun_list


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    parts = str(value).replace("/", "-").split("-")
    if len(parts) < 3:
        return None
    try:
        return date(int(parts[0]), int(parts[1]), int(parts[2]))
    except ValueError:
        return None


def _safe_date(year: int, month: int, day: int) -> date:
    while day > 0:
        try:
            return date(year, month, day)
        except ValueError:
            day -= 1
    return date(year, month, 1)
