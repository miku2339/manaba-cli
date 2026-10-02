**日本語** | [繁體中文](README.zh-TW.md) | [English](README.en.md) | [한국어](README.ko.md) | [Français](README.fr.md) | [Deutsch](README.de.md)

# manaba-cli

長崎外国語大学の [manaba](https://nagasaki-gaigo.manaba.jp/ct/login) 向け、非公式の読み取り専用 CLI です。

[manaba](https://manaba.jp/products/)（マナバ）は株式会社朝日ネットのクラウド型教育支援サービスです。日本の多くの学校が同じシステムを使っています。コースニュース、教材、掲示板、小テスト、レポート、プロジェクト、成績、ポートフォリオを、授業の前後と授業中に扱います。この CLI が接続するのは長崎外国語大学のサイトだけです。

ログインは自分のパソコンのターミナルで行います。パスワード、Cookie、セッションファイルは git に入れず、チャットにも貼らないでください。これは大学の公式ツールではありません。

コマンドが表示する文章は、いまのところ繁體中文です。

## 読むもの

学生マニュアルは [こちら](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/)、機能紹介は [こちら](https://manaba.jp/products/function/) です。

- コース
- 未提出課題（小テスト、ドリル、アンケート、レポート、プロジェクト）
- コースニュース
- コースコンテンツ
- 掲示板
- 小テストとドリル
- アンケート
- レポート
- プロジェクト
- 成績
- ポートフォリオ
- 提出記録

課題の提出、アンケートの回答、出席コードの送信はしません。出席は manaba のオプション機能で、この CLI の対象外です。

## インストール

Python 3.11 以上。

```bash
git clone https://github.com/miku233333/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

コマンド名は `manaba` です。

## ログイン

ローカルのターミナルだけで実行します。標準入力がターミナルでないときは、パスワードの入力を拒否します。環境変数のパスワードは読みません。

```bash
manaba login
manaba login --store-password
```

`--store-password` はユーザIDとパスワードを macOS のキーチェーン（サービス名 `manaba.cli`）へ保存します。セッションは `~/.local/share/manaba-cli/session.json`、権限は `0600` です。

```bash
manaba logout
```

## 読み取り

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

`tasks` は未提出課題です。`--kind quiz` にはドリルも含まれます。`download` は長崎外国語大学の manaba 以外へは送りません。すでにあるファイルは上書きしません。

`unverified` は、まだ読めていないという意味です。授業がない、課題がない、という意味ではありません。ページの形が変わって中身を判別できないときも `unverified` です。

## エージェント

`AGENTS.md` を参照してください。エージェントが実行してよいのは、読み取り専用コマンドに `--json` を付けたものだけです。`manaba login` は実行しないでください。

## ライセンス

MIT。
