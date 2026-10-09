#!/usr/bin/env python3
"""把韓文欄位的繁中翻譯同步到「Chinese (traditional)」語言欄位。

董事長 2026-10-10：遊戲加啟動參數 -enable_all_languages 後可以選 Chinese (traditional)，
中文模式沒有韓文模式的「위／일」格式問題，但官方中文是機翻、人名也被音譯。
這支工具在所有 merge 工具跑完後執行，讓中文欄位與韓文欄位內容一致：

- 同一檔內有中文欄位的：gui_translations／tutorial_data 的 <CN>、<CNGROUP> ← <KR>、<KRGROUP>；
  schools 的 *_CHINESE ← *_KOREAN；world_default 的 *_chinese="" ← *_korean=""；
  names 的 <CN> ← <EN>（人名保留英文）。
- 獨立的中文檔：直接用韓文版內容，BOM 與換行照中文原檔。

用法：python3 tools/build_chinese.py "<27 版 data 資料夾（取中文原檔的 BOM／換行格式）>"
"""

import os
import re
import sys

COPIES = [  # (中文檔, 來源韓文檔)
    ("text/chinese.xml", "text/korean.xml"),
    ("storylines/default/storylines_chinese.xml", "storylines/default/storylines_korean.xml"),
    ("misc/hints_chinese.txt", "misc/hints_korean.txt"),
    ("misc/historical_recaps_chinese.txt", "misc/historical_recaps_korean.txt"),
    ("database/injuries_chinese.txt", "database/injuries_korean.txt"),
    ("database/off_field_injuries_chinese.txt", "database/off_field_injuries_korean.txt"),
]


def rb(p):
    return open(p, "rb").read().decode("utf-8")


def wb(p, s):
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    open(p, "wb").write(s.encode("utf-8"))


def like(text, original):
    """換成中文原檔的 BOM 與換行。"""
    bom = original.startswith("﻿")
    crlf = "\r\n" in original
    t = text.lstrip("﻿").replace("\r\n", "\n")
    if crlf:
        t = t.replace("\n", "\r\n")
    return ("﻿" if bom else "") + t


def copy_tag(text, src, dst):
    """同一個區塊內 <dst> 的值改成 <src> 的值（區塊以 </src> 所在的元素為準）。"""
    def fix(m):
        block = m.group(0)
        v = re.search(rf"<{src}>(.*?)</{src}>", block, re.S)
        if v is None:
            return block
        return re.sub(rf"<{dst}>.*?</{dst}>", lambda _: f"<{dst}>{v.group(1)}</{dst}>", block, count=1, flags=re.S)
    return fix


def main(game):
    n = {}
    # gui：每個 HCS 的 CN ← KR
    p = "text/gui_translations.xml"
    s = rb(p)
    s2 = re.sub(r'<HCS i="\d+">.*?</HCS>', copy_tag(None, "KR", "CN"), s, flags=re.S)
    n[p] = s2 != s
    wb(p, s2)
    # tutorial：CN ← KR、CNGROUP ← KRGROUP
    p = "text/tutorial_data.xml"
    s = rb(p)
    s2 = re.sub(r"<TI [^>]*>.*?</TI>", copy_tag(None, "KR", "CN"), s, flags=re.S)
    s2 = re.sub(r"<TI [^>]*>.*?</TI>", copy_tag(None, "KRGROUP", "CNGROUP"), s2, flags=re.S)
    n[p] = s2 != s
    wb(p, s2)
    # names：CN ← EN（人名保留英文）
    p = "database/names.xml"
    s = rb(p)
    s2 = re.sub(r"<N nid=\"\d+\"[^>]*>.*?</N>", copy_tag(None, "EN", "CN"), s, flags=re.S)
    n[p] = s2 != s
    wb(p, s2)
    # schools：*_CHINESE ← *_KOREAN
    p = "database/schools.xml"
    s = rb(p)
    def sch(m):
        block = m.group(0)
        for tag, val in re.findall(r"<(\w+)_KOREAN>(.*?)</\1_KOREAN>", block, re.S):
            block = re.sub(rf"<{tag}_CHINESE>.*?</{tag}_CHINESE>", lambda _: f"<{tag}_CHINESE>{val}</{tag}_CHINESE>", block, flags=re.S)
        return block
    s2 = re.sub(r"<SCHOOL .*?</SCHOOL>", sch, s, flags=re.S)
    n[p] = s2 != s
    wb(p, s2)
    # world：x_chinese="" ← x_korean=""
    p = "database/world_default.xml"
    s = rb(p)
    def wd(m):
        tag = m.group(0)
        for a, val in re.findall(r'(\w+)_korean="([^"]*)"', tag):
            tag = re.sub(rf'{a}_chinese="[^"]*"', lambda _: f'{a}_chinese="{val}"', tag)
        return tag
    s2 = re.sub(r"<[A-Z_]+ [^>]*_korean=[^>]*>", wd, s)
    n[p] = s2 != s
    wb(p, s2)
    # 獨立中文檔
    pairs = COPIES + [(os.path.join("strategy_profiles", f.replace("_korean", "_chinese")), os.path.join("strategy_profiles", f))
                      for f in sorted(os.listdir("strategy_profiles")) if f.endswith("_korean.txt")]
    for dst, src in pairs:
        wb(dst, like(rb(src), rb(os.path.join(game, dst))))
        n[dst] = True
    for k, v in n.items():
        print(("已更新 " if v else "無變動 ") + k)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
