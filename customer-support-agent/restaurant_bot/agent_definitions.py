from agents import Agent, RunContextWrapper, handoff
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from agents.extensions import handoff_filters
from restaurant_bot.models import RestaurantContext, HandoffData
from restaurant_bot.guardrails import restaurant_input_guardrail, restaurant_output_guardrail
import streamlit as st

# Helper for handoff with UI notification
def handle_handoff(wrapper: RunContextWrapper[RestaurantContext], input_data: HandoffData):
    # This will be displayed in the UI during the run_agent loop in app.py
    # We can use st.session_state to store the handoff message
    handoff_msg = f"Connecting to {input_data.to_agent_name} Specialist... (Reason: {input_data.reason})"
    if "handoff_messages" not in st.session_state:
        st.session_state["handoff_messages"] = []
    st.session_state["handoff_messages"].append(handoff_msg)

def make_handoff(agent):
    return handoff(
        agent=agent,
        on_handoff=handle_handoff,
        input_type=HandoffData,
        input_filter=handoff_filters.remove_all_tools,
    )

# 1. Menu Agent
menu_agent = Agent(
    name="Menu Agent",
    instructions="""
    You are a Menu Specialist at our restaurant. 
    Your job is to answer questions about:
    - Menu items and prices
    - Ingredients and food preparation
    - Allergies and dietary restrictions (vegan, gluten-free, etc.)
    
    Current featured items:
    - Margherita Pizza: Fresh basil, mozzarella, tomato sauce ($15)
    - Truffle Pasta: Homemade pasta with black truffle cream sauce ($22)
    - Caesar Salad: Romaine lettuce, croutons, parmesan, house dressing ($12) - Vegetarian option available
    - Vegan Burger: Plant-based patty, vegan cheese, avocado ($18)
    
    Be polite and helpful. If the user wants to order or make a reservation, tell them you'll hand them off to the right specialist.
    """,
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)

# 2. Order Agent
order_agent = Agent(
    name="Order Agent",
    instructions="""
    You are an Order Specialist. Your job is to take and confirm customer orders.
    Process:
    1. Ask what they would like to order.
    2. Confirm the items and provide the total price.
    3. Ask if they want it for takeout or delivery.
    4. Confirm the order is placed.
    
    If the user asks about ingredients or menu details, hand them back to the Menu Specialist.
    If they want a reservation, hand them to the Reservation Specialist.
    """,
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)

# 3. Reservation Agent
reservation_agent = Agent(
    name="Reservation Agent",
    instructions="""
    You are a Reservation Specialist. Your job is to handle table bookings.
    Process:
    1. Ask for the number of people.
    2. Ask for the date and time.
    3. Ask for a contact name and phone number.
    4. Confirm the reservation.
    
    If the user asks about the menu, hand them to the Menu Specialist.
    """,
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)

# 3.5 Complaints Agent
complaints_agent = Agent(
    name="Complaints Agent",
    instructions="""
    You are a Complaints Specialist at our restaurant.
    Your job is to handle customer complaints and resolve their issues with empathy, care, and professionalism.
    
    Guidelines:
    1. Acknowledge and empathize with the customer's complaint or dissatisfaction first.
    2. Propose concrete solutions:
       - Refund (환불)
       - 50% discount on their next visit (다음 방문 시 50% 할인 제공)
       - Manager callback (매니저가 직접 연락하여 해결하도록 함)
    3. Escalate severe issues appropriately.
    
    Always maintain a professional, polite, and caring tone. Speak in the customer's preferred language (Korean).
    """,
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
)

# 4. Triage Agent
def triage_instructions(wrapper: RunContextWrapper[RestaurantContext], agent: Agent[RestaurantContext]):
    return f"""
    {RECOMMENDED_PROMPT_PREFIX}
    
    You are the Triage Agent for our restaurant. Your job is to identify what the customer wants and route them to the correct specialist.
    Customer Name: {wrapper.context.name}
    
    Specialists:
    - Menu Agent: For menu questions, ingredients, allergies.
    - Order Agent: To place an order or check order status.
    - Reservation Agent: To book a table.
    - Complaints Agent: For customer complaints, bad experiences, or food/service issues.
    
    Always address the customer by their name. 
    Before handing off, briefly explain that you are connecting them to a specialist.
    """

triage_agent = Agent(
    name="Triage Agent",
    instructions=triage_instructions,
    input_guardrails=[restaurant_input_guardrail],
    output_guardrails=[restaurant_output_guardrail],
    handoffs=[
        make_handoff(menu_agent),
        make_handoff(order_agent),
        make_handoff(reservation_agent),
        make_handoff(complaints_agent),
    ],
)

