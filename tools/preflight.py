#!/usr/bin/env python3
"""裝進遊戲前的最後檢查（只讀）：成品檔會不會讓遊戲讀不到或顯示壞掉。

對每個要覆蓋的檔案，跟 27 版原檔比：
  1. XML 能不能解析、編碼 UTF-8、BOM 與換行（CRLF/LF）跟原檔一致
  2. 有沒有裸 & 或雙重跳脫（&amp;#39;）
  3. txt 行數與換行跟原檔一致
  4. 字型能不能開、有沒有繁中字（需要 fontTools，沒有就跳過）

用法:
    python3 tools/preflight.py "K:/SteamLibrary/steamapps/common/Out of the Park Baseball 27/data" [成品 data 資料夾]
成品資料夾預設是 repo 本身（text/、database/、misc/、fonts/font20/）。
"""

import os
import re
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = [
    "text/gui_translations.xml", "text/korean.xml", "text/tutorial_data.xml",
    "database/names.xml", "database/schools.xml", "database/world_default.xml",
    "database/injuries_korean.txt", "database/off_field_injuries_korean.txt",
    "misc/hints_korean.txt", "misc/historical_recaps_korean.txt",
]
BARE_AMP = re.compile(rb"&(?!#\d+;|#x[0-9a-fA-F]+;|[A-Za-z]+;)")
DOUBLE = re.compile(rb"[^\s\"<>]*&amp;(?:#\d+|[A-Za-z]+);[^\s\"<>]*")


def shape(b):
    return {"bom": b.startswith(b"\xef\xbb\xbf"), "crlf": b"\r\n" in b}


def main(argv):
    game = argv[0]
    built = argv[1] if len(argv) > 1 else ROOT
    bad = []
    for rel in FILES:
        g, o = os.path.join(game, rel), os.path.join(built, rel)
        gb, ob = open(g, "rb").read(), open(o, "rb").read()
        try:
            ob.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            bad.append(f"{rel}: 不是 UTF-8 ({e})")
            continue
        if shape(gb) != shape(ob):
            bad.append(f"{rel}: BOM/換行跟原檔不同 原={shape(gb)} 成品={shape(ob)}")
        if rel.endswith(".xml"):
            try:
                ET.fromstring(ob)
            except ET.ParseError as e:
                bad.append(f"{rel}: XML 解析失敗 {e}")
            # 原檔本來就有的不算我們的（例：官方英文地名 Pab&amp;#283;nice）
            n_new, n_old = len(BARE_AMP.findall(ob)), len(BARE_AMP.findall(gb))
            if n_new > n_old:
                bad.append(f"{rel}: 裸 & 比原檔多 {n_new - n_old} 處")
            extra = set(DOUBLE.findall(ob)) - set(DOUBLE.findall(gb))
            if extra:
                bad.append(f"{rel}: 雙重跳脫 {len(extra)} 種原檔沒有的寫法，例 "
                           + b" ".join(sorted(extra)[:3]).decode("utf-8", "replace"))
        elif gb.count(b"\n") != ob.count(b"\n"):
            n_g, n_o = gb.count(b"\n"), ob.count(b"\n")
            bad.append(f"{rel}: 行數 原={n_g} 成品={n_o}")
        print(f"  檢查完 {rel}")

    fonts = os.path.join(built, "fonts", "font20")
    try:
        from fontTools.ttLib import TTFont
        for name in sorted(os.listdir(fonts)):
            cmap = TTFont(os.path.join(fonts, name), lazy=True, fontNumber=0).getBestCmap()
            miss = [c for c in "中華職棒全壘打三振" if ord(c) not in cmap]
            if miss:
                bad.append(f"fonts/font20/{name}: 缺字 {miss}")
        print("  檢查完 字型")
    except ImportError:
        print("  略過字型檢查（pip install fonttools）")

    print("\n".join(bad) if bad else "全部通過")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
