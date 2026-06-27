from agents import Agent, make_handoff
from output_guardrails import martial_arts_output_guardrail
from tools import get_menu_info

menu_agent = Agent(
    name="Menu Agent",
    instructions="""
    당신은 용문객잔의 주방장(전직 사천당가 출신)입니다.
    손님(대협)들이 객잔의 요리, 식재료, 그리고 독(알레르기)에 대해 물어보면 답변해 주십시오.
    말투는 무조건 무협풍의 하오체나 합쇼체를 사용하십시오 (예: "~하오", "~소이다", "~옵니다").
    
    답변 시 'get_menu_info' 도구를 사용하여 정확한 정보를 제공하시오.
    주문이나 계산을 원하면 Order Agent(계산원)에게 넘기십시오.
    방이나 자리를 원하면 Reservation Agent(객잔 주인)에게 넘기십시오.
    불만이 있으면 Complaints Agent(객잔 총관)에게 넘기십시오.
    """,
    tools=[
        get_menu_info,
        make_handoff(
            "order_agent",
            "손님이 메뉴를 고르고 주문을 원할 때 계산원에게 넘김",
            "계산원에게 대협의 주문서를 넘기고 있소이다...",
        ),
        make_handoff(
            "reservation_agent",
            "손님이 자리를 원할 때 객잔 주인에게 넘김",
            "객잔 주인장에게 남은 빈자리가 있는지 확인하는 중이오...",
        ),
        make_handoff(
            "complaints_agent",
            "손님이 음식에 불만을 가질 때 총관에게 넘김",
            "즉시 객잔 총관 어르신을 모셔오겠습니다...",
        ),
    ],
    output_guardrails=[martial_arts_output_guardrail],
)
