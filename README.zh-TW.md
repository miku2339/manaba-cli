[日本語](README.md) | **繁體中文** | [English](README.en.md) | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# manaba-cli

給長崎外國語大學 [manaba](https://nagasaki-gaigo.manaba.jp/ct/login) 用的非官方唯讀 CLI。

[manaba](https://manaba.jp/products/)（マナバ）是朝日ネット的雲端學習系統，日本很多學校用同一套。它可以發課程消息、教材、討論區、小測驗、報告、專案、成績和學習歷程。這支程式只連長崎外國語大學的站台。

登入在自己電腦的終端機做。密碼、cookie、session 檔不要進 git，也不要貼到聊天裡。這不是學校的官方工具。

指令畫面上的句子目前是繁體中文。

## 會讀的內容

學生手冊在[這裡](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/)，功能介紹在[這裡](https://manaba.jp/products/function/)。

- 課程
- 未繳交作業（小測驗、ドリル、問卷、報告、專案）
- 課程新聞
- 課程內容
- 討論區
- 小測驗與ドリル
- 問卷
- 報告
- 專案
- 成績
- 學習歷程（ポートフォリオ）
- 繳交紀錄

不代交作業、不填問卷、不送出席碼。出席是 manaba 的選配功能，不在這支 CLI 裡。

## 安裝

需要 Python 3.11 以上。

```bash
git clone https://github.com/miku2339/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

指令名稱是 `manaba`。

## 登入

只在本機終端機執行。stdin 不是終端機時，會拒絕讀取密碼。也不讀環境變數裡的密碼。

```bash
manaba login
manaba login --store-password
```

`--store-password` 會把ユーザID和密碼放進 macOS 鑰匙圈（服務名稱 `manaba.cli`）。session 在 `~/.local/share/manaba-cli/session.json`，權限是 `0600`。

```bash
manaba logout
```

## 讀取

```bash
manaba status --json
manaba courses --json
manaba tasks --json
manaba tasks --kind report --json
manaba course 12345 --json
manaba news 12345 --json
manaba reports 12345 --json
manaba quizzes 12345 --json
manaba surveys 12345 --json
manaba projects 12345 --json
manaba topics 12345 --json
manaba contents 12345 --json
manaba grades 12345 --json
manaba portfolio --json
manaba submissions --json
manaba download 'page_15?c12345' -o ./week1.pdf --json
```

`tasks` 是未繳交作業。`--kind quiz` 會連ドリル一起列出。`download` 只會向長崎外國語大學的 manaba 要檔案，已存在的檔案不會覆寫。

`unverified` 的意思是還沒讀到，不是「沒有課」或「沒有作業」。頁面版面認不出來時也是 `unverified`。

## Agent

看 `AGENTS.md`。Agent 只能跑加上 `--json` 的唯讀指令。不要跑 `manaba login`。

## 授權

MIT。
