---
name: manaba-cli
description: Read-only CLI for Nagasaki University of Foreign Studies manaba (courses, unsubmitted tasks, news, reports, quizzes, portfolio). Use when the user mentions 長崎外大, manaba, 未提出課題, コースニュース, or manaba-cli. Never collect passwords, cookies, or session files in chat.
---

# manaba-cli

Binary: `"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba"`

manaba is Asahi Net's cloud LMS. This CLI talks only to `https://nagasaki-gaigo.manaba.jp`.

The default README is Japanese. Traditional Chinese, English, Korean, French, and German copies sit beside it.

## Hard rules

- Do not run `manaba login` or `manaba logout`. QIXI runs login in a local Terminal.
- Do not print passwords, cookies, session JSON, or Keychain items.
- Missing session or an unrecognized page is `unverified`, not "no homework".
- Do not paste whole course files, grades, or the portfolio into chat.
- Do not submit reports, quizzes, surveys, or attendance.

## Agent-safe commands

```bash
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" status --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" courses --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" tasks --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" course COURSE_ID --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" news COURSE_ID --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" reports COURSE_ID --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" quizzes COURSE_ID --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" grades COURSE_ID --json
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" portfolio --json
```

Return names, due times, filenames, `source`, and `captured_at`.

## Login (human Terminal only)

```bash
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" login
"/Users/ouqixi/Documents/ChatGPT/長崎外大cil/.venv/bin/manaba" login --store-password
```
