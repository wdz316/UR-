"""UR 官网东京空室爬虫（打官方 JSON 接口，无需浏览器）.

接口（见官网 /chintai/common/js/api*.js, gmap.js）:
  POST chintai/api/bukken/search/list_init/   tdfk=13            -> 各エリア件数
  POST chintai/api/bukken/search/map_marker/  tdfk+bbox          -> 全部団地 id/lat/lng/roomCount（一次）
  POST chintai/api/bukken/search/list_bukken/ tdfk=13&area=XX    -> 団地明细（名称/行政区/租金区间/交通HTML）
  POST chintai/api/room/list/                 tdfk&mode&id       -> 各部屋（翻页 mode=add&last_id）
  GET  www.ur-net.go.jp/chintai/kanto/tokyo/<id>.html            -> 住所（正则提取，失败留空）

礼貌爬取: 间隔 DELAY 秒，失败重试 3 次，只读公开募集信息。
输出: data/ur_tokyo.json（与 demo 数据模型同构，另含 room/room_url）。
"""
import html
import json
import re
import time
import urllib.parse
import urllib.request
from datetime import date

API = "https://chintai.r6.ur-net.go.jp/chintai/api/"
SITE = "https://www.ur-net.go.jp"
TDFK = "13"  # 东京都
DELAY = 1.0
UA = {"User-Agent": "URZhaoFang/0.1 (personal research; contact: local)"}
BBOX = {"ne_lat": "35.95", "ne_lng": "139.95", "sw_lat": "35.5", "sw_lng": "139.0"}


def post(path, params, timeout=30):
    data = urllib.parse.urlencode(params).encode()
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(API + path, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - 重试所有网络/解析错误
            last = e
            time.sleep(2)
    raise RuntimeError(f"POST {path} {params} 失败: {last}")


def get_text(url, timeout=30):
    last = None
    for _ in range(3):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(2)
    raise RuntimeError(f"GET {url} 失败: {last}")


WARD_AREA = {  # 23区 -> エリア（demo 筛选项）
    "千代田区": "都心", "中央区": "都心", "港区": "都心", "新宿区": "都心",
    "文京区": "都心", "渋谷区": "都心",
    "北区": "城北", "荒川区": "城北", "板橋区": "城北", "練馬区": "城北", "足立区": "城北",
    "中野区": "城西", "杉並区": "城西", "豊島区": "城西",
    "品川区": "城南", "目黒区": "城南", "大田区": "城南", "世田谷区": "城南",
    "江東区": "城東", "墨田区": "城東", "江戸川区": "城東", "葛飾区": "城東", "台東区": "城東",
}


def ward_area(ward):
    if ward in WARD_AREA:
        return WARD_AREA[ward]
    if ward.endswith("市"):
        return "多摩"  # 東京市部（八王子・町田・立川…）
    return ""


def num(s):
    """'84,900円' -> 84900；解析失败返回 None（保持脏数据可见）"""
    if s is None:
        return None
    m = re.search(r"[\d,]+", str(s).replace("，", ","))
    return int(m.group(0).replace(",", "")) if m else None


def fnum(s):
    if s is None:
        return None
    m = re.search(r"\d+(?:\.\d+)?", html.unescape(str(s)))
    return float(m.group(0)) if m else None


def clean(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s or ""))).strip()


def parse_access(access_html):
    """交通HTML第一条 -> (line, station)。如 'JR京浜東北・根岸線「根岸」駅バス13分'"""
    text = clean(access_html)
    m = re.search(r"(.+?線)「(.+?)」駅", text)
    if m:
        return m.group(1).strip(), m.group(2).strip() + "駅"
    m = re.search(r"「(.+?)」駅", text)
    if m:
        return "", m.group(1).strip() + "駅"
    return "", ""


def parse_address(detail_html):
    """详情页 住所表 -> 地址文本，找不到返回 ''"""
    m = re.search(r"住所</th>\s*<td>(.*?)</td>", detail_html, re.S)
    if not m:
        return ""
    return clean(m.group(1))


def parse_floor(s):
    m = re.search(r"(\d+)\s*階", html.unescape(str(s or "")))
    return int(m.group(1)) if m else None


def parse_walk(access_html):
    """交通HTML -> 到最近车站步行分钟（取首个 徒歩N分；纯巴士/无数据返回 None）"""
    m = re.search(r"徒歩\s*(\d+)", clean(access_html))
    return int(m.group(1)) if m else None


def fetch_rooms(danchi_id):
    """取某团地全部房间（init 首批 + add 翻页直到空），返回 room/list/ 原始行列表"""
    rooms, last_id = [], None
    params = {"tdfk": TDFK, "mode": "init", "id": danchi_id}
    while True:
        batch = post("room/list/", params) or []
        time.sleep(DELAY)
        if not batch:
            break
        rooms.extend(batch)
        last_id = batch[-1]["id"]
        params = {"tdfk": TDFK, "mode": "add", "id": danchi_id,
                  "last_id": last_id}
    return rooms


def normalize_room(danchi, room, today):
    line, station = parse_access(danchi.get("access", ""))
    return {
        "danchi": html.unescape(danchi.get("name") or ""),
        "ward": html.unescape(danchi.get("skcs") or ""),
        "area_group": ward_area(html.unescape(danchi.get("skcs") or "")),
        "address": danchi.get("_address", ""),
        "rent": num(room.get("rent")),
        "kyoekihi": num(room.get("commonfee")),
        "madori": room.get("type"),
        "area": fnum(room.get("floorspace")),
        "floor": parse_floor(room.get("floor")),
        "walk": parse_walk(danchi.get("access", "")),
        "line": line,
        "station": station,
        "lat": danchi.get("_lat"),
        "lng": danchi.get("_lng"),
        "url": SITE + (room.get("urlDetail") or danchi.get("bukkenUrl") or ""),
        "room": html.unescape(room.get("name") or ""),
        "updated": today,
    }


def crawl():
    today = date.today().isoformat()
    markers = {m["id"]: m for m in
               post("bukken/search/map_marker/",
                    {"tdfk": TDFK, **BBOX, "small": "false"}) or []}
    time.sleep(DELAY)
    areas = post("bukken/search/list_init/", {"tdfk": TDFK})
    time.sleep(DELAY)
    units = []
    for a in areas:
        danchis = post("bukken/search/list_bukken/",
                       {"tdfk": TDFK, "area": a["Key"]}) or []
        time.sleep(DELAY)
        for d in danchis:
            if not (d.get("roomCount") or 0):
                continue
            mk = markers.get(d["id"], {})
            d["_lat"], d["_lng"] = mk.get("lat"), mk.get("lng")
            try:
                d["_address"] = parse_address(get_text(SITE + d["bukkenUrl"]))
            except RuntimeError:
                d["_address"] = ""
            time.sleep(DELAY)
            for r in fetch_rooms(d["id"]):
                units.append(normalize_room(d, r, today))
    return units


if __name__ == "__main__":
    out = crawl()
    with open("data/ur_tokyo.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"units={len(out)} -> data/ur_tokyo.json")
