import sys
import os
# Add project root to sys.path for Streamlit
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv
import asyncio
import streamlit as st
from openai import OpenAI
from agents import Runner, SQLiteSession, InputGuardrailTripwireTriggered
from restaurant_bot.models import RestaurantContext
from restaurant_bot.agent_definitions import triage_agent

dotenv.load_dotenv()
client = OpenAI()

st.set_page_config(page_title="Restaurant Bot", page_icon="🍴")
st.title("🍴 Restaurant Bot")

# Context for the restaurant
if "restaurant_ctx" not in st.session_state:
    st.session_state["restaurant_ctx"] = RestaurantContext(
        customer_id=1,
        name="정혁", # Default name in Korean
    )

if "session" not in st.session_state:
    st.session_state["session"] = SQLiteSession(
        "restaurant-history",
        "restaurant-bot-memory.db",
    )

if "agent" not in st.session_state:
    st.session_state["agent"] = triage_agent

if "handoff_messages" not in st.session_state:
    st.session_state["handoff_messages"] = []

session = st.session_state["session"]

async def paint_history():
    messages = await session.get_items()
    for message in messages:
        if "role" in message:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    if message["type"] == "message":
                        text = message["content"][0]["text"]
                        st.write(text.replace("$", "\$"))

async def run_agent(message):
    with st.chat_message("ai"):
        text_placeholder = st.empty()
        response = ""
        
        try:
            stream = Runner.run_streamed(
                st.session_state["agent"],
                message,
                session=session,
                context=st.session_state["restaurant_ctx"],
            )

            async for event in stream.stream_events():
                if event.type == "raw_response_event":
                    if event.data.type == "response.output_text.delta":
                        response += event.data.delta
                        text_placeholder.write(response.replace("$", "\$"))

                elif event.type == "agent_updated_stream_event":
                    if st.session_state["agent"].name != event.new_agent.name:
                        # Clear handoff messages from session state to display only new ones
                        if st.session_state["handoff_messages"]:
                            for msg in st.session_state["handoff_messages"]:
                                st.info(f"🔄 {msg}")
                            st.session_state["handoff_messages"] = []
                        
                        # In addition to the session_state messages, show a status indicator
                        st.caption(f"Connected to {event.new_agent.name}")
                        st.session_state["agent"] = event.new_agent
                        
                        # Reset for next agent's output if any
                        text_placeholder = st.empty()
                        response = ""

        except InputGuardrailTripwireTriggered:
            st.error("보안 정책상 처리할 수 없는 요청입니다.")

async def main():
    await paint_history()
    
    if prompt := st.chat_input("레스토랑 봇에게 무엇이든 물어보세요!"):
        with st.chat_message("user"):
            st.write(prompt)
        await run_agent(prompt)

if __name__ == "__main__":
    asyncio.run(main())
