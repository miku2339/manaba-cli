[日本語](README.md) | [繁體中文](README.zh-TW.md) | [English](README.en.md) | **한국어** | [Français](README.fr.md) | [Deutsch](README.de.md)

# manaba-cli

나가사키 외국어 대학 [manaba](https://nagasaki-gaigo.manaba.jp/ct/login)용 비공식 읽기 전용 CLI입니다.

[manaba](https://manaba.jp/products/)는 아사히넷의 클라우드 학습 시스템입니다. 일본의 많은 학교가 같은 시스템으로 과목 소식, 교재, 게시판, 퀴즈, 리포트, 프로젝트, 성적, 포트폴리오를 다룹니다. 이 CLI는 나가사키 외국어 대학 사이트에만 접속합니다.

로그인은 자기 컴퓨터의 터미널에서 합니다. 비밀번호, 쿠키, 세션 파일은 git에 넣지 말고 채팅에도 붙여 넣지 마세요. 대학 공식 도구가 아닙니다.

명령이 보여주는 문장은 현재 번체 중국어입니다.

## 읽는 항목

학생 매뉴얼은 [여기](https://doc.manaba.jp/doc/course2-manual/student2.976/ja/), 기능 소개는 [여기](https://manaba.jp/products/function/)에 있습니다.

- 과목
- 미제출 과제(퀴즈, 드릴, 설문, 리포트, 프로젝트)
- 과목 소식
- 과목 콘텐츠
- 게시판
- 퀴즈와 드릴
- 설문
- 리포트
- 프로젝트
- 성적
- 포트폴리오
- 제출 기록

과제를 제출하거나, 설문에 답하거나, 출석 코드를 보내지 않습니다. 출석은 manaba의 선택 기능이며 이 CLI의 범위 밖입니다.

## 설치

Python 3.11 이상이 필요합니다.

```bash
git clone https://github.com/miku233333/manaba-cli.git
cd manaba-cli
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

명령 이름은 `manaba`입니다.

## 로그인

로컬 터미널에서만 실행합니다. stdin이 터미널이 아니면 비밀번호 입력을 거부합니다. 환경 변수의 비밀번호도 읽지 않습니다.

```bash
manaba login
manaba login --store-password
```

`--store-password`는 사용자 ID와 비밀번호를 macOS 키체인(서비스 이름 `manaba.cli`)에 저장합니다. 세션 파일은 `~/.local/share/manaba-cli/session.json`이고 권한은 `0600`입니다.

```bash
manaba logout
```

## 조회

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

`tasks`는 미제출 과제입니다. `--kind quiz`에는 드릴도 포함됩니다. `download`는 이 대학 manaba 이외의 호스트로 요청하지 않으며, 이미 있는 파일은 덮어쓰지 않습니다.

`unverified`는 아직 읽지 못했다는 뜻입니다. 수업이나 과제가 없다는 뜻이 아닙니다. 화면 구조를 알아보지 못해도 `unverified`입니다.

## 에이전트

`AGENTS.md`를 보세요. 에이전트는 `--json`을 붙인 읽기 전용 명령만 실행할 수 있습니다. `manaba login`은 실행하지 마세요.

## 라이선스

MIT.
