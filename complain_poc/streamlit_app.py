import streamlit as st
import requests
import re
from chatbot.chatbot import ask_groq,load_pdf_chunks,build_vector_index,retrieve_context



PDF_PATH = "data\CustomerFAQ.pdf"  

if "model" not in st.session_state:
    st.session_state.chunks = load_pdf_chunks(PDF_PATH)
    model, index, chunks = build_vector_index(st.session_state.chunks)
    st.session_state.model = model
    st.session_state.index = index
    st.session_state.chunks = chunks


st.title("Complaint Filing Assistant")

if "complaint" not in st.session_state:
    st.session_state.complaint = {
        "name": None,
        "phone_number": None,
        "email": None,
        "complaint_details": None
    }

if "filing_in_progress" not in st.session_state:
    st.session_state.filing_in_progress = False

if "messages" not in st.session_state:
    st.session_state.messages = []


def create_complaint(data):
    response = requests.post("http://localhost:5000/complaints", json=data)
    return response.json()

def get_complaint(complaint_id):
    response = requests.get(f"http://localhost:5000/complaints/{complaint_id}")
    return response.json()


def handle_input(user_input):
    complaint = st.session_state.complaint
    lower_input = user_input.lower()


    id_match = re.search(r"\b[a-f0-9]{8}\b", lower_input)
    if ("get" in lower_input or "show" in lower_input or "details" in lower_input) and id_match:
        complaint_id = id_match.group(0)
        result = get_complaint(complaint_id)
        if "complaint_id" in result:
            return f"""Complaint Details:
**Complaint ID**: {result['complaint_id']}
**Name**: {result['name']}
**Phone**: {result['phone_number']}
**Email**: {result['email']}
**Details**: {result['complaint_details']}
**Created At**: {result['created_at']}"""
        else:
            return "No complaint found with that ID. Please check and try again."

  
    if not st.session_state.filing_in_progress and re.search(r"(file|raise|register|submit).*complaint", lower_input):
        st.session_state.filing_in_progress = True
        return "I'm sorry to hear that. Let's get it sorted. What's your **name**?"

  
    if st.session_state.filing_in_progress:
        if not complaint["name"]:
            complaint["name"] = user_input
            return "Thank you! What is your phone number?"

        elif not complaint["phone_number"]:
            complaint["phone_number"] = user_input
            return "Got it. What is your email address?"

        elif not complaint["email"]:
            complaint["email"] = user_input
            return "Thanks! Could you please describe your complaint?"

        elif not complaint["complaint_details"]:
            complaint["complaint_details"] = user_input
            result = create_complaint(complaint)
            st.session_state.complaint = {
                "name": None,
                "phone_number": None,
                "email": None,
                "complaint_details": None
            }
            st.session_state.filing_in_progress = False
            return f"Your complaint has been registered with ID: **{result['complaint_id']}**."

 
    if "lost" in lower_input and "complaint id" in lower_input:
        return "To recover your Complaint ID, please contact support or provide your registered email and phone (feature coming soon)."

    context = retrieve_context(user_input, st.session_state.model, st.session_state.index, st.session_state.chunks, top_k=3)
    return ask_groq(user_input, context)


user_input = st.chat_input("How can I help you today?")
if user_input:
    st.session_state.messages.append(("user", user_input))
    bot_response = handle_input(user_input)
    st.session_state.messages.append(("bot", bot_response))

for sender, msg in st.session_state.messages:
    with st.chat_message(sender):
        st.markdown(msg)
