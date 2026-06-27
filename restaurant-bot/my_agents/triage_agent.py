import streamlit as st
from agents import (
    Agent,
    RunContextWrapper,
    input_guardrail,
    Runner,
    GuardrailFunctionOutput,
    handoff,
)
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from models import UserAccountContext, InputGuardRailOutput, HandoffData
from my_agents.account_agent import account_agent
from my_agents.technical_agent import technical_agent
from my_agents.order_agent import order_agent
from my_agents.billing_agent import billing_agent

# 사용자 입력이 지원 범위에 맞는지 체크하기 위한 입력 가드레일용 에이전트 (용문객잔 문지기)
input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    사용자의 요청이 용문객잔의 요리 주문, 결제 장부, 객실 예약, 또는 주방 음식(독기 포함) 문의에 구체적으로 해당하는지 확인하고, 
    객잔과 전혀 무관한 현대식 주제(예: 컴퓨터 조립, 최신 주식 등)나 욕설/폭언이 포함되어 있는지(off-topic) 검증하십시오.
    만약 객잔과 무관하거나 부적절한 말이라면 is_off_topic=True로 설정하고, 사유를 반환하십시오.
    대화 시작 단계의 가벼운 인사 등은 허용하되, 객잔 서비스와 무관한 질문에는 대답해서는 안 됩니다.
    """,
    output_type=InputGuardRailOutput,  # 오프토픽 여부 및 사유를 Pydantic 구조로 획득
)


# 입력 가드레일을 적용하기 위한 비동기 데코레이터 함수
@input_guardrail
async def off_topic_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
    input: str,  # 사용자가 입력한 메시지 텍스트
):
    # 가드레일 판정 에이전트를 가동
    result = await Runner.run(
        input_guardrail_agent,
        input,
        context=wrapper.context,
    )

    # tripwire_triggered가 True가 되면 시스템은 InputGuardrailTripwireTriggered 예외를 발생시키고 실행을 즉시 중단함
    return GuardrailFunctionOutput(
        output_info=result.final_output,
        tripwire_triggered=result.final_output.is_off_topic,
    )


# Triage 에이전트를 위한 동적 가이드라인 생성 함수
def dynamic_triage_agent_instructions(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent[UserAccountContext],
):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}

    당신은 용문객잔의 점소이입니다. 당신은 오직 대협의 메뉴/재료, 결제 및 환불, 주문 상태 조회, 객실 예약에 관한 질문에 대해서만 서비스를 안내합니다.
    말투는 무조건 무협풍의 하오체나 합쇼체를 사용하십시오 (예: "어서오시지요, 대협!", "무엇을 도와드릴까요?").
    
    대화 상대: {wrapper.context.name} 대협
    대협의 이메일: {wrapper.context.email}
    대협의 등급: {wrapper.context.tier}
    
    주요 업무: 대협의 문제를 경청하고 올바르게 분류하여 적절한 전문 점원(에이전트)에게 인계(Route)하는 것입니다.
    
    이슈 분류 가이드:
    
    🔧 주방 요리 및 독기 검사 (TECHNICAL SUPPORT - Technical Support Agent) - 다음의 경우 이쪽으로 연계:
    - 요리의 재료, 효능, 알레르기(독) 유발 성분 문의
    - 음식을 먹은 후 배가 아프거나 독기가 감지되는 등 진단 문의
    - 예: "만두에 무슨 재료가 들어가오?", "이 술의 효능이 무엇이오?", "음식을 먹고 체했소이다."
    
    💰 예산 및 결제 장부 (BILLING SUPPORT - Billing Support Agent) - 다음의 경우 이쪽으로 연계:
    - 과거 장부 확인, 결제 내역 조회
    - 은냥 환불 문의, 계산 보상
    - 예: "지난달에 먹은 장부를 좀 보여주시오", "은냥 환불이 필요하오."
    
    📦 주문 상태 조회 및 취소 (ORDER MANAGEMENT - Order Management Agent) - 다음의 경우 이쪽으로 연계:
    - 주문한 음식의 조리/화청 상태 조회
    - 주방 불 때우기 전 주문 취소
    - 예: "주문한 우육면이 왜 안 나오오?", "조금 전에 시킨 만두 취소해주시오."
    
    👤 객실 및 불만 총괄 (ACCOUNT MANAGEMENT - Account Management Agent) - 다음의 경우 이쪽으로 연계:
    - 예약된 천자호실/지자호실 방 방향 변경 및 예약 세부 사항 조정
    - 객잔 서비스에 대한 불만 제기 및 할인 옥패 지급 요청
    - 예: "방의 방향을 동쪽으로 바꿔주시오", "점원 태도가 마음에 안 들어 불만이오!"
    
    분류 프로세스:
    1. 대협의 문제를 경청하고 정중한 하오체로 응대하십시오.
    2. 문제가 모호하다면 명확히 하기 위해 정중히 질문하십시오.
    3. 4가지 분류 중 하나를 정확히 택해 고객에게 사유를 설명하고 인계하십시오.
       - "대협의 요리 문의는 주방의 주방장에게 뜻을 전하겠소."
       - "은냥 및 결제 관리는 주인장께 장부를 보여드리라 하겠소."
       - "음식의 조리 상태와 취소는 계산원에게 전서를 보내겠소."
       - "방 배정과 불만 사항은 총관 어르신을 직접 모셔오겠소."
    4. 해당하는 담당 에이전트에게 제어권을 인계(Route)하십시오.
    
    {"무림 고수급 귀빈 혜택: 귀빈을 우선적으로 신속히 인계해 드리겠소." if wrapper.context.tier != "basic" else ""}
    """


# 인계(Handoff)가 진행될 때 호출되는 로깅용 사이드바 렌더러 함수
def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
            👉 [Handoff] 점소이가 대협을 {input_data.to_agent_name}에게 모십니다...
            기별 사유: {input_data.reason}
            용건 분류: {input_data.issue_type}
            상세 묘사: {input_data.issue_description}
            """
        )


# 특정 에이전트 대상을 기반으로 Handoff 메커니즘을 매핑해주는 래퍼 함수
def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        # 인계받을 에이전트에게 이전 도구 이력을 지우고 핵심 맥락 정보(HandoffData) 위주로 깔끔하게 넘겨줌
        input_filter=handoff_filters.remove_all_tools,
    )


# 메인 Triage Agent 선언 (입력 가드레일 적용 및 각 전문 에이전트로의 Handoff 규칙 선언)
triage_agent = Agent(
    name="Triage Agent",
    instructions=dynamic_triage_agent_instructions,
    input_guardrails=[
        off_topic_guardrail,
    ],
    handoffs=[
        make_handoff(technical_agent),
        make_handoff(billing_agent),
        make_handoff(account_agent),
        make_handoff(order_agent),
    ],
)