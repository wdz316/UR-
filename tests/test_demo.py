"""demo 过滤逻辑测试（与 demo/index.html::filterUnits 保持一致）"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "tokyo_sample.json"
REQUIRED = {"danchi", "ward", "address", "rent", "kyoekihi", "madori",
            "area", "floor", "line", "station", "lat", "lng", "url", "updated"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def fav_id(u):
    return u["danchi"] + "|" + (u.get("room") or "")


def filter_units(units, max_rent=10**9, min_area=0, madori=(), line="",
                 max_walk=None, kw="", ku_only=False, fav_only=False, favs=()):
    out = []
    for u in units:
        # rent 为 None（官网未公示）时不参与家賃过滤：常显，由前端高亮
        if u.get("rent") is not None and u["rent"] > max_rent:
            continue
        if u["area"] < min_area:
            continue
        if madori and u["madori"] not in madori:
            continue
        if line and u["line"] != line:
            continue
        if max_walk is not None and not (
                u.get("walk") is not None and u["walk"] <= max_walk):
            continue
        if kw and kw not in (u["danchi"] + u["ward"] + u["address"]
                             + u["line"] + u["station"]):
            continue
        if ku_only and not str(u.get("ward") or "").endswith("区"):
            continue
        if fav_only and fav_id(u) not in favs:
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


def test_filter_by_madori_multi_and_kw():
    units = load()
    r = filter_units(units, madori=["2DK", "2LDK"])
    assert all(u["madori"] in ("2DK", "2LDK") for u in r)
    assert len(r) >= 3
    r2 = filter_units(units, kw="練馬")
    assert all("練馬" in (u["danchi"] + u["ward"] + u["address"]) for u in r2)


def test_filter_by_line():
    units = load()
    r = filter_units(units, line="JR埼京線")
    assert len(r) >= 1
    assert all(u["line"] == "JR埼京線" for u in r)


def test_null_rent_always_shown():
    units = [{"danchi": "X", "ward": "立川市", "address": "立川市幸町1-1",
              "line": "JR中央線", "station": "立川駅", "room": "101",
              "rent": None, "area": 50.0, "madori": "3DK"}]
    assert filter_units(units, max_rent=1) == units  # 再低的上限也不隐藏
    assert filter_units(units, max_rent=10**9) == units
    assert filter_units(units, kw="立川") == units  # 关键字仍可筛掉
    assert filter_units(units, kw="新宿") == []


def test_filter_by_walk():
    units = [
        {"danchi": "A", "ward": "北区", "address": "a", "line": "L",
         "station": "S", "rent": 80000, "area": 40.0, "madori": "2DK",
         "walk": 4},
        {"danchi": "B", "ward": "北区", "address": "b", "line": "L",
         "station": "S", "rent": 80000, "area": 40.0, "madori": "2DK",
         "walk": 12},
        {"danchi": "C", "ward": "北区", "address": "c", "line": "L",
         "station": "S", "rent": 80000, "area": 40.0, "madori": "2DK",
         "walk": None},
    ]
    assert [u["danchi"] for u in filter_units(units, max_walk=5)] == ["A"]
    assert len(filter_units(units)) == 3  # 不限时全留


def test_fav_only():
    units = load()
    ids = [fav_id(units[0])]
    r = filter_units(units, fav_only=True, favs=ids)
    assert [fav_id(u) for u in r] == ids


def test_ku_only():
    units = [
        {"danchi": "A", "ward": "北区", "address": "a", "line": "L",
         "station": "S", "rent": 80000, "area": 40.0, "madori": "2DK"},
        {"danchi": "B", "ward": "町田市", "address": "b", "line": "L",
         "station": "S", "rent": 80000, "area": 40.0, "madori": "2DK"},
    ]
    assert [u["danchi"] for u in filter_units(units, ku_only=True)] == ["A"]
    assert len(filter_units(units)) == 2  # 默认不过滤
