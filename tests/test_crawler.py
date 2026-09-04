"""爬虫解析函数离线测试（不碰网络，fixture 取自真实接口结构）"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "crawler"))
from ur_tokyo import (clean, fnum, normalize_room, num, parse_access,
                      parse_address, parse_floor, ward_area)

DANCHI = {"id": "20_2600", "name": "テスト団地", "skcs": "板橋区",
          "access": "<li>都営三田線「高島平」駅徒歩5分</li>",
          "bukkenUrl": "/chintai/kanto/tokyo/20_2600.html",
          "_address": "板橋区高島平1-1", "_lat": 35.79, "_lng": 139.66}
ROOM = {"id": "001080409", "name": "1-8棟409号室", "type": "3DK",
        "rent": "60,900円", "commonfee": "(共益費4,500円）",
        "floorspace": "53㎡", "floor": "4階",
        "urlDetail": "/chintai/kanto/tokyo/20_2600_room.html?JKSS=001080409"}


def test_num():
    assert num("84,900円") == 84900
    assert num("(共益費4,500円）") == 4500
    assert num(None) is None
    assert num("相談") is None


def test_fnum_floor():
    assert fnum("53㎡") == 53.0
    assert parse_floor("4階") == 4
    assert parse_floor("") is None


def test_parse_access():
    line, st = parse_access(DANCHI["access"])
    assert line == "都営三田線" and st == "高島平駅"


def test_parse_access_multi_route_takes_first():
    line, st = parse_access(
        "<li>都営新宿線「大島」駅徒歩10分 JR総武線「亀戸」駅バス7分</li>")
    assert line == "都営新宿線" and st == "大島駅"


def test_ward_area():
    assert ward_area("板橋区") == "城北"
    assert ward_area("町田市") == "多摩"
    assert ward_area("八王子市") == "多摩"
    assert ward_area("港区") == "都心"


def test_parse_address():
    html = "<tr><th scope=\"row\">住所</th><td><p>板橋区高島平1-1</p></td></tr>"
    assert parse_address(html) == "板橋区高島平1-1"
    assert parse_address("<p>無関係</p>") == ""


def test_normalize_room():
    u = normalize_room(DANCHI, ROOM, "2026-09-04")
    assert u["rent"] == 60900 and u["kyoekihi"] == 4500
    assert u["madori"] == "3DK" and u["area"] == 53.0 and u["floor"] == 4
    assert u["ward"] == "板橋区" and u["area_group"] == "城北"
    assert u["line"] == "都営三田線" and u["station"] == "高島平駅"
    assert (u["lat"], u["lng"]) == (35.79, 139.66)
    assert u["url"].endswith("JKSS=001080409") and u["room"] == "1-8棟409号室"


def test_clean_strips_tags():
    assert clean("<li>JR山手線「池袋」駅</li>") == "JR山手線「池袋」駅"
