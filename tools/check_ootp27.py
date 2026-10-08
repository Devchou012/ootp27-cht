#!/usr/bin/env python3
"""檢查 OOTP 27 的原始檔能不能直接套用本專案的合併工具（只讀，不寫任何檔）。

會看四件事（對應 PORTING-27.md）：
  1. 檔名與路徑：本專案要覆蓋的檔案，在 27 版安裝資料夾裡找不找得到、路徑一不一樣
  2. <CN> 欄位：27 版 gui_translations.xml 還有沒有簡體中文可以拿來補新條目
  3. 編號對應：HCS i 與 OBJ id 跟本專案的對不對得上、英文原文有沒有被改掉
  4. database／fonts：只回報 27 版的檔案位置，不比內容（這些要用 merge_* 重產）

用法：
    python3 tools/check_ootp27.py "D:/SteamLibrary/steamapps/common/Out of the Park Baseball 27"
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from merge_gui import HCS_RE, CJK_RE as GUI_CJK_RE, HANGUL_RE  # noqa: E402
from merge_korean import CAT_SPLIT_RE, CAT_ID_RE, OBJ_ID_RE, COMMENT_RE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGETS = [
    "text/gui_translations.xml", "text/korean.xml", "text/tutorial_data.xml",
    "database/names.xml", "database/schools.xml", "database/world_default.xml",
    "database/injuries_korean.txt", "database/off_field_injuries_korean.txt",
    "misc/hints_korean.txt", "misc/historical_recaps_korean.txt", "fonts/font20/regular.ttf",
]
TAG_RE = {t: re.compile(rf"<{t}>(.*?)</{t}>", re.S) for t in ("EN", "KR", "CN")}


def read(p):
    with open(p, encoding="utf-8", errors="replace") as f:
        return f.read()


def find(game, rel):
    """先找同路徑；找不到就在整個安裝資料夾裡找同檔名。"""
    direct = os.path.join(game, rel)
    if os.path.isfile(direct):
        return direct, True
    name = os.path.basename(rel)
    for d, _, files in os.walk(game):
        if name in files:
            return os.path.join(d, name), False
    return None, False


def hcs(text):
    out = {}
    for m in HCS_RE.finditer(text):
        body = m.group("body")
        out[m.group("i")] = {t: (r.search(body).group(1) if r.search(body) else "") for t, r in TAG_RE.items()}
    return out


def objs(text):
    ids = set()
    for chunk in CAT_SPLIT_RE.split(text):
        cat = CAT_ID_RE.search(chunk)
        if cat:
            # 註解掉的 OBJ 也算：本專案把多餘講法註解起來保留
            ids.update((cat.group(1), o) for o in OBJ_ID_RE.findall(chunk))
    return ids


def pct(a, b):
    return f"{a}/{b}（{a * 100 // b if b else 0}%）"


def main():
    if len(sys.argv) != 2 or not os.path.isdir(sys.argv[1]):
        sys.exit(__doc__)
    game = sys.argv[1]
    verdict = []

    print("== 1. 檔名與路徑 ==")
    found = {}
    for rel in TARGETS:
        p, same = find(game, rel)
        found[rel] = p
        print(f"  {'同路徑' if same else '換位置' if p else '找不到'}  {rel}" + (f"  -> {os.path.relpath(p, game)}" if p and not same else ""))
    if not found["text/gui_translations.xml"] or not found["text/korean.xml"]:
        verdict.append("主要文字檔找不到：檔案結構改了，工具要先改路徑或格式")

    gui = found["text/gui_translations.xml"]
    if gui:
        print("\n== 2. <CN> 欄位（自動補新條目靠它）==")
        new, old = hcs(read(gui)), hcs(read(os.path.join(ROOT, "text/gui_translations.xml")))
        has_cn = sum(1 for v in new.values() if GUI_CJK_RE.search(v["CN"]))
        korean = sum(1 for v in new.values() if HANGUL_RE.search(v["KR"]))
        print(f"  HCS 共 {len(new)} 筆；<CN> 有中文 {pct(has_cn, len(new))}；<KR> 是韓文 {korean} 筆")
        if has_cn * 2 < len(new):
            verdict.append("<CN> 不到一半有中文：新條目沒辦法自動補，要人工翻")

        print("\n== 3. 編號對應（gui_translations.xml）==")
        same = [i for i in new if i in old]
        changed = [i for i in same if new[i]["EN"] != old[i]["EN"]]
        added = [i for i in new if i not in old]
        print(f"  沿用編號 {pct(len(same), len(new))}，其中英文被改 {len(changed)} 筆")
        print(f"  27 版新增 {len(added)} 筆，舊版有但 27 版沒有 {len(set(old) - set(new))} 筆")
        for i in changed[:5]:
            print(f"    i={i}  舊：{old[i]['EN'][:50]!r}  新：{new[i]['EN'][:50]!r}")
        if same and len(changed) * 10 > len(same):
            verdict.append("超過一成編號的英文被改：編號可能重排過，照編號搬會對錯位置")

    kor = found["text/korean.xml"]
    if kor:
        print("\n== 3. 編號對應（korean.xml，CAT＋OBJ）==")
        new_o = objs(COMMENT_RE.sub(lambda m: m.group(0)[4:-3], read(kor)))
        old_o = objs(COMMENT_RE.sub(lambda m: m.group(0)[4:-3], read(os.path.join(ROOT, "text/korean.xml"))))
        print(f"  27 版 OBJ {len(new_o)} 筆，本專案有對應的 {pct(len(new_o & old_o), len(new_o))}，新增 {len(new_o - old_o)} 筆")

    print("\n== 4. database／fonts ==")
    print("  上面列出的位置就是 27 版原檔；不要直接用本專案的檔案覆蓋，用 merge_world.py／merge_schools.py 以 27 版為基底重產")

    print("\n== 結論 ==")
    print("  " + ("\n  ".join(verdict) if verdict else "沒看到擋路的問題：照 PORTING-27.md 的步驟重跑合併工具"))


if __name__ == "__main__":
    main()
