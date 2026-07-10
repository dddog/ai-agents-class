# 스마트 플래시카드 코치 (Country Guessing Game)

본 프로젝트는 **LangGraph**를 활용하여 구축된 대화형 인공지능 에이전트로, 사용자가 무작위로 출제되는 국가 관련 퀴즈를 풀고 피드백을 받을 수 있는 교육용 게임입니다.

## 🚀 에이전트 주요 기능

1. **지식 보강형 퀴즈 출제 (Tool 연동)**
   - 위키피디아(Wikipedia) 검색 도구를 연동하여 단순한 문제를 넘어 풍부한 배경지식을 포함한 고품질 퀴즈를 생성합니다.

2. **병렬 처리 아키텍처 (Send API)**
   - 여러 개의 국가 개념을 LangGraph의 `Send` API를 통해 병렬(동시)로 처리하여 퀴즈 생성 속도를 극대화합니다.

3. **휴먼 인 더 루프 (Human-in-the-Loop)**
   - `interrupt` 기능을 활용하여 사용자가 퀴즈 답변을 입력할 때까지 에이전트가 대기(Pause)하고, 답변 데이터가 들어오면 즉시 실행을 재개(Resume)합니다.

4. **동적 힌트 제공 및 재도전 루프 (Conditional Edge)**
   - 채점 결과가 기준 점수(예: 80점) 미만일 경우 오답 힌트 노드(`generate_hint`)로 분기하여 정답의 일부(첫 글자 등)를 힌트로 제공한 뒤 재도전을 유도합니다.

## 🛠 기술 스택
- **Python 3.13+**
- **LangGraph** (StateGraph, InMemorySaver 등)
- **LangChain & OpenAI** (GPT-4o-mini 모델)
- **uv** (고속 패키지 및 가상환경 관리)

## 💻 실행 방법

### 1. 의존성 설치
```bash
uv sync
```

### 2. 로컬 개발 서버 실행
```bash
uv run langgraph dev
```

### 3. 게임 테스트
서버 구동 후 출력되는 **LangSmith Studio UI** 접속 링크(예: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`)에 접속한 뒤, 좌측 `+ New Thread`를 생성하여 게임을 진행합니다.
