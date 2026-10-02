# Agent contract

manaba 是朝日ネット的雲端 LMS。這份 repo 的 CLI 只讀長崎外國語大學的站：`https://nagasaki-gaigo.manaba.jp`。

預設說明在日文 `README.md`。另外有繁體中文、英文、韓文、法文、德文。

- 二進位：`"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba"`
- 可以跑：`status`、`courses`、`tasks`、`course`、`news`、`reports`、`quizzes`、`surveys`、`projects`、`topics`、`contents`、`grades`、`portfolio`、`submissions`、`download`，一律加 `--json`
- 不要跑 `manaba login` 或 `manaba logout`
- 不要印密碼、cookie、session JSON、Keychain 內容
- 沒有 session，或版面認不出來，是 `unverified`，不是「沒有作業」
- 不要把整份教材、成績或ポートフォリオ貼進聊天；用標題、期限、檔名和短摘錄
- 不要代交レポート、小測試、アンケート、出席

登入由 QIXI 在本機 Terminal 執行：

```bash
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" login
```
