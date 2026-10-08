#!/usr/bin/env python3
"""27 版其他還是韓文的檔：教練／總管背景、球隊暱稱表、授權條款。

- strategy_profiles/*_korean.txt：跟英文版逐行對齊。鍵 P<檔案序>L<行號>，
  檔案序照 temp/strategy_profiles/ 裡 *_english.txt 的排序。有譯文用譯文，
  沒有就用英文那一行，不留韓文。
- database/team_nick_names.xml：<ST_KR> 先查 merge_gui.TEAM_NICK，再查鍵 N<英文暱稱>，
  都沒有退回英文。
- license_korean.txt：法律文字不機翻，直接用官方英文 license.txt。

用法:
    python3 tools/merge_extras.py "<27 版 data 資料夾>" batch.tsv [...]
輸出到 repo 的 strategy_profiles/、database/team_nick_names.xml、license_korean.txt。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from merge_gui import TEAM_NICK  # noqa: E402

HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")
EN_DIR = "temp/strategy_profiles"


def load(paths):
    rows = {}
    for p in paths:
        for line in open(p, encoding="utf-8"):
            cols = line.rstrip("\n").split("\t")
            if len(cols) >= 2 and re.fullmatch(r"P\d+L\d+|N.+", cols[0]):
                rows[cols[0]] = cols[-1].strip()
    return rows


def main(argv):
    game, rows = argv[0], load(argv[1:])
    bad = []

    files = sorted(f for f in os.listdir(EN_DIR) if f.endswith("_english.txt"))
    os.makedirs("strategy_profiles", exist_ok=True)
    for fi, f in enumerate(files):
        en = open(os.path.join(EN_DIR, f), encoding="utf-8-sig", newline="").read().split("\r\n")
        out = []
        for ln, line in enumerate(en):
            zh = rows.get(f"P{fi}L{ln}", line)
            # 表格行的數字（例 10/5/3/15/5）不能被翻掉
            if re.search(r"\d+/\d+", line) and re.findall(r"\d+", zh) != re.findall(r"\d+", line):
                bad.append(f"{f}:{ln + 1} 數字不符 {line[:40]!r} -> {zh[:40]!r}")
            out.append(zh)
        kr = f.replace("_english", "_korean")
        with open(os.path.join("strategy_profiles", kr), "w", encoding="utf-8", newline="") as fh:
            fh.write("\r\n".join(out))

    src = os.path.join(game, "database", "team_nick_names.xml")
    nick = open(src, encoding="utf-8", newline="").read()

    def sub(m):
        so = m.group(1)
        zh = TEAM_NICK.get(so) or rows.get(f"N{so}") or so
        return f"<TNN><SO>{so}</SO><ST_KR>{zh}</ST_KR></TNN>"

    nick = re.sub(r"<TNN><SO>(.*?)</SO><ST_KR>.*?</ST_KR></TNN>", sub, nick)
    with open("database/team_nick_names.xml", "w", encoding="utf-8", newline="") as fh:
        fh.write(nick)

    lic = open(os.path.join(game, "license.txt"), encoding="utf-8-sig", newline="").read()
    with open("license_korean.txt", "w", encoding="utf-8-sig", newline="") as fh:
        fh.write(lic)

    for p in ["database/team_nick_names.xml", "license_korean.txt"] + [
            os.path.join("strategy_profiles", f.replace("_english", "_korean")) for f in files]:
        if HANGUL_RE.search(open(p, encoding="utf-8-sig").read()):
            bad.append(f"{p}: 還有韓文")
        if re.search(r'[<>&"]', "".join(v for k, v in rows.items() if k.startswith("N"))):
            bad.append("暱稱譯文含 < > & \"")
            break
    print("\n".join(bad[:20]) if bad else f"套用 {len(rows)} 筆，PASS")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
