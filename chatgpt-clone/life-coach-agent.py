import dotenv

dotenv.load_dotenv()
from openai import OpenAI
import asyncio
import base64
import streamlit as st
from agents import (
    Agent,
    Runner,
    SQLiteSession,
    WebSearchTool,
    FileSearchTool,
    ImageGenerationTool,
    CodeInterpreterTool,
    HostedMCPTool,
)
from agents.mcp.server import MCPServerStdio

client = OpenAI()

VECTOR_STORE_ID = "vs_6a30aa4142888191ae887b9663eda988"

# 세션 상태 초기화 (메모리 DB 연결)
if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "chat-history",
        "chat-gpt-clone-memory.db",
    )
session = st.session_state["session"]


# 과거 대화 기록을 화면에 그리는 함수
async def paint_history():
    messages = await session.get_items()

    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    content = message["content"]
                    if isinstance(content, str):
                        st.write(content)
                    elif isinstance(content, list):
                        for part in content:
                            if "image_url" in part:
                                st.image(part["image_url"])

                else:
                    # AI가 답변한 텍스트 메시지 출력
                    if message["type"] == "message":
                        st.write(message["content"][0]["text"].replace("$", "\$"))

        if "type" in message:
            message_type = message["type"]
            if message_type == "web_search_call":
                with st.chat_message("ai"):
                    st.write("🔍 웹에서 유용한 조언과 팁을 검색했습니다...")
            elif message_type == "file_search_call":
                with st.chat_message("ai"):
                    st.write("🗂️ 사용자의 파일을 참조했습니다...")
            elif message_type == "image_generation_call":
                image = base64.b64decode(message["result"])
                with st.chat_message("ai"):
                    st.write("🎨 생성된 이미지 입니다:")
                    st.image(image)
            elif message_type == "code_interpreter_call":
                with st.chat_message("ai"):
                    st.write("🤖 데이터를 분석하고 코드를 실행했습니다:")
                    st.code(message["code"])
            elif message_type == "mcp_list_tools":
                with st.chat_message("ai"):
                    st.write(f"⚒️ {message['server_label']} 서버의 도구 목록을 가져왔습니다.")
            elif message_type == "mcp_call":
                with st.chat_message("ai"):
                    st.write(
                        f"⚒️ {message['server_label']}의 {message['name']} 도구를 실행했습니다. (인자: {message['arguments']})"
                    )


asyncio.run(paint_history())


def update_status(status_container, event):

    status_messages = {
        "response.web_search_call.completed": ("✅ 웹 검색이 완료되었습니다.", "complete"),
        "response.web_search_call.in_progress": (
            "🔍 라이프 코칭을 위한 최신 정보 검색 시작...",
            "running",
        ),
        "response.web_search_call.searching": (
            "🔍 조언, 팁, 동기부여 콘텐츠를 검색하는 중...",
            "running",
        ),
        "response.file_search_call.completed": (
            "✅ 개인 목표 및 다이어리 참조 완료.",
            "complete",
        ),
        "response.file_search_call.in_progress": (
            "🗂️ 사용자의 목표 및 일기 파일을 확인하는 중...",
            "running",
        ),
        "response.file_search_call.searching": (
            "🗂️ 파일 내 일기 및 다이어리 내용을 참조하는 중...",
            "running",
        ),
        "response.image_generation_call.generating": (
            "🎨 맞춤형 비전 보드 및 동기부여 포스터 그리는 중...",
            "running",
        ),
        "response.image_generation_call.in_progress": (
            "🎨 동기부여 이미지 생성 중...",
            "running",
        ),
        "response.code_interpreter_call_code.done": (
            "🤖 목표 달성률 계산 및 코드 실행 완료.",
            "complete",
        ),
        "response.code_interpreter_call.completed": (
            "🤖 코드 분석 완료.",
            "complete",
        ),
        "response.code_interpreter_call.in_progress": (
            "🤖 목표 데이터 분석 중...",
            "complete",
        ),
        "response.code_interpreter_call.interpreting": (
            "🤖 데이터 코드 해석 중...",
            "complete",
        ),
        "response.mcp_call.completed": (
            "⚒️ 도구 호출 완료",
            "complete",
        ),
        "response.mcp_call.failed": (
            "⚒️ 도구 호출 중 오류가 발생했습니다.",
            "complete",
        ),
        "response.mcp_call.in_progress": (
            "⚒️ 연동된 외부 도구를 사용하는 중...",
            "running",
        ),
        "response.mcp_list_tools.completed": (
            "⚒️ 연동 도구 목록 확인 완료",
            "complete",
        ),
        "response.mcp_list_tools.failed": (
            "⚒️ 연동 도구 목록을 가져오지 못했습니다.",
            "complete",
        ),
        "response.mcp_list_tools.in_progress": (
            "⚒️ 사용할 수 있는 외부 도구를 탐색 중...",
            "running",
        ),
        "response.completed": (" ", "complete"),
    }

    if event in status_messages:
        label, state = status_messages[event]
        status_container.update(label=label, state=state)


# 에이전트를 구동하는 메인 비동기 함수
async def run_agent(message):
    yfinance_server = MCPServerStdio(
        params={
            "command": "uvx",
            "args": ["mcp-yahoo-finance"],
        },
        cache_tools_list=True,
        client_session_timeout_seconds=60,
    )

    timezone_server = MCPServerStdio(
        params={
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone=America/New_York"],
        },
        client_session_timeout_seconds=60,
    )

    async with yfinance_server, timezone_server:

        agent = Agent(
            mcp_servers=[
                yfinance_server,
                timezone_server,
            ],
            name="나만의 라이프 코치 (Life Coach)", # 에이전트 이름 변경
            instructions="""
        당신은 사용자의 삶을 더 나은 방향으로 이끌어주는 따뜻하고 전문적인 '나만의 라이프 코치(Life Coach)' 에이전트입니다.
        사용자의 목표 달성, 습관 형성, 멘탈 관리를 돕고 동기부여를 주는 것이 주 임무입니다.

        당신은 아래와 같은 강력한 도구들을 가지고 있으며, 상황에 맞게 적극적으로 활용해야 합니다:
            - 웹 검색 도구 (Web Search Tool): 사용자가 최신 고민이나 조언, 팁, 웰빙 정보, 동기부여가 되는 인용구 및 최신 콘텐츠를 요구할 때 사용하세요.
            - 파일 검색 도구 (File Search Tool): 사용자가 과거에 작성한 개인 목표, 다이어리, 일기 등의 파일을 기반으로 맞춤형 코칭을 원할 때 이 도구로 해당 내용을 참조하세요.
            - 이미지 생성 도구 (Image GenerationTool): 사용자가 목표를 시각화하고 싶어 하거나, 비전 보드(Vision Board) 제작, 혹은 격려가 되는 동기부여 포스터를 만들어 달라고 요청할 때 적극적으로 사용하여 멋진 이미지를 그려주세요.
            - 코드 인터프리터 도구 (Code Interpreter Tool): 사용자의 목표 달성률, 습관 추적 그래프 생성, 점수 계산 등 데이터 기반의 통계나 시각화가 필요할 때 코드를 작성하고 실행하세요.
            
        대화할 때는 항상 긍정적이고 지지하는 어조를 유지하며, 사용자가 시각적 자극을 원할 때는 이미지 생성 도구를 통해 비전 보드를 제공하세요.
        """, # 페르소나 및 지침 한글 맞춤 고도화
            tools=[
                WebSearchTool(),
                FileSearchTool(
                    vector_store_ids=[VECTOR_STORE_ID],
                    max_num_results=3,
                ),
                ImageGenerationTool(
                    tool_config={
                        "type": "image_generation",
                        "quality": "high",
                        "output_format": "jpeg",
                        "partial_images": 1,
                    }
                ),
                CodeInterpreterTool(
                    tool_config={
                        "type": "code_interpreter",
                        "container": {
                            "type": "auto",
                        },
                    }
                ),
                HostedMCPTool(
                    tool_config={
                        "server_url": "https://mcp.context7.com/mcp",
                        "type": "mcp",
                        "server_label": "Context7",
                        "server_description": "소프트웨어 프로젝트 문서나 가이드를 가져올 때 사용합니다.",
                        "require_approval": "never",
                    }
                ),
            ],
        )

        with st.chat_message("ai"):
            status_container = st.status("⏳ 라이프 코치가 생각하는 중...", expanded=False)
            code_placeholder = st.empty()
            image_placeholder = st.empty()
            text_placeholder = st.empty()
            response = ""
            code_response = ""

            st.session_state["code_placeholder"] = code_placeholder
            st.session_state["image_placeholder"] = image_placeholder
            st.session_state["text_placeholder"] = text_placeholder

            stream = Runner.run_streamed(
                agent,
                message,
                session=session,
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":

                    update_status(status_container, event.data.type)

                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))

                    if event.data.type == "response.code_interpreter_call_code.delta":
                        code_response += event.data.delta
                        code_placeholder.code(code_response)

                    elif (
                        event.data.type
                        == "response.image_generation_call.partial_image"
                    ):
                        image = base64.b64decode(event.data.partial_image_b64)
                        image_placeholder.image(image)


prompt = st.chat_input(
    "라이프 코치에게 이야기하거나 목표를 공유해 보세요... (예: 내 올해 목표에 맞는 비전 보드 그려줘)",
    accept_file=True,
    file_type=[
        "txt",
        "jpg",
        "jpeg",
        "png",
    ],
)

if prompt:

    if "code_placeholder" in st.session_state:
        st.session_state["code_placeholder"].empty()
    if "image_placeholder" in st.session_state:
        st.session_state["image_placeholder"].empty()
    if "text_placeholder" in st.session_state:
        st.session_state["text_placeholder"].empty()

    for file in prompt.files:
        if file.type.startswith("text/"):
            with st.chat_message("ai"):
                with st.status("⏳ 일기/목표 파일 업로드 중...") as status:
                    uploaded_file = client.files.create(
                        file=(file.name, file.getvalue()),
                        purpose="user_data",
                    )
                    status.update(label="⏳ 멘토링 벡터 스토어에 파일 분석 및 추가 중...")
                    client.vector_stores.files.create(
                        vector_store_id=VECTOR_STORE_ID,
                        file_id=uploaded_file.id,
                    )
                    status.update(label="✅ 파일 분석 완료! 코칭에 반영합니다.", state="complete")
        elif file.type.startswith("image/"):
            with st.status("⏳ 이미지 파일 분석 중...") as status:
                file_bytes = file.getvalue()
                base64_data = base64.b64encode(file_bytes).decode("utf-8")
                data_uri = f"data:{file.type};base64,{base64_data}"
                asyncio.run(
                    session.add_items(
                        [
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "input_image",
                                        "detail": "auto",
                                        "image_url": data_uri,
                                    }
                                ],
                            }
                        ]
                    )
                )
                status.update(label="✅ 분석용 이미지 업로드 완료", state="complete")
            with st.chat_message("human"):
                st.image(data_uri)

    if prompt.text:
        with st.chat_message("human"):
            st.write(prompt.text)
        asyncio.run(run_agent(prompt.text))


with st.sidebar:
    reset = st.button("코칭 대화 기록 초기화") # 한글 변경
    if reset:
        asyncio.run(session.clear_session())
        st.success("대화 메모리가 초기화되었습니다.") # 피드백 문구 추가
    
    st.write("### 현재 저장된 코칭 세션 데이터") # 타이틀 한글 추가
    st.write(asyncio.run(session.get_items()))