"""demo 数据与过滤逻辑测试（与 demo/index.html::filterUnits 保持一致）"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "tokyo_sample.json"
REQUIRED = {"danchi", "ward", "address", "rent", "kyoekihi", "madori", "area",
            "floor", "lat", "lng", "url", "updated"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def filter_units(units, max_rent=10**9, min_area=0, madori="", kw=""):
    out = []
    for u in units:
        if u["rent"] > max_rent:
            continue
        if u["area"] < min_area:
            continue
        if madori and u["madori"] != madori:
            continue
        if kw and kw not in (u["danchi"] + u["ward"] + u["address"]):
            continue
        out.append(u)
    return out


def test_schema_complete():
    units = load()
    assert len(units) >= 5, "样本至少5条才有筛选意义"
    for u in units:
        assert REQUIRED <= set(u), f"缺字段: {REQUIRED - set(u)}"
        assert u["rent"] > 0 and u["area"] > 0
        assert 35.0 < u["lat"] < 36.0 and 139.0 < u["lng"] < 140.0  # 东京都大致范围


def test_filter_by_rent():
    units = load()
    cheap = filter_units(units, max_rent=80000)
    assert all(u["rent"] <= 80000 for u in cheap)
    assert len(cheap) >= 1


def test_filter_by_madori_and_kw():
    units = load()
    r = filter_units(units, madori="2DK")
    assert all(u["madori"] == "2DK" for u in r)
    r2 = filter_units(units, kw="練馬")
    assert all("練馬" in (u["danchi"] + u["ward"] + u["address"]) for u in r2)
