"""把 data/ur_tokyo.json 内嵌进 demo/index.html，双击即开无需起服务.

用法: python crawler/build_demo.py
流程: 先跑 python crawler/ur_tokyo.py 刷新数据，再跑本脚本重新内嵌。
"""
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "ur_tokyo.json"
PAGE = ROOT / "demo" / "index.html"


def main():
    units = json.loads(DATA.read_text(encoding="utf-8"))
    today = date.today().isoformat()
    block = ("/*DATA-BEGIN*/\nconst DATA = "
             + json.dumps(units, ensure_ascii=False)
             + f";\nconst BUILD_DATE = \"{today}\";\n/*DATA-END*/")
    html = PAGE.read_text(encoding="utf-8")
    new, n = re.subn(r"/\*DATA-BEGIN\*/.*?/\*DATA-END\*/", lambda _: block,
                     html, flags=re.S)
    assert n == 1, "DATA 标记块未找到"
    PAGE.write_text(new, encoding="utf-8")
    print(f"embedded {len(units)} units build={today} size={PAGE.stat().st_size}B")


if __name__ == "__main__":
    main()
