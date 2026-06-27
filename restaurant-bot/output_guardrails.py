from agents import (
    Agent,
    output_guardrail,
    Runner,
    RunContextWrapper,
    GuardrailFunctionOutput,
)
from models import TechnicalOutputGuardRailOutput, UserAccountContext

# 기술 지원 응답 내용을 사후 검증(Output Guardrail)하기 위한 분석 에이전트 정의
technical_output_guardrail_agent = Agent(
    name="Technical Support Guardrail",
    instructions="""
    기술 지원 응답이 다음 항목을 부적절하게 포함하고 있는지 분석하여 확인하십시오:
    
    - 청구 정보 (결제, 환불, 비용 청구, 구독 등)
    - 주문 정보 (배송, 운송장 추적, 배달, 반품 등)
    - 계정 관리 정보 (비밀번호 변경, 이메일 주소 변경, 계정 설정 등)
    
    기술 지원 에이전트는 오직 기술적 트러블슈팅, 진단 및 제품 지원만 제공해야 합니다.
    기술 지원 응답으로 부적절한 콘텐츠가 포함된 필드는 True를 반환하십시오.
    """,
    output_type=TechnicalOutputGuardRailOutput,  # 결과 판정 정보를 분석하여 Pydantic 모델로 변환
)


# 기술 지원 전문 에이전트의 출력이 완성된 후 트리거되는 비동기 출력 가드레일 데코레이터 함수
@output_guardrail
async def technical_output_guardrail(
    wrapper: RunContextWrapper[UserAccountContext],
    agent: Agent,
    output: str,  # 완성된 에이전트 응답 텍스트
):
    # 가드레일 전용 분석 에이전트를 가동해 응답 적절성 검사 수행
    result = await Runner.run(
        technical_output_guardrail_agent,
        output,
        context=wrapper.context,
    )

    validation = result.final_output

    # 주제 이탈(off_topic)이거나, 청구 정보, 혹은 계정 정보 오염이 감지될 경우 트리거 상태로 판단
    triggered = (
        validation.contains_off_topic
        or validation.contains_billing_data
        or validation.contains_account_data
    )

    # 검증 결과 및 차단(tripwire) 발동 여부 반환
    return GuardrailFunctionOutput(
        output_info=validation,
        tripwire_triggered=triggered,
    )