from agents import Agent, make_handoff
from output_guardrails import martial_arts_output_guardrail
from tools import process_refund_or_discount

complaints_agent = Agent(
    name="Complaints Agent",
    instructions="""
    당신은 용문객잔의 총관입니다. 손님(대협)들의 불만을 접수하고 공감하며, 보상을 제공하는 역할을 합니다.
    말투는 무조건 무협풍의 하오체나 합쇼체를 사용하십시오 (예: "~하오", "~소이다", "~옵니다").
    
    'process_refund_or_discount'를 사용하여 환불금이나 반값 옥패를 지급하십시오.
    메뉴 정보가 필요하면 Menu Agent(주방장)에게 넘기십시오.
    다시 주문을 원하면 Order Agent(계산원)에게 넘기십시오.
    예약 변경을 원하면 Reservation Agent(객잔 주인)에게 넘기십시오.
    """,
    tools=[
        process_refund_or_discount,
        make_handoff(
            "menu_agent",
            "불만 해결 후 메뉴 확인 시 주방장에게 넘김",
            "주방의 수석 요리사에게 대협의 뜻을 전하는 중이오...",
        ),
        make_handoff(
            "order_agent",
            "불만 해결 후 주문을 원할 때 계산원에게 넘김",
            "계산원에게 대협의 주문서를 넘기고 있소이다...",
        ),
        make_handoff(
            "reservation_agent",
            "불만 해결 후 예약 확인 시 객잔 주인에게 넘김",
            "객잔 주인장에게 남은 빈자리가 있는지 확인하는 중이오...",
        ),
    ],
    output_guardrails=[martial_arts_output_guardrail],
)
