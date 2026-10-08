#!/usr/bin/env python3
"""收件匣劇情新聞（storylines_korean.xml）中文化。

27 版的劇情檔整份是韓文，遊戲附的 storylines_chinese.xml 是機翻且佔位符壞掉
（682 篇有 599 篇對不上英文），所以改由英文翻譯。每篇 ARTICLE 只換 <SUBJECT>
與 <TEXT>，其他結構逐字沿用 27 版原檔；還沒翻的退回英文，不留韓文。

鍵：<ARTICLE id> 加 S（標題）或 T（內文），例如 763S、763T。
譯文裡的 ⏎ 代表換行（原檔是 CRLF）。

用法:
    python3 tools/merge_storylines.py --todo > todo.tsv     # 匯出還沒翻的：鍵<TAB>英文
    python3 tools/merge_storylines.py batch.tsv [...]       # 套用（鍵<TAB>中文），逐筆檢查，有問題不寫檔
    python3 tools/merge_storylines.py --verify
基底放 temp/storylines_korean.xml 與 temp/storylines_english.xml（27 版原檔）。
"""

import html
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
from apply_zh import check  # noqa: E402  佔位符、引號、< > &、殘留英文

BASE_KR = "temp/storylines_korean.xml"
BASE_EN = "temp/storylines_english.xml"
OUT = "storylines/default/storylines_korean.xml"

ART_RE = re.compile(r'(<ARTICLE id="(\d+)"[^>]*>\s*<SUBJECT>)(.*?)(</SUBJECT>\s*<TEXT>)(.*?)(</TEXT>)', re.S)
HANGUL_RE = re.compile(r"[가-힣ᄀ-ᇿ㄰-㆏]")
CJK_RE = re.compile(r"[一-鿿]")
CHOICE_RE = re.compile(r"\[(?!%)[^\]]*\]")
INJ_RE = re.compile(r"<INJURY_DESCRIPTION>(.*?)</INJURY_DESCRIPTION>")


def read(p):
    with open(p, encoding="utf-8-sig", newline="") as f:
        return f.read()


def write(p, s):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8-sig", newline="") as f:  # 原檔有 BOM
        f.write(s)


def english():
    return {m.group(2): (m.group(3), m.group(5)) for m in ART_RE.finditer(read(BASE_EN))}


def flat(s):
    return html.unescape(s).replace("\r\n", "⏎").replace("\n", "⏎")


def todo():
    en = english()
    cur = read(OUT) if os.path.exists(OUT) else read(BASE_KR)
    for m in ART_RE.finditer(cur):
        i = m.group(2)
        for k, val, src in (("S", m.group(3), en[i][0]), ("T", m.group(5), en[i][1])):
            if not CJK_RE.search(val):
                print(f"{i}{k}\t{flat(src)}")


def load(paths):
    rows = {}
    for p in paths:
        for line in open(p, encoding="utf-8"):
            cols = line.rstrip("\n").split("\t")
            if len(cols) >= 2 and re.fullmatch(r"\d+[ST]", cols[0]):
                rows[cols[0]] = cols[-1].strip()
    return rows


def apply(paths):
    rows, en = load(paths), english()
    problems = []
    for key, zh in rows.items():
        i, k = key[:-1], key[-1]
        src = flat(en[i][0 if k == "S" else 1])
        problems += check(key, src, zh)
        if zh.count("⏎") != src.count("⏎"):
            problems.append(f"{key}: 換行數不符 {src.count('⏎')} -> {zh.count('⏎')}")
        # [a|b|c]（沒有 %）是隨機選項，要翻，但選項數不能變
        arity = lambda s: sorted(x.count("|") for x in CHOICE_RE.findall(s))
        if arity(zh) != arity(src):
            problems.append(f"{key}: 隨機選項數不符 {arity(src)} -> {arity(zh)}")
    if problems:
        print("\n".join(problems[:40]))
        sys.exit(f"共 {len(problems)} 個問題，沒有寫檔")

    cur = read(OUT) if os.path.exists(OUT) else read(BASE_KR)

    def sub(m):
        i = m.group(2)
        parts = []
        for k, val, src in (("S", m.group(3), en[i][0]), ("T", m.group(5), en[i][1])):
            if f"{i}{k}" in rows:
                val = rows[f"{i}{k}"].replace("⏎", "\r\n")
            elif not CJK_RE.search(val):
                val = src  # 還沒翻：退回英文，不留韓文
            parts.append(val)
        return m.group(1) + parts[0] + m.group(4) + parts[1] + m.group(6)

    out = ART_RE.sub(sub, cur)

    # 傷兵名單上的缺陣原因：照順序對英文檔，查 storyline_injuries.tsv，查不到用英文
    inj_tsv = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storyline_injuries.tsv")
    table = dict(l.rstrip("\n").split("\t", 1) for l in open(inj_tsv, encoding="utf-8") if "\t" in l)
    en_inj = iter(INJ_RE.findall(read(BASE_EN)))
    out = INJ_RE.sub(lambda m: f"<INJURY_DESCRIPTION>{table.get((e := next(en_inj)), e)}</INJURY_DESCRIPTION>", out)
    if "\r\n" not in read(BASE_KR):  # 27 版韓文檔是 LF，英文檔是 CRLF，照韓文檔
        out = out.replace("\r\n", "\n")
    write(OUT, out)
    print(f"套用 {len(rows)} 筆 -> {OUT}")
    return verify()


def verify():
    out, base, en = read(OUT), read(BASE_KR), english()
    ok = True
    try:
        ET.fromstring(out.encode("utf-8"))
        print("  XML 解析            : OK")
    except ET.ParseError as e:
        print(f"  XML 解析失敗        : {e}")
        ok = False
    shape = lambda s: INJ_RE.sub("", ART_RE.sub(lambda m: m.group(1) + m.group(4) + m.group(6), s))
    drift = shape(out) != shape(base)
    print(f"  標題內文以外偏離基底: {'有' if drift else '0'}")
    arts = list(ART_RE.finditer(out))
    han = len(HANGUL_RE.findall(out))  # 整份檔，含傷病描述
    bad_ph = [m.group(2) for m in arts
              if sorted(re.findall(r"\[%[^\]]*\]", html.unescape(m.group(3) + m.group(5))))
              != sorted(re.findall(r"\[%[^\]]*\]", html.unescape("".join(en[m.group(2)]))))]
    zh = sum(bool(CJK_RE.search(m.group(5))) for m in arts)
    print(f"  殘留韓文字數        : {han}")
    print(f"  佔位符與英文對不上  : {len(bad_ph)}", bad_ph[:5] if bad_ph else "")
    print(f"  中文化進度          : {zh} / {len(arts)}")
    ok = ok and not drift and not han and not bad_ph
    print("  結果                : " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    a = sys.argv[1:]
    if a == ["--todo"]:
        todo()
    elif a == ["--verify"]:
        sys.exit(verify())
    elif a:
        sys.exit(apply(a))
    else:
        sys.exit(__doc__)
