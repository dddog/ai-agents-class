import dotenv

# .env 파일에서 환경변수(OpenAI API Key 등)를 로드
dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import streamlit as st
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from models import UserAccountContext
from my_agents.triage_agent import triage_agent

# OpenAI 클라이언트 초기화
client = OpenAI()

# 기본 로그인 상태를 시뮬레이션하기 위한 사용자 계정 컨텍스트 정의
user_account_ctx = UserAccountContext(
    customer_id=1,
    name="nico",
    tier="basic",
)


# Streamlit 세션 내 대화 이력 저장용 SQLiteSession 초기화
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "customer-support-memory.db",
    )
session = st.session_state["session"]

# 현재 활성화된 에이전트를 세션 상태에 저장 (최초 진입 시 Triage Agent)
if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent


# 이전 대화 기록을 화면에 로드하여 렌더링하는 비동기 함수
async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        # $ 기호가 Streamlit LaTeX 수식 렌더러와 충돌하지 않도록 이스케이프 처리
                        st.write(message["content"][0]["text"].replace("$", "\$"))


# 저장된 이전 대화 렌더링 실행
asyncio.run(paint_history())


# 에이전트를 실행하고 출력을 스트리밍하는 함수
async def run_agent(message):

    with st.chat_message("ai"):
        text_placeholder = st.empty()  # 텍스트가 실시간으로 입력되는 효과를 주기 위한 빈 컨테이너
        response = ""

        st.session_state["text_placeholder"] = text_placeholder

        try:
            # Runner를 이용해 비동기 스트림 실행 시작
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=user_account_ctx,
            )

            async for event in stream.stream_events():
                # LLM의 날것(Raw) 텍스트 조각이 출력되는 이벤트 처리
                if event.type == "raw_response_event":

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        # 스트림 텍스트를 실시간으로 화면에 렌더링
                        text_placeholder.write(response.replace("$", "\$"))

                # 실행 에이전트가 Handoff에 의해 변경되는 이벤트 처리
                elif event.type == "agent_updated_stream_event":

                    if st.session_state["agent"].name != event.new_agent.name:
                        
                        # 에이전트 전환 사실을 UI에 표기
                        st.write(f"🤖 Transfered from {st.session_state['agent'].name} to {event.new_agent.name}")

                        # 세션 내 활성 에이전트 업데이트 및 출력 컨테이너 리셋
                        st.session_state["agent"] = event.new_agent
                        text_placeholder = st.empty()
                        st.session_state["text_placeholder"] = text_placeholder
                        response = ""

        # 입력 가드레일(부적절한 질문 차단 등)이 트리거되었을 때의 예외 처리
        except InputGuardrailTripwireTriggered:
            st.write("I can't help you with that.")

        # 출력 가드레일(부적절한 응답 차단 등)이 트리거되었을 때의 예외 처리
        except OutputGuardrailTripwireTriggered:
            st.write("Cant show you that answer.")
            st.session_state["text_placeholder"].empty()

# 사용자 입력창 생성
message = st.chat_input(
    "Write a message for your assistant",
)

# 사용자가 새로운 메시지를 입력하면 동작 수행
if message:

    if message:
        with st.chat_message("human"):
            st.write(message)
        # 에이전트 비동기 실행 루프 호출
        asyncio.run(run_agent(message))


# 사이드바 설정 (대화 기록 리셋 기능 및 현재 원시 세션 데이터 조회 기능 제공)
with st.sidebar:
    reset = st.button("Reset memory")
    if reset:
        asyncio.run(session.clear_session())
    st.write(asyncio.run(session.get_items()))