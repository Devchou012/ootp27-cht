#!/usr/bin/env python3
"""唯讀檢核 OOTP 繁中翻譯一致性、術語與禁用詞。"""

from __future__ import annotations

import html
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from merge_gui import TEAM_SECTIONS, parse, placeholders_match  # noqa: F401

CHECK_SECTIONS = {"HARD_CODED_STRINGS", "LEAGUE_NAMES"}
BANNED_WORDS = (
    "賽季", "總管", "反饋", "屏幕", "設置", "保存", "視頻", "質量",
    "信息", "默認", "菜單", "網絡", "文件夾", "用戶", "激活", "登錄",
)


def clean(value: str) -> str:
    """將 parse() 回傳的 XML 原始值轉為可比較文字。"""
    return html.unescape(value or "").strip()


def norm_en(value: str) -> str:
    return clean(value).casefold()


def tsv(value: object) -> str:
    """避免內容中的換行或 Tab 破壞 TSV 格式。"""
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")


def entries_from_data(data: dict) -> list[tuple[int, str, str, str]]:
    """將 parse() 結果整理為 (編號, section, EN, KR)。"""
    result = []
    for index, (section, tags) in data.items():
        en = clean(tags.get("EN", ""))
        kr = clean(tags.get("KR", ""))
        result.append((index, section, en, kr))
    return result


def find_inconsistencies(
    entries: list[tuple[int, str, str, str]],
) -> list[tuple[str, int, str, str]]:
    groups: dict[str, list[tuple[int, str, str]]] = defaultdict(list)

    for index, section, en, kr in entries:
        if section not in CHECK_SECTIONS or not en or kr == en:
            continue
        groups[norm_en(en)].append((index, en, kr))

    findings = []
    for values in groups.values():
        translations = Counter(kr for _, _, kr in values)
        if len(translations) < 2:
            continue

        english = values[0][1]
        translation_text = "｜".join(
            f"{translation}×{count}"
            for translation, count in sorted(translations.items())
        )
        indexes = ",".join(str(index) for index, _, _ in values)
        findings.append((english, len(values), translation_text, indexes))

    return sorted(findings, key=lambda row: (norm_en(row[0]), row[3]))


def main_translation(value: str) -> str:
    """移除中文說明括號，只保留術語指定的主要譯法。"""
    return re.split(r"[（(]", clean(value), maxsplit=1)[0].strip()


def load_glossary(path: Path, ui_format: bool = False) -> list[tuple[str, str]]:
    if not path.is_file():
        return []

    terms = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if ui_format:
            if "\t" not in line:
                continue
            english_part, chinese_part = line.split("\t", 1)
        else:
            if not line.startswith("-") or "→" not in line:
                continue
            english_part, chinese_part = line[1:].split("→", 1)

        chinese = main_translation(chinese_part)
        if not chinese:
            continue

        for english in ([english_part] if ui_format else english_part.split("/")):  # K/9 不能拆
            english = clean(english)
            # 括號標情境的是同形異義（GB 勝差／滾地球），機器分不出來，留給人工
            if english and "(" not in english and "（" not in english:
                terms.append((english, chinese))

    return terms


def is_short_term(english: str) -> bool:
    """最多六個英文單字，避免把完整句子當成術語掃描。"""
    return len(re.findall(r"[A-Za-z0-9]+", english)) <= 6


_ALLOW_TSV = Path(__file__).with_name("qa_allow.tsv")  # 編號<TAB>術語，人工審過不用改的
ALLOW = ({tuple(l.rstrip("\n").split("\t")[:2]) for l in _ALLOW_TSV.open(encoding="utf-8")
          if "\t" in l and not l.startswith("#")} if _ALLOW_TSV.exists() else set())


def find_term_issues(
    entries: list[tuple[int, str, str, str]],
    terms: list[tuple[str, str]],
) -> list[tuple[int, str, str, str, str]]:
    findings = []
    seen = set()

    for term, required in terms:
        if not is_short_term(term):
            continue
        # 全大寫縮寫（ERA、PCT）大小寫要相符，免得撞到 Era、Pct
        flags = 0 if term.isupper() else re.IGNORECASE
        pattern = re.compile(r"\b" + re.escape(term) + r"\b", flags)

        for index, _section, en, kr in entries:
            if not en or not is_short_term(en) or not pattern.search(en) or required in kr:
                continue
            if kr.strip() == en.strip():  # 縮寫欄位保留英文視為合格（10-09 裁定）
                continue
            if (str(index), term) in ALLOW:  # 人工審過、情境不同的
                continue

            row = (index, term, required, en, kr)
            if row not in seen:
                seen.add(row)
                findings.append(row)

    return sorted(findings, key=lambda row: (row[0], row[1].casefold()))


def find_banned_words(
    entries: list[tuple[int, str, str, str]],
) -> list[tuple[int, str, str]]:
    findings = []

    for index, _section, _en, kr in entries:
        for word in BANNED_WORDS:
            if word not in kr:
                continue
            if word == "總管" and "總管理" in kr:
                continue
            if word == "賽季" and "賽季" not in kr.replace("休賽季", ""):  # 休賽季是台灣用法
                continue
            findings.append((index, word, kr))

    return sorted(findings, key=lambda row: (row[0], row[1]))


def write_tsv(path: Path, rows: list[tuple]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write("\t".join(tsv(value) for value in row) + "\n")


def run(root: Path, output_dir: Path) -> tuple[int, int, int]:
    data = parse(str(root / "text" / "gui_translations.xml"))
    entries = entries_from_data(data)

    # 介面只用介面術語表；docs/glossary.md 是播報用語（left、hit…），套到介面會大量誤報
    terms = load_glossary(root / "docs" / "glossary_ui.md", ui_format=True)

    inconsistencies = find_inconsistencies(entries)
    term_issues = find_term_issues(entries, terms)
    banned_issues = find_banned_words(entries)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_tsv(
        output_dir / "qa_inconsistent.tsv",
        [("英文", "出現次數", "各譯法與次數", "編號清單"), *inconsistencies],
    )
    write_tsv(
        output_dir / "qa_terms.tsv",
        [("編號", "術語", "應含", "英文", "目前中文"), *term_issues],
    )
    write_tsv(
        output_dir / "qa_banned.tsv",
        [("編號", "禁用詞", "目前中文"), *banned_issues],
    )

    print(f"一致性：{len(inconsistencies)} 筆")
    print(f"術語：{len(term_issues)} 筆")
    print(f"禁用詞：{len(banned_issues)} 筆")
    return len(inconsistencies), len(term_issues), len(banned_issues)


def selftest() -> None:
    sample = [
        (1, "HARD_CODED_STRINGS", "Win Percentage", "勝率"),
        (2, "LEAGUE_NAMES", " win percentage ", "比率"),
        (3, "OTHER", "Win Percentage", "其他"),
        (4, "HARD_CODED_STRINGS", "General Manager", "總管理員"),
        (5, "HARD_CODED_STRINGS", "Save Game", "保存遊戲"),
        (6, "HARD_CODED_STRINGS", "Batting Average", "打擊率"),
    ]

    inconsistent = find_inconsistencies(sample)
    assert len(inconsistent) == 1
    assert inconsistent[0][0] == "Win Percentage"
    assert inconsistent[0][1] == 2

    term_issues = find_term_issues(
        sample,
        [("Batting Average", "打擊平均"), ("Very Long Example Term Here Test", "略")],
    )
    assert term_issues == [(6, "Batting Average", "打擊平均", "Batting Average", "打擊率")]

    banned = find_banned_words(sample)
    assert banned == [(5, "保存", "保存遊戲")]
    print("selftest: OK")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    else:
        repo_root = Path(__file__).resolve().parents[1]
        destination = (
            Path(sys.argv[1]).resolve()
            if len(sys.argv) > 1
            else repo_root / "temp" / "qa"
        )
        run(repo_root, destination)
