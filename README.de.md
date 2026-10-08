[日本語](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md) | [한국어](README.ko.md) | [Français](README.fr.md) | **Deutsch**

# manaba-cli

Inoffizielle, nur lesende Kommandozeile für [manaba](https://nagasaki-gaigo.manaba.jp/ct/login) an der Fremdsprachenuniversität Nagasaki.

[manaba](https://manaba.jp/products/) ist der Cloud-Lerndienst von Asahi Net. Viele Schulen in Japan nutzen dasselbe System für Kursnachrichten, Materialien, Foren, Tests, Berichte, Projekte, Noten und Portfolios. Dieses CLI spricht nur mit der Seite der Fremdsprachenuniversität Nagasaki.

Die Anmeldung erfolgt in einem Terminal auf dem eigenen Rechner. Passwörter, Cookies und die Sitzungsdatei gehören nicht in git und nicht in einen Chat. Das ist kein offizielles Werkzeug der Universität.

Die Befehlsausgaben sind derzeit auf traditionellem Chinesisch.

## Was gelesen wird

Das Studierendenhandbuch steht [hier](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/). Die Funktionsübersicht steht [hier](https://manaba.jp/products/function/).

- Kurse
- Nicht abgegebene Aufgaben (Tests, Übungen, Umfragen, Berichte, Projekte)
- Kursnachrichten
- Kursinhalte
- Forum
- Tests und Übungen
- Umfragen
- Berichte
- Projekte
- Noten
- Portfolio
- Abgabeverlauf

Es gibt keine Abgabe, keine Umfrageantwort und keinen Anwesenheitscode. Anwesenheit ist eine optionale manaba-Funktion und nicht Teil dieses CLI.

## Installation

Python 3.11 oder neuer.

```bash
git clone https://github.com/miku2339/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Der Befehl heißt `manaba`.

## Anmeldung

Nur in einem lokalen Terminal ausführen. Wenn die Standardeingabe kein Terminal ist, wird das Passwort nicht gelesen. Passwörter in Umgebungsvariablen werden ebenfalls ignoriert.

```bash
manaba login
manaba login --store-password
```

`--store-password` speichert Benutzer-ID und Passwort im macOS-Schlüsselbund (Dienst `manaba.cli`). Die Sitzung liegt in `~/.local/share/manaba-cli/session.json` mit den Rechten `0600`.

```bash
manaba logout
```

## Lesen

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

`tasks` ist die Liste der nicht abgegebenen Aufgaben. `--kind quiz` schließt Übungen ein. `download` verlässt den manaba-Host dieser Universität nicht und überschreibt keine vorhandene Datei.

`unverified` heißt, dass die Seite nicht gelesen werden konnte. Es heißt nicht, dass es keinen Kurs oder keine Aufgabe gibt. Ein unbekanntes Seitenlayout ist ebenfalls `unverified`.

## Agenten

Siehe `AGENTS.md`. Ein Agent darf nur die lesenden Befehle mit `--json` ausführen. `manaba login` nicht starten.

## Lizenz

MIT.
