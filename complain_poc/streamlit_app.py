import streamlit as st
import requests
from chatbot.chatbot import get_chatbot_chain
import sys

sys.modules['torch.classes'] = None

st.set_page_config(page_title="RAG Complaint Chatbot")
st.title("Complaint Chatbot")

chatbot = get_chatbot_chain()


if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.complaint_data = {
        "name": "",
        "phone_number": "",
        "email": "",
        "complaint_details": ""
    }
    st.session_state.stage = "init"
    st.session_state.complaint_id = ""


def send_to_api(data):
    response = requests.post("http://127.0.0.1:5000/complaints", json=data)
    return response.json() if response.status_code == 200 else {"error": "Failed to create complaint."}

def get_complaint_by_id(cid):
    response = requests.get(f"http://127.0.0.1:5000/complaints/{cid}")
    return response.json() if response.status_code == 200 else None

def bot_say(message):
    st.session_state.chat_history.append(("bot", message))
    st.write(f"**Bot:** {message}")

def user_say(message):
    st.session_state.chat_history.append(("user", message))
    st.write(f"**You:** {message}")


for role, msg in st.session_state.chat_history:
    st.write(f"**{'Bot' if role == 'bot' else 'You'}:** {msg}")


if st.button("Raise a Complaint"):
    st.session_state.stage = "collect_name"
    bot_say("Sure! Let's raise a complaint. Please enter your full name:")

if st.button("Fetch Complaint Details"):
    st.session_state.stage = "fetch"

if st.button("FAQ"):
    st.session_state.stage = "faq"
    bot_say("Great! What FAQ question can I help you with?")

if st.session_state.stage == "fetch":
    complaint_id_input = st.text_input("Enter Complaint ID:", key="complaint_id_input")
    if complaint_id_input:
        data = get_complaint_by_id(complaint_id_input.strip())
        if data:
            bot_say(f"""Complaint ID: {data['complaint_id']}
Name: {data['name']}
Phone: {data['phone_number']}
Email: {data['email']}
Details: {data['complaint_details']}
Created At: {data['created_at']}""")
        else:
            bot_say("Sorry, no complaint found with that ID.")
        st.session_state.stage = "init"


user_input = st.text_input("Your input:", key="user_input")

if user_input:
    user_say(user_input)
    stage = st.session_state.stage

    if stage == "collect_name":
        st.session_state.complaint_data["name"] = user_input.strip()
        bot_say("Thanks. Now, your phone number?")
        st.session_state.stage = "collect_phone"

    elif stage == "collect_phone":
        st.session_state.complaint_data["phone_number"] = user_input.strip()
        bot_say("Great. Please provide your email address.")
        st.session_state.stage = "collect_email"

    elif stage == "collect_email":
        st.session_state.complaint_data["email"] = user_input.strip()
        bot_say("Got it. Lastly, describe your complaint.")
        st.session_state.stage = "collect_details"

    elif stage == "collect_details":
        st.session_state.complaint_data["complaint_details"] = user_input.strip()
        bot_say("Submitting your complaint...")
        result = send_to_api(st.session_state.complaint_data)
        if "complaint_id" in result:
            cid = result["complaint_id"]
            st.session_state.complaint_id = cid
            bot_say(f"Your complaint has been registered with ID: {cid}.")
        else:
            bot_say("There was an error submitting your complaint.")
        st.session_state.stage = "init"

    elif stage == "faq" or stage == "faq_continue":
        if user_input.lower().strip() in ["exit", "main menu", "no"]:
            bot_say("Returning to main menu.")
            st.session_state.stage = "init"
        else:
            prompt = (
                f"You are a helpful customer support assistant. "
                f"Answer the following frequently asked question clearly and concisely:\n\n"
                f"Question: {user_input}"
            )
            answer = chatbot.run(prompt)
            bot_say(answer)
            bot_say("Would you like to ask another FAQ? Type 'exit' to return to the main menu.")
            st.session_state.stage = "faq_continue"
