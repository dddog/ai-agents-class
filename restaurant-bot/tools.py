import streamlit as st
from agents import function_tool, AgentHooks, Agent, Tool, RunContextWrapper
from models import UserAccountContext
import random
from datetime import datetime, timedelta

# =============================================================================
# TECHNICAL SUPPORT TOOLS (주방장 / 메뉴 정보 지원 도구)
# =============================================================================

@function_tool
def run_diagnostic_check(
    context: UserAccountContext, product_name: str, issue_description: str
) -> str:
    """
    용문객잔 주방 요리에 문제가 있는지 진단하거나 독(알레르기) 기운을 검사합니다.

    Args:
        product_name: 진단할 요리명 (예: 만두, 마파두부, 홍소육)
        issue_description: 손님이 느끼는 문제 증상 (예: 배가 아픔, 독이 든 것 같음)
    """
    st.write(
        f"🛠️ 주방 요리 진단 비급 작동: {product_name} 요리의 {issue_description} 상태를 살피는 중이오..."
    )

    diagnostics = [
        "진단 결과: 주방장의 비약이 과하게 들어가 일시적으로 혈기가 도는 것이니 안심하시오.",
        "진단 결과: 상한 재료가 섞여 독기가 생겼소. 즉시 음식을 파기하고 보상하겠소.",
        "진단 결과: 특별한 독기는 감지되지 않았으나 위장이 약한 자는 매운 향에 체할 수 있소.",
        "진단 결과: 요리는 아주 온전하오. 내공을 증진하는 기운이 가득 차 있소."
    ]
    return random.choice(diagnostics)


@function_tool
def get_technical_documentation(context: UserAccountContext, product_name: str) -> str:
    """
    용문객잔의 메뉴 정보(요리 비방, 효능, 알레르기)를 조회합니다.

    Args:
        product_name: 조회할 요리명 (만두, 죽엽청, 마파두부, 홍소육, 우육면 중 하나)
    """
    st.write(f"📖 요리 비방 서책 뒤적이는 중: {product_name}")
    docs = {
        "만두": "용문객잔 특제 고기만두. 돼지고기와 비법 향신료가 듬뿍 들어가 기력을 신속히 보충해줍니다. 알레르기(독): 돼지고기.",
        "죽엽청": "대나무 잎으로 빚어 3년 묵힌 맑은 술. 속을 달래주고 막힌 혈을 풀어 혈기를 왕성하게 합니다.",
        "마파두부": "사천의 얼얼한 초피 향이 가득한 요리. 몸 안의 차가운 독을 빼내는 데 좋으나 위장이 약한 자는 피해야 하오. 알레르기(독): 대두.",
        "홍소육": "푹 삶아 기름기를 뺀 돼지고기 장조림. 내공 증진에 도움이 되나 기름기가 많소.",
        "우육면": "소고기 뼈를 하루 낮밤 고아낸 진한 육수의 국수. 알레르기(독): 밀가루."
    }
    return docs.get(
        product_name.lower(),
        f"해당 요리({product_name})는 아직 주방에서 비방이 개발되지 않았소이다. 만두, 죽엽청, 마파두부 등을 물어보시오.",
    )


# =============================================================================
# BILLING SUPPORT TOOLS (객잔 주인 / 예약 및 은냥 보상 도구)
# =============================================================================

@function_tool
def get_billing_history(context: UserAccountContext) -> str:
    """
    손님의 객잔 이용 및 은냥 결제 내역(과거 장부)을 조회합니다.
    """
    st.write(f"💳 {context.name} 대협의 과거 결제 장부를 열어보는 중이오...")
    return f"{context.name} 대협의 장부 기록:\n- 건륭 3년 정월 초하루: 만두와 죽엽청 7냥 (완납)\n- 건륭 3년 이월 보름: 천자호실 하루 투숙 15냥 (완납)\n- 건륭 3년 삼월 그믐: 우육면과 소주 5냥 (완납)"


@function_tool
def issue_refund(context: UserAccountContext, transaction_id: str, amount: float) -> str:
    """
    손님에게 은냥을 보상(환불)하거나 다음 투숙 시 쓸 수 있는 전대를 환수해 줍니다.

    Args:
        transaction_id: 보상 대상이 되는 장부의 거래 ID
        amount: 환불/보상해 줄 은냥의 액수
    """
    st.write(f"💸 장부 ID {transaction_id} 건에 대해 {amount}냥의 은냥 보상을 처리하오...")
    return f"대협의 전대에 은냥 {amount}냥을 성공적으로 돌려드렸소이다."


# =============================================================================
# ACCOUNT MANAGEMENT TOOLS (객잔 총관 / 불만 및 보상 비급 도구)
# =============================================================================

@function_tool
def update_account_address(context: UserAccountContext, new_address: str) -> str:
    """
    예약된 천자호실 또는 지자호실의 위치(방향)를 변경합니다.

    Args:
        new_address: 새로 배정할 방의 방향 (예: 동천자호실, 서지자호실)
    """
    st.write(f"🏠 {context.name} 대협의 예약 호실을 {new_address}로 조정하오...")
    return f"예약하신 호실이 성공적으로 '{new_address}'로 변경되었소이다."


@function_tool
def reset_password(context: UserAccountContext) -> str:
    """
    손님의 불만을 해결하기 위해 특제 '반값 할인 옥패'를 지급하는 절차를 밟습니다.
    """
    st.write(f"🔐 {context.email} 주소로 반값 옥패의 서한을 전하는 전서구를 날렸소...")
    return f"대협의 서한({context.email})으로 반값 옥패 수신 확인서가 발송되었으니 확인해 보시오."


# =============================================================================
# ORDER MANAGEMENT TOOLS (계산원 / 주문 및 화청 도구)
# =============================================================================

@function_tool
def get_order_status(context: UserAccountContext, order_id: str) -> str:
    """
    주문 번호를 바탕으로 주방에서 요리가 조리되는 상태(화청 상태)를 조회합니다.

    Args:
        order_id: 조회할 주문 장부 번호
    """
    st.write(f"📦 장부 번호 {order_id}의 조리 상태를 점검하오...")
    statuses = ["재료 손질 중", "화로에서 익히는 중", "접시에 담는 중", "손님 상으로 서빙 완료"]
    current_status = random.choice(statuses)
    estimated_delivery = (datetime.now() + timedelta(minutes=random.randint(5, 20))).strftime(
        "%H시 %M분"
    )
    return f"장부 번호 {order_id}의 요리 상태: {current_status}. 예상 제공 시간은 대략 {estimated_delivery} 즈음이오."


@function_tool
def cancel_order(context: UserAccountContext, order_id: str) -> str:
    """
    주방에 아직 화청이 들어가기 전(불을 피우기 전)인 요리 주문을 취소합니다.

    Args:
        order_id: 취소할 주문 장부 번호
    """
    st.write(f"❌ 장부 번호 {order_id}의 주문 취소를 주방에 기별하오...")
    return f"주문 장부 {order_id}번에 대한 화청 취소가 완료되었소. 은냥은 그대로 보전되오."