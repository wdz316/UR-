"""demo 过滤逻辑测试（与 demo/template.html::filterUnits 保持一致）"""
import json
import re
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data" / "tokyo_sample.json"
REQUIRED = {"danchi", "ward", "address", "rent", "kyoekihi", "madori",
            "area", "floor", "line", "station", "lat", "lng", "url", "updated"}


def load():
    return json.loads(DATA.read_text(encoding="utf-8"))


def fav_id(u):
    return u["danchi"] + "|" + (u.get("room") or "")


def split_kw(kw):
    """空格/逗号/顿号（含全角）分隔多个关键字，与 demo 的 splitKw 一致"""
    return [k for k in re.split(r"[\s\u3000,，、]+", str(kw or "")) if k]


def filter_units(units, max_rent=10**9, min_area=0, madori=(), line="",
                 max_walk=None, kw="", ku_only=False, fav_only=False, favs=()):
    out = []
    kws = split_kw(kw)
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
        # 多个关键字：命中任意一个即保留；检索范围含棟号 room，与页面一致
        hay = (u["danchi"] + u["ward"] + u["address"] + u["line"]
               + u["station"] + (u.get("room") or ""))
        if kws and not any(k in hay for k in kws):
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


KW_UNITS = [
    {"danchi": "晴海アイランド", "ward": "中央区", "address": "中央区晴海1-8-5",
     "line": "都営大江戸線", "station": "勝どき駅", "room": "5号棟503号室",
     "rent": 133700, "area": 36.0, "madori": "1K"},
    {"danchi": "森下ハイツ", "ward": "江東区", "address": "江東区森下2-1",
     "line": "都営新宿線", "station": "森下駅", "room": "2号棟101号室",
     "rent": 90000, "area": 40.0, "madori": "2DK"},
    {"danchi": "鶴川", "ward": "町田市", "address": "町田市鶴川",
     "line": "小田急線", "station": "鶴川駅", "room": "1号棟201号室",
     "rent": 70000, "area": 45.0, "madori": "3DK"},
]


def _names(r):
    return [u["danchi"] for u in r]


def test_split_kw():
    assert split_kw("森下 晴海") == ["森下", "晴海"]
    assert split_kw("森下\u3000晴海") == ["森下", "晴海"]  # 全角空格
    assert split_kw("森下,晴海、鶴川，町田") == ["森下", "晴海", "鶴川", "町田"]
    assert split_kw("  ") == [] and split_kw("") == [] and split_kw(None) == []


def test_kw_multi_any_match():
    # 用户场景：同时找森下和晴海，命中任一即显示
    assert _names(filter_units(KW_UNITS, kw="森下 晴海")) == ["晴海アイランド", "森下ハイツ"]
    assert _names(filter_units(KW_UNITS, kw="森下")) == ["森下ハイツ"]
    assert _names(filter_units(KW_UNITS, kw="森下和晴海")) == []  # 不拆“和”，整体不匹配


def test_kw_blank_not_filter():
    assert len(filter_units(KW_UNITS, kw="   ")) == 3  # 纯空白不应把结果清空


def test_kw_searches_room_number_and_station():
    assert _names(filter_units(KW_UNITS, kw="503号室")) == ["晴海アイランド"]  # 棟号可搜
    assert _names(filter_units(KW_UNITS, kw="勝どき")) == ["晴海アイランド"]  # 站名可搜


def test_kw_combined_with_other_filters():
    # 关键字命中 + 家賃上限同时生效：森下 90000 在 8 万上限下被筛掉
    r = filter_units(KW_UNITS, kw="森下 晴海", max_rent=100000)
    assert _names(r) == ["森下ハイツ"]
