[日本語](README.md) | [繁體中文](README.zh-TW.md) | **English** | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# manaba-cli

An unofficial read-only CLI for [manaba](https://nagasaki-gaigo.manaba.jp/ct/login) at Nagasaki University of Foreign Studies.

[manaba](https://manaba.jp/products/) is Asahi Net’s cloud learning system. Many schools in Japan use the same product for course news, materials, boards, quizzes, reports, projects, grades, and portfolios. This CLI talks only to the Nagasaki University of Foreign Studies site.

Sign in from a terminal on your own computer. Do not commit passwords, cookies, or the session file, and do not paste them into chat. This is not an official university tool.

Command output is currently written in Traditional Chinese.

## What it reads

The student manual is [here](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/). The feature overview is [here](https://manaba.jp/products/function/).

- Courses
- Unsubmitted work (quizzes, drills, surveys, reports, projects)
- Course news
- Course content
- Boards
- Quizzes and drills
- Surveys
- Reports
- Projects
- Grades
- Portfolio
- Submission history

It does not submit work, answer surveys, or send attendance codes. Attendance is an optional manaba add-on and is out of scope.

## Install

Python 3.11 or newer.

```bash
git clone https://github.com/miku2339/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

The command is `manaba`.

## Sign in

Run this only in a local terminal. If stdin is not a terminal, the CLI refuses to read a password. It also ignores passwords in environment variables.

```bash
manaba login
manaba login --store-password
```

`--store-password` stores the user ID and password in the macOS Keychain (service `manaba.cli`). The session file is `~/.local/share/manaba-cli/session.json` with mode `0600`.

```bash
manaba logout
```

## Read

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

`tasks` is the unsubmitted-work list. `--kind quiz` includes drills. `download` never leaves the university’s manaba host, and it will not overwrite an existing file.

`unverified` means the CLI could not read the page. It does not mean there is no class or no assignment. An unrecognized page layout is also `unverified`.

## Agents

See `AGENTS.md`. An agent may run the read-only commands with `--json` only. Do not run `manaba login`.

## License

MIT.
