[日本語](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md) | [한국어](README.ko.md) | **Français** | [Deutsch](README.de.md)

# manaba-cli

CLI non officiel, en lecture seule, pour le [manaba](https://nagasaki-gaigo.manaba.jp/ct/login) de l’Université des langues étrangères de Nagasaki.

[manaba](https://manaba.jp/products/) est le service d’apprentissage en ligne d’Asahi Net. Beaucoup d’établissements au Japon utilisent le même outil pour les annonces de cours, les documents, les forums, les quiz, les devoirs, les projets, les notes et le portfolio. Ce CLI ne contacte que le site de l’Université des langues étrangères de Nagasaki.

La connexion se fait dans un terminal sur votre ordinateur. Ne mettez pas les mots de passe, les cookies ni le fichier de session dans git, et ne les collez pas dans une conversation. Ce n’est pas un outil officiel de l’université.

Les messages affichés par les commandes sont pour l’instant en chinois traditionnel.

## Ce qui est lu

Le manuel étudiant est [ici](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/). La présentation des fonctions est [ici](https://manaba.jp/products/function/).

- Cours
- Travaux non rendus (quiz, exercices, questionnaires, devoirs, projets)
- Annonces du cours
- Contenus du cours
- Forum
- Quiz et exercices
- Questionnaires
- Devoirs
- Projets
- Notes
- Portfolio
- Historique des remises

Le CLI n’envoie pas de devoir, ne répond pas aux questionnaires et n’envoie pas de code de présence. La présence est une option de manaba, hors du périmètre de cet outil.

## Installation

Python 3.11 ou plus récent.

```bash
git clone https://github.com/miku233333/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

La commande s’appelle `manaba`.

## Connexion

À lancer seulement dans un terminal local. Si l’entrée standard n’est pas un terminal, le CLI refuse de lire un mot de passe. Il ignore aussi les mots de passe placés dans les variables d’environnement.

```bash
manaba login
manaba login --store-password
```

`--store-password` enregistre l’identifiant et le mot de passe dans le Trousseau macOS (service `manaba.cli`). La session est dans `~/.local/share/manaba-cli/session.json`, avec les droits `0600`.

```bash
manaba logout
```

## Lecture

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

`tasks` est la liste des travaux non rendus. `--kind quiz` inclut les exercices. `download` ne quitte pas le manaba de cette université et n’écrase pas un fichier déjà présent.

`unverified` veut dire que la page n’a pas pu être lue. Cela ne veut pas dire qu’il n’y a pas de cours ni de devoir. Une mise en page non reconnue est aussi `unverified`.

## Agents

Voir `AGENTS.md`. Un agent ne peut lancer que les commandes en lecture seule avec `--json`. Ne lancez pas `manaba login`.

## Licence

MIT.
