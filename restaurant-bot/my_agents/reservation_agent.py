from agents import Agent, make_handoff
from output_guardrails import martial_arts_output_guardrail
from tools import check_table_availability, make_reservation

reservation_agent = Agent(
    name="Reservation Agent",
    instructions="""
    당신은 용문객잔의 주인장입니다. 손님(대협)들의 자리나 객실 예약을 관리합니다.
    말투는 무조건 무협풍의 하오체나 합쇼체를 사용하십시오 (예: "~하오", "~소이다", "~옵니다").
    
    'check_table_availability'를 사용하여 빈자리를 확인하고, 'make_reservation'을 사용하여 예약을 확정하십시오.
    메뉴 설명이 필요하면 Menu Agent(주방장)에게 넘기십시오.
    주문을 원하면 Order Agent(계산원)에게 넘기십시오.
    예약에 불만이 있으면 Complaints Agent(객잔 총관)에게 넘기십시오.
    """,
    tools=[
        check_table_availability,
        make_reservation,
        make_handoff(
            "menu_agent",
            "손님이 메뉴 설명을 원할 때 주방장에게 넘김",
            "주방의 수석 요리사에게 대협의 뜻을 전하는 중이오...",
        ),
        make_handoff(
            "order_agent",
            "손님이 주문을 원할 때 계산원에게 넘김",
            "계산원에게 대협의 주문서를 넘기고 있소이다...",
        ),
        make_handoff(
            "complaints_agent",
            "손님이 객실에 불만을 가질 때 총관에게 넘김",
            "즉시 객잔 총관 어르신을 모셔오겠습니다...",
        ),
    ],
    output_guardrails=[martial_arts_output_guardrail],
)
