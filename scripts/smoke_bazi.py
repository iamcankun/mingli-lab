import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.adapters.node_bazi import NodeBaziAdapter
from app.services.bazi import normalize_chart


def main() -> None:
    raw = NodeBaziAdapter().calculate(
        {
            "solarDatetime": "1990-05-15T14:30:00+08:00",
            "gender": 1,
            "eightCharProviderSect": 1,
        }
    )
    chart = normalize_chart(raw)
    pillars = chart["pillars"]
    assert chart["bazi"] == "庚午 辛巳 庚辰 癸未"
    assert len(pillars) == 4
    assert all(item["stem"]["char"] and item["branch"]["char"] for item in pillars)
    print(f"OK {chart['bazi']} 日主={chart['day_master']}")


if __name__ == "__main__":
    main()

