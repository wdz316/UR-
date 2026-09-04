"""由 demo/template.html 生成双版本单文件页面（数据内嵌，双击即开）.

- demo/index.html    日版：OSM 地图（日本用）
- demo/index_cn.html 国内版：高德地图（发家人）

用法: 先 python crawler/ur_tokyo.py 刷新数据，再 python crawler/build_demo.py
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ur_tokyo.json"
TEMPLATE = ROOT / "demo" / "template.html"

CN_TILE = """const map = L.map('map').setView([35.68,139.60], 10);
// 高德地图瓦片（国内外均可访问，中文标注，方便家人看）
L.tileLayer('https://webrd0{s}.is.autonavi.com/appmaptile?lang=zh_cn&size=1&scale=1&style=8&x={x}&y={y}&z={z}',{subdomains:['1','2','3','4'],attribution:'© 高德地图 AutoNavi'}).addTo(map);"""


def build(out_name, title_suffix, tile_block=None):
    units = json.loads(DATA.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    html = TEMPLATE.read_text(encoding="utf-8")
    data_block = ("/*DATA-BEGIN*/\nconst DATA = "
                  + json.dumps(units, ensure_ascii=False)
                  + f";\nconst BUILD_DATE = \"{today}\";\n/*DATA-END*/")
    html, n = re.subn(r"/\*DATA-BEGIN\*/.*?/\*DATA-END\*/", lambda _: data_block,
                      html, flags=re.S)
    assert n == 1, "DATA 标记块未找到"
    if tile_block:
        html, n = re.subn(r"/\*TILE-BEGIN\*/.*?/\*TILE-END\*/",
                          lambda _: "/*TILE-BEGIN*/\n" + tile_block + "\n/*TILE-END*/",
                          html, flags=re.S)
        assert n == 1, "TILE 标记块未找到"
    html = html.replace("__TITLE_SUFFIX__", title_suffix)
    assert "__TITLE_SUFFIX__" not in html
    out = ROOT / "demo" / out_name
    out.write_text(html, encoding="utf-8")
    print(f"{out_name}: {len(units)} units build={today} size={out.stat().st_size}B")


def main():
    build("index.html", "")            # 日版 OSM（模板默认）
    build("index_cn.html", "（国内版）", CN_TILE)


if __name__ == "__main__":
    main()
