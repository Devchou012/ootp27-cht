# 移植到 OOTP 27

本 repo fork 自 [bojinhong/ootp23-cht](https://github.com/bojinhong/ootp23-cht)。
目標是用同一套合併工具，以 OOTP 27（2026-03-13 發售）的原始檔為基底重做繁體中文化。

## 為什麼可以沿用

- 中文化借用的是遊戲的「韓文」語言欄位，OOTP 27 仍然支援英文與韓文。
- `tools/merge_*.py` 都以「官方原始檔為基底」：舊翻譯照編號（HCS `i`、CAT／OBJ `id`）搬過去，
  新版新增的條目用 `<CN>` 轉繁補上，補不了的退回英文。

## 先檢查（約 15 分鐘）

```
python tools/check_ootp27.py "<OOTP 27 安裝資料夾>"
```

它只讀不寫，會回報：

1. 本專案要覆蓋的檔案在 27 版裡的位置（同路徑／換位置／找不到）
2. 27 版 `gui_translations.xml` 有幾成 `<CN>` 有中文。不到一半的話，新條目要人工翻
3. HCS 與 OBJ 編號的沿用比例、英文被改的筆數。超過一成被改，代表編號可能重排過
4. database 與 fonts 的位置

最後一段「結論」沒有列出問題，再往下做。

## 重做步驟

1. 備份 27 版安裝資料夾裡會被覆蓋的檔案（上面第 1 點列出的那些）。
2. 把 27 版的**未改動原始檔**複製到 `temp/`，檔名照各工具的預設值：

   | 工具 | 放進 temp/ 的 27 版原檔 |
   |---|---|
   | `merge_gui.py` | `gui_translations.xml` |
   | `merge_korean.py` | `english.xml`（播報文字基底） |
   | `merge_tutorial.py` | `tutorial_data.xml` |
   | `merge_world.py` | `world_default.xml` |
   | `merge_schools.py` | `schools.xml` |
   | `localize_names.py` | `names.xml` |

3. 依序重跑，每支跑完都跑 `--verify`：
   ```
   pip install opencc-python-reimplemented
   python tools/merge_gui.py && python tools/merge_gui.py --verify
   python tools/merge_korean.py && python tools/merge_korean.py --verify
   python tools/merge_tutorial.py
   python tools/merge_world.py
   python tools/merge_schools.py
   python tools/localize_names.py
   ```
4. `python tools/merge_korean.py --todo` 列出 27 版新增、還沒翻的播報文字，用 `apply_zh.py` 批次補。
5. 把產出的檔案依第 1 點的位置放回 27 版資料夾，字型照 `fonts/font20/` 對應到 27 版的字型資料夾。
6. 遊戲設定把語言改成韓文，重開遊戲。

## 注意

- `database/` 的檔案不要直接覆蓋到 27 版。那是 23 版資料做的，一定要以 27 版原檔為基底，用第 3 步重產。
- Steam 更新遊戲或「驗證遊戲檔案」都會把檔案還原，每次更新後要重做第 2–5 步。
- 上游沒有附授權條款。這個 fork 只供個人使用，不要另外散布翻譯檔。

## 術語表

27 版補翻用的台灣棒球術語在 `docs/glossary.md`（來源與裁定理由在案件 #2026-10-08-02）。裝進遊戲前跑 `python tools/preflight.py "<27 版 data 資料夾>"`，要「全部通過」。

## 已知限制（2026-10-09）

韓文模式下，名次後面的「위」與日期裡的「일」是遊戲程式依語言自動加上的，不在任何文字檔裡，改不到。
27 版雖然附了整套繁中檔（chinese.xml 等），程式也有 Chinese (traditional) 選項，但正式版選單只開放英文與韓文；
啟動參數 `-enable_all_languages` 與 app.cfg 加 `enable_all_languages` 都試過，無效。
