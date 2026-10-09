# ootp27-cht
Out of the Park Baseball 27 繁體中文化（台灣用語）

fork 自 [bojinhong/ootp23-cht](https://github.com/bojinhong/ootp23-cht)，以 OOTP 27（27.5.81）原檔為基底重做。翻譯同時放在兩個語言欄位，內容相同：

| 遊戲語言 | 怎麼開 | 說明 |
|---|---|---|
| **Chinese (traditional)**（建議） | Steam 遊戲「內容」→「啟動選項」填 `-enable_all_languages`，遊戲設定語言選 Chinese (traditional) | 日期、名次是中文格式 |
| 韓文（Korean） | 遊戲設定直接選韓文 | 名次後面會出現「위」、日期出現「일」（程式內建，改不到） |

不改執行檔，只換 `data/` 底下的文字與字型。中文模式另外換了字型（官方中文字型缺 554 個字）。

## 翻譯原則

| 項目 | 怎麼處理 |
|---|---|
| 人名（球員、教練、總經理、老闆、職員、名人） | 保留英文原文 |
| 隊名、聯盟名 | 翻成中文 |
| 數據欄位 | 保留英文縮寫：AVG、OBP、SLG、OPS、ERA、WHIP、WAR、HR、RBI、SO、BB、SB… |
| 棒球術語 | 依中華民國棒球協會《棒球規則》（113 年版）、國家教育研究院樂詞網、中華職棒用法，例：犧牲飛球、壘指導員、盜壘、救援成功 |
| 用語 | 台灣用語，不用中國大陸用語（螢幕、設定、球季、總經理、聯盟主席…） |

術語表：[docs/glossary_ui.md](docs/glossary_ui.md)（介面與數據）、[docs/glossary.md](docs/glossary.md)（播報）。

## 翻譯範圍

| 內容 | 檔案 | 狀態 |
|---|---|---|
| 介面（按鈕、欄位、說明、對話視窗） | `text/gui_translations.xml` | 完成，Claude 逐行審稿 |
| 比賽播報、新聞稿、球探評語 | `text/korean.xml` | 4,729／4,729，Claude 逐行審稿 |
| 教學 | `text/tutorial_data.xml` | 完成，Claude 逐行審稿 |
| 收件匣新聞與劇情 | `storylines/default/storylines_korean.xml` | 671／682（其餘 11 篇英文原檔是空白） |
| 載入提示、名人語錄、歷史回顧 | `misc/hints_korean.txt`、`misc/historical_recaps_korean.txt` | 完成 |
| 教練與總經理背景 | `strategy_profiles/*_korean.txt` | 完成 |
| 球隊暱稱、國家城市、學校、傷病 | `database/` | 完成 |
| 授權條款 | `license_korean.txt` | 用官方英文版（法律文字不機翻） |

**已知限制**：韓文模式下，名次後面的「위」與日期裡的「일」是程式內建，改不到；用 Chinese (traditional) 模式就沒有這個問題。

**既有存檔**：遊戲切換語言時會把聯盟檔裡的人名轉成該語言，舊存檔可能還留著官方中文版音譯的人名。新開聯盟就會是英文人名。

## 安裝

### 方法一：用打包好的備份（本機）
`~/ootp27-中文化備份/data` 是照遊戲資料夾結構放好的成品，附 `SHA256SUMS.txt`。

```powershell
# 遊戲先關掉
Copy-Item -Recurse -Force "$env:USERPROFILE\ootp27-中文化備份\data\*" "K:\SteamLibrary\steamapps\common\Out of the Park Baseball 27\data\"
```

### 方法二：從 repo
1. 關掉遊戲，先備份遊戲 `data/` 裡會被覆蓋的檔案。
2. 把本 repo 的下列資料夾與檔案，照同樣路徑複製到遊戲的 `data/`：`text/`、`database/`、`misc/`、`storylines/`、`strategy_profiles/`、`license_korean.txt`。
3. 字型：`fonts/font20/*.ttf` 複製到遊戲的 `data/fonts/font20/` 與 `data/fonts/font30/`（中文模式用），另外把 `bold.ttf` 複製一份命名為 `bb_bold.ttf`。
4. 裝前檢查（只讀）：
   ```
   python tools/preflight.py "<原始 data 資料夾備份>" "<要裝的 data>"
   ```
   要出現「全部通過」。

### 切換語言
1. Steam 遊戲庫 → OOTP 27 右鍵 →「內容」→「一般」→「啟動選項」填 `-enable_all_languages`。
2. 遊戲設定 → 語言選「Chinese (traditional)」→ 依提示關閉遊戲 → 重新開啟。

（不加啟動選項時只能選韓文，翻譯內容一樣。）

## 測試清單

開遊戲後依序看這幾個地方，看到怪的就截圖：

1. **主畫面與選單**：按鈕、分頁名稱是否通順，有沒有殘留英文或韓文。
2. **球隊數據與排名頁**：數據欄位要是英文縮寫（AVG、ERA、WAR…）；名次後面的「위」是已知限制。
3. **比賽中逐球播報**：主客、好壞球、出局數有沒有翻反，人名要是英文。
4. **賽後戰報與新聞**：句子是否自然，術語是否正確（犧牲飛球、壘指導員、救援成功）。
5. **收件匣**：劇情新聞、信件、傷兵通知（傷病描述要是中文）。
6. **教學**：從新手教學開始走一遍，畫面說明要對得上目前這一步。
7. **載入畫面提示**：名人語錄的人名要是英文。
8. **球員個人頁**：守位、能力名稱、合約用語（續約、跳脫條款、下放權）。
9. **教練與總經理資料**：背景介紹的人名要是英文。

回報方式：截圖加上畫面名稱，說明哪裡不對（意思錯、看不懂、該英文的變中文等）。修正會寫進 `tools/gui_fixes.tsv`、`tools/tutorial_fixes.tsv` 等修正表，重跑工具也不會被洗掉。

## Steam 更新後中文不見

Steam 更新或「驗證遊戲檔案」會把檔案還原成官方原檔。步驟見 [PORTING-27.md](PORTING-27.md)「改版後重裝」：

1. 逐檔比對新版原檔和 `~/ootp27-backup-original`，找出改版動到的檔。
2. 沒動到的直接把備份複製回去。
3. 動到的檔，用新版原檔重跑對應的 `tools/merge_*.py`，`merge_korean.py --todo` 補翻新增句。
4. `preflight.py` 全部通過後再複製進遊戲。

## 還原成原版

- Steam：遊戲右鍵 →「內容」→「已安裝檔案」→「驗證遊戲檔案的完整性」。
- 或把 `~/ootp27-backup-original` 複製回遊戲 `data/`。

## 維護工具

| 工具 | 用途 |
|---|---|
| `tools/check_ootp27.py` | 檢查新版原檔能不能直接套用合併工具 |
| `tools/merge_gui.py` | 產生介面 `<KR>`（修正表 `gui_fixes.tsv`） |
| `tools/merge_korean.py` | 播報文字；`--todo` 列未翻、`--verify` 檢查 |
| `tools/apply_zh.py` | 把「id<TAB>中文」套進播報，佔位符對英文原檔檢查 |
| `tools/merge_tutorial.py` | 教學（修正表 `tutorial_fixes.tsv`；英文相同才沿用舊翻譯） |
| `tools/merge_storylines.py` | 收件匣劇情與傷病描述 |
| `tools/merge_extras.py` | 教練背景、球隊暱稱、授權條款 |
| `tools/merge_world.py`、`merge_schools.py`、`localize_names.py` | 國家城市、學校、人名資料 |
| `tools/qa.py` | 內部檢核：同一英文多種譯法、違反術語表、中國用語 |
| `tools/build_chinese.py` | 所有 merge 跑完後執行：把韓文欄位的翻譯同步到中文欄位與中文檔、人名中文欄改英文 |
| `tools/preflight.py` | 裝前檢查：編碼、換行、XML、跳脫字元、行數、字型 |

工具都要放 27 版原檔到 `temp/`（見 PORTING-27.md）。歷史進度見 [PROGRESS.md](PROGRESS.md)。

## 授權

上游專案沒有附授權條款，本 fork 僅供個人使用，請勿另外散布翻譯檔。遊戲內容版權屬 Out of the Park Developments。
