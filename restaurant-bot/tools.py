import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import UserAccountContext
import random
from datetime import datetime, timedelta


# =============================================================================
# TECHNICAL SUPPORT TOOLS (기술 지원 에이전트 전용 도구)
# =============================================================================


@function_tool
def run_diagnostic_check(
    context: UserAccountContext, product_name: str, issue_description: str
) -> str:
    """
    고객 제품의 잠재적인 문제를 파악하기 위해 진단 검사를 실행합니다.

    Args:
        product_name: 문제가 발생한 제품명
        issue_description: 발생한 문제 기술
    """
    # 더미 데이터로 진단 결과 시뮬레이션
    diagnostics = [
        "✅ Server connectivity: Normal",
        "✅ API endpoints: Responsive",
        "⚠️  Cache memory: 85% full (recommend clearing)",
        "✅ Database connections: Stable",
        "⚠️  Last update: 7 days ago (update available)",
    ]

    return f"🔍 Diagnostic results for {product_name}:\n" + "\n".join(diagnostics)


@function_tool
def provide_troubleshooting_steps(context: UserAccountContext, issue_type: str) -> str:
    """
    자주 발생하는 문제에 대한 단계별 문제 해결 가이드를 제공합니다.

    Args:
        issue_type: 문제의 유형 (connection, login, performance, crash 등)
    """
    # 문제 유형별 해결 가이드 매핑
    steps_map = {
        "connection": [
            "1. 인터넷 연결 상태를 확인하십시오.",
            "2. 브라우저 캐시 및 쿠키를 삭제하십시오.",
            "3. 브라우저 확장 프로그램을 일시적으로 비활성화해 보십시오.",
            "4. 시크릿(Incognito) 창에서 다시 시도하십시오.",
            "5. 공유기 및 모뎀을 재부팅해 보십시오.",
        ],
        "login": [
            "1. 아이디와 비밀번호가 정확한지 확인하십시오.",
            "2. Caps Lock 키가 눌려있는지 확인하십시오.",
            "3. 브라우저 캐시를 완전히 비우십시오.",
            "4. 필요한 경우 비밀번호 재설정을 진행하십시오.",
            "5. VPN 사용 중이라면 잠시 연결을 끊으십시오.",
        ],
        "performance": [
            "1. 사용하지 않는 브라우저 탭을 닫으십시오.",
            "2. 브라우저 캐시를 지우십시오.",
            "3. 사용 가능한 시스템 메모리(RAM)와 하드 용량을 확인하십시오.",
            "4. 브라우저 버전을 최신으로 업데이트하십시오.",
            "5. 실행 중인 애플리케이션을 다시 시작하십시오.",
        ],
        "crash": [
            "1. 애플리케이션을 최신 버전으로 업데이트하십시오.",
            "2. 프로그램을 재시작하십시오.",
            "3. 권장 시스템 사양을 충족하는지 확인하십시오.",
            "4. 충돌할 수 있는 다른 보안 프로그램을 비활성화해 보십시오.",
            "5. 안전 모드로 프로그램을 실행해 보십시오.",
        ],
    }

    # 적절한 해결책을 찾지 못한 경우의 기본값 정의
    steps = steps_map.get(
        issue_type.lower(),
        [
            "1. 애플리케이션을 종료한 뒤 다시 시작하십시오.",
            "2. 프로그램의 업데이트 정보를 확인하십시오.",
            "3. 상세한 에러 코드와 함께 고객 센터에 문의해 주십시오.",
        ],
    )

    # 챗봇 대화 컨텍스트 상에 문제 해결 지원을 시도했다는 로그를 남김
    context.add_troubleshooting_step(f"Provided {issue_type} troubleshooting steps")
    return f"🛠️ Troubleshooting steps for {issue_type}:\n" + "\n".join(steps)


@function_tool
def escalate_to_engineering(
    context: UserAccountContext, issue_summary: str, priority: str = "medium"
) -> str:
    """
    기술 지원 에이전트가 해결할 수 없는 복잡한 문제를 개발 부서(Engineering)로 전달(에스컬레이션)합니다.

    Args:
        issue_summary: 기술적 문제의 핵심 요약
        priority: 처리 우선순위 (low, medium, high, critical)
    """
    # 더미 티켓 번호 생성
    ticket_id = f"ENG-{random.randint(10000, 99999)}"

    # 고객 등급에 따라 소요 예상 시간 분기 처리 (기본 4시간, 프리미엄 2시간)
    return f"""
🚀 Issue escalated to Engineering Team
📋 Ticket ID: {ticket_id}
⚡ Priority: {priority.upper()}
📝 Summary: {issue_summary}
🕐 Expected response: {2 if context.is_premium_customer() else 4} hours
    """.strip()


# =============================================================================
# BILLING SUPPORT TOOLS (청구 지원 에이전트 전용 도구)
# =============================================================================


@function_tool
def lookup_billing_history(context: UserAccountContext, months_back: int = 6) -> str:
    """
    고객의 청구 및 납부 이력을 조회합니다.

    Args:
        months_back: 조회할 과거 개월 수 (기본값: 6)
    """
    payments = []
    # 요청받은 개월 수만큼의 가짜 결제 내역 생성
    for i in range(months_back):
        date = datetime.now() - timedelta(days=30 * i)
        amount = random.choice([29.99, 49.99, 99.99])
        status = random.choice(["Paid", "Paid", "Paid", "Failed"])
        payments.append(f"• {date.strftime('%b %Y')}: ${amount} - {status}")

    return f"💳 Billing History (Last {months_back} months):\n" + "\n".join(payments)


@function_tool
def process_refund_request(
    context: UserAccountContext, refund_amount: float, reason: str
) -> str:
    """
    결제 건에 대한 환불 처리를 개시합니다.

    Args:
        refund_amount: 환불 요청 금액
        reason: 환불 신청 사유
    """
    # 프리미엄 고객은 결제 처리 소요 일수를 3일로 단축 (일반 고객은 5일)
    processing_days = 3 if context.is_premium_customer() else 5
    refund_id = f"REF-{random.randint(100000, 999999)}"

    return f"""
✅ Refund request processed
🔗 Refund ID: {refund_id}
💰 Amount: ${refund_amount}
📝 Reason: {reason}
⏱️ Processing time: {processing_days} business days
💳 Refund will appear on original payment method
    """.strip()


@function_tool
def update_payment_method(context: UserAccountContext, payment_type: str) -> str:
    """
    사용자가 안전하게 결제 수단을 업데이트할 수 있도록 안내 링크를 이메일로 발송합니다.

    Args:
        payment_type: 업데이트하려는 결제 수단 종류 (credit_card, paypal, bank_transfer)
    """
    return f"""
    💳 Payment method update initiated
    📋 Type: {payment_type.replace('_', ' ').title()}
    🔒 Secure link sent to: {context.email}
    ⏰ Link expires in: 24 hours
    ✅ No interruption to current service
    """.strip()


@function_tool
def apply_billing_credit(
    context: UserAccountContext, credit_amount: float, reason: str
) -> str:
    """
    고객 서비스 보상 혹은 결제 오류 보정용 계정 크레딧(포인트 등)을 지급합니다.

    Args:
        credit_amount: 지급할 크레딧 액수
        reason: 지급 사유
    """
    return f"""
🎁 Account credit applied
💰 Credit amount: ${credit_amount}
📝 Reason: {reason}
⚡ Applied to account: {context.customer_id}
📧 Confirmation sent to: {context.email}
    """.strip()


# =============================================================================
# ORDER MANAGEMENT TOOLS (주문 관리 에이전트 전용 도구)
# =============================================================================


@function_tool
def lookup_order_status(context: UserAccountContext, order_number: str) -> str:
    """
    주문 번호를 바탕으로 배송 진행 상태와 송장 정보를 조회합니다.

    Args:
        order_number: 고객의 주문 번호
    """
    statuses = ["processing", "shipped", "in_transit", "delivered"]
    current_status = random.choice(statuses)

    tracking_number = f"1Z{random.randint(100000, 999999)}"
    estimated_delivery = datetime.now() + timedelta(days=random.randint(1, 5))

    return f"""
📦 Order Status: {order_number}
🏷️ Status: {current_status.title()}
🚚 Tracking: {tracking_number}
📅 Estimated delivery: {estimated_delivery.strftime('%B %d, %Y')}
📍 Shipping to: {context.email}
    """.strip()


@function_tool
def initiate_return_process(
    context: UserAccountContext, order_number: str, return_reason: str, items: str
) -> str:
    """
    구매자가 수령한 상품의 반품 접수를 개시합니다.

    Args:
        order_number: 반품할 주문 번호
        return_reason: 반품 요청 사유
        items: 반품 신청 대상 품목들
    """
    return_id = f"RET-{random.randint(100000, 999999)}"
    # 일반 회원은 5.99달러의 반품 라벨 발급비 청구 (프리미엄 회원은 무료 제공)
    return_label_fee = 0 if context.is_premium_customer() else 5.99

    return f"""
📦 Return initiated
🔗 Return ID: {return_id}
📋 Order: {order_number}
📝 Items: {items}
💰 Return label fee: ${return_label_fee}
📧 Return label sent to: {context.email}
⏰ Return window: 30 days
    """.strip()


@function_tool
def schedule_redelivery(
    context: UserAccountContext, tracking_number: str, preferred_date: str
) -> str:
    """
    배송 실패 건(부재중 등)에 대해 재배송 예약을 신청합니다.

    Args:
        tracking_number: 운송장 번호
        preferred_date: 수령 희망 일자
    """
    return f"""
🚚 Redelivery scheduled
📦 Tracking: {tracking_number}
📅 New delivery date: {preferred_date}
🏠 Address confirmed: {context.email}
📞 Driver will call 30 minutes before delivery
    """.strip()


@function_tool
def expedite_shipping(context: UserAccountContext, order_number: str) -> str:
    """
    주문 배송 속도를 강제로 상향 조정합니다 (프리미엄 고객 전용 기능).

    Args:
        order_number: 배송을 재촉할 주문 번호
    """
    if not context.is_premium_customer():
        return "❌ Expedited shipping upgrade requires Premium membership"

    return f"""
⚡ Shipping expedited
📦 Order: {order_number}
🚀 Upgraded to: Next-day delivery
💰 No additional charge (Premium benefit)
📧 Updated tracking sent to: {context.email}
    """.strip()


# =============================================================================
# ACCOUNT MANAGEMENT TOOLS (계정 관리 에이전트 전용 도구)
# =============================================================================


@function_tool
def reset_user_password(context: UserAccountContext, email: str) -> str:
    """
    비밀번호 변경용 보안 토큰 및 변경 가이드를 이메일로 전송합니다.

    Args:
        email: 인증 및 메일을 전송받을 계정 주소
    """
    reset_token = f"RST-{random.randint(100000, 999999)}"

    return f"""
🔐 Password reset initiated
📧 Reset link sent to: {email}
🔗 Reset token: {reset_token}
⏰ Link expires in: 1 hour
🛡️ For security, link is single-use only
    """.strip()


@function_tool
def enable_two_factor_auth(context: UserAccountContext, method: str = "app") -> str:
    """
    사용자의 계정 보안성 향상을 위해 2단계 OTP 인증 수단 설정을 지원합니다.

    Args:
        method: 2단계 인증 방식 (app, sms, email)
    """
    setup_code = f"2FA-{random.randint(100000, 999999)}"

    return f"""
🔒 Two-Factor Authentication Setup
📱 Method: {method.upper()}
🔑 Setup code: {setup_code}
📧 Instructions sent to: {context.email}
⚡ Enhanced security activated
    """.strip()


@function_tool
def update_account_email(
    context: UserAccountContext, old_email: str, new_email: str
) -> str:
    """
    계정 로그인용 이메일 계정을 업데이트하며, 인증 단계를 가동합니다.

    Args:
        old_email: 기존 이메일 주소
        new_email: 변경할 이메일 주소
    """
    verification_code = f"VER-{random.randint(100000, 999999)}"

    return f"""
📧 Email update requested
📤 From: {old_email}
📥 To: {new_email}
🔐 Verification code: {verification_code}
⏰ Code expires in: 30 minutes
✅ Change will be activated after verification
    """.strip()


@function_tool
def deactivate_account(
    context: UserAccountContext, reason: str, feedback: str = ""
) -> str:
    """
    고객의 계정 탈퇴(비활성화) 접수를 개시합니다.

    Args:
        reason: 계정 삭제 신청 이유
        feedback: 건의 사항 및 피드백
    """
    return f"""
⚠️ Account deactivation initiated
👤 Account: {context.customer_id}
📝 Reason: {reason}
💬 Feedback: {feedback if feedback else 'None provided'}
⏰ Account will be deactivated in 24 hours
🔄 Can be reactivated within 30 days
📧 Confirmation sent to: {context.email}
    """.strip()


@function_tool
def export_account_data(context: UserAccountContext, data_types: str) -> str:
    """
    개인 정보 권리에 근거하여 고객 프로필, 결제 내역, 주문 이력 등의 데이터 내보내기를 생성합니다.

    Args:
        data_types: 내보낼 정보 범위 (profile, orders, billing 등)
    """
    export_id = f"EXP-{random.randint(100000, 999999)}"

    return f"""
📊 Data export requested
🔗 Export ID: {export_id}
📋 Data types: {data_types}
⏱️ Processing time: 2-4 hours
📧 Download link will be sent to: {context.email}
🔒 Link expires in: 7 days
    """.strip()


# =============================================================================
# AGENT ACTIVITY LOGGING HOOKS (에이전트 동작 모니터링 및 로깅 훅)
# =============================================================================

class AgentToolUsageLoggingHooks(AgentHooks):
    """
    에이전트 생명 주기와 도구 호출 시작/종료 이벤트를 관찰하여
    Streamlit 사이드바에 실시간으로 동작 현황을 렌더링하는 모니터링 클래스
    """

    async def on_tool_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
    ):
        # 특정 에이전트가 도구를 호출하기 시작할 때 실행
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** starting tool: `{tool.name}`")

    async def on_tool_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        tool: Tool,
        result: str,
    ):
        # 도구 실행이 종료되어 실행 결과 데이터를 반환받았을 때 실행
        with st.sidebar:
            st.write(f"🔧 **{agent.name}** used tool: `{tool.name}`")
            st.code(result)

    async def on_handoff(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        source: Agent[UserAccountContext],
    ):
        # 작업 제어권이 다른 전문 에이전트로 이동(Handoff)했을 때 실행
        with st.sidebar:
            st.write(f"🔄 Handoff: **{source.name}** → **{agent.name}**")

    async def on_start(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
    ):
        # 해당 에이전트 러너가 동작을 시작할 때 실행
        with st.sidebar:
            st.write(f"🚀 **{agent.name}** activated")

    async def on_end(
        self,
        context: RunContextWrapper[UserAccountContext],
        agent: Agent[UserAccountContext],
        output,
    ):
        # 해당 에이전트 러너의 전체 처리가 종료되었을 때 실행
        with st.sidebar:
            st.write(f"🏁 **{agent.name}** completed")