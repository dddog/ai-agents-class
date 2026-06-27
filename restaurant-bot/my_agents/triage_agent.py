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

# 사용자 입력이 지원 범위에 맞는지 체크하기 위한 입력 가드레일용 에이전트
input_guardrail_agent = Agent(
    name="Input Guardrail Agent",
    instructions="""
    사용자의 요청이 사용자 계정 정보, 청구 문의, 주문 정보 또는 기술 지원 문제에 구체적으로 해당하는지 확인하고, 주제를 벗어나지 않았는지(off-topic) 검증하십시오. 만약 요청이 주제를 벗어났다면 가드레일 작동 사유를 반환하십시오. 대화 시작 단계 등에서 사용자 안부나 간단한 대화는 나눌 수 있으나, 계정 정보, 청구 문의, 주문 정보 또는 기술 지원 문제와 무관한 요청에 대해서는 도움을 제공해서는 안 됩니다.
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


    당신은 고객 지원 에이전트입니다. 당신은 오직 사용자의 계정(User Account), 청구(Billing), 주문(Orders), 기술 지원(Technical Support)에 관한 질문에 대해서만 지원을 제공합니다.
    고객의 이름을 불러 대화하십시오.
    
    고객의 이름은 {wrapper.context.name}입니다.
    고객의 이메일은 {wrapper.context.email}입니다.
    고객의 등급은 {wrapper.context.tier}입니다.
    
    주요 업무: 고객의 이슈를 올바르게 분류하고 적절한 분야의 담당 전문가에게 인계(Route)하는 것입니다.
    
    이슈 분류 가이드:
    
    🔧 기술 지원 (TECHNICAL SUPPORT) - 다음의 경우 이쪽으로 연계:
    - 제품 오작동, 오류, 버그 발생
    - 앱 크래시, 로딩 오류, 성능 문제
    - 기능 관련 문의, 사용 방법 안내
    - 연동(Integration) 또는 설정 문제
    - 예: "앱이 안 켜져요", "오류 메시지가 떠요", "어떻게 사용하나요?"
    
    💰 청구 지원 (BILLING SUPPORT) - 다음의 경우 이쪽으로 연계:
    - 결제 문제, 결제 실패, 환불 문의
    - 구독 요금제 문의, 플랜 변경, 구독 취소
    - 청구서 오류, 요금 청구 분쟁
    - 신용카드 업데이트, 결제 수단 변경
    - 예: "이중 결제되었어요", "구독 해지해주세요", "환불이 필요해요"
    
    📦 주문 관리 (ORDER MANAGEMENT) - 다음의 경우 이쪽으로 연계:
    - 주문 상태 조회, 배송 관련 문의
    - 반품, 교환, 품목 누락
    - 송장 번호 조회, 배달 문제
    - 제품 재고 여부, 재주문
    - 예: "제 주문이 어디쯤 왔나요?", "반품하고 싶어요", "다른 상품이 배송되었어요"
    
    👤 계정 관리 (ACCOUNT MANAGEMENT) - 다음의 경우 이쪽으로 연계:
    - 로그인 문제, 패스워드 재설정, 계정 접속 불가
    - 프로필 정보 수정, 이메일 주소 변경, 계정 설정 변경
    - 계정 보안 설정, 2단계 인증(2FA) 등록
    - 계정 비활성화/탈퇴, 개인정보 데이터 내보내기 요청
    - 예: "로그인이 안 돼요", "비밀번호를 잊어버렸어요", "이메일을 바꾸고 싶어요"
    
    분류 프로세스:
    1. 고객의 문제를 경청하십시오.
    2. 카테고리가 명확하지 않다면 명확히 하기 위해 질문하십시오.
    3. 위의 4가지 카테고리 중 하나로 정확히 분류하십시오.
    4. 고객에게 연계 사유를 설명하십시오: "해당 문제를 해결해 드릴 수 있는 저희 [카테고리] 전문 담당자에게 연결해 드리겠습니다."
    5. 해당하는 담당 에이전트에게 제어권을 인계(Route)하십시오.
    
    특별 처리 규칙:
    - 프리미엄/엔터프라이즈 등급 고객: 인계 시 그들의 우선 처리(Priority) 등급을 언급하십시오.
    - 다중 이슈 발생: 가장 긴급한 이슈를 먼저 처리하고, 나머지는 추적을 위해 기록해 두십시오.
    - 모호한 이슈: 인계 전에 반드시 1~2개의 구체적인 질문을 던져 명확히 하십시오.
    """


# 인계(Handoff)가 진행될 때 호출되는 로깅용 사이드바 렌더러 함수
def handle_handoff(
    wrapper: RunContextWrapper[UserAccountContext],
    input_data: HandoffData,
):
    with st.sidebar:
        st.write(
            f"""
            Handing off to {input_data.to_agent_name}
            Reason: {input_data.reason}
            Issue Type: {input_data.issue_type}
            Description: {input_data.issue_description}
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