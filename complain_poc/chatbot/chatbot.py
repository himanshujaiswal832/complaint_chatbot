from groq import Groq
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import fitz  
import requests


def load_pdf_chunks(pdf_path, chunk_size=50, chunk_overlap=5):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - chunk_overlap  
    return chunks


def build_vector_index(chunks):
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(chunks)
    dim = embeddings[0].shape[0]
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(embeddings))
    return model, index, chunks


def retrieve_context(query, model, index, chunks, top_k=1):
    query_embedding = model.encode([query])
    distances, indices = index.search(np.array(query_embedding), top_k)
    return "\n".join([chunks[i] for i in indices[0]])


def ask_groq(user_query, context):
    client = Groq()
    messages = [
        {"role": "system", "content": f"You are a helpful assistant. Use the context below to answer the question.\n\nContext:\n{context}"},
        {"role": "user", "content": user_query}
    ]

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  
        messages=messages,
        temperature=0.7,
        max_completion_tokens=1024,
        top_p=1,
        stream=True,
    )

    bot_response = ""
    for chunk in completion:
        bot_response += chunk.choices[0].delta.content or ""
    return bot_response.strip()


def create_complaint(data):
    response = requests.post("http://localhost:5000/complaints", json=data)
    return response.json()


def handle_complaint_filing(user_input, complaint):
    
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
        complaint.clear()  
        return f"Your complaint has been registered with ID: {result['complaint_id']}."

    return None


def handle_complaint_retrieval(user_input):
    if "show details for complaint" in user_input.lower():
        complaint_id = user_input.strip().split()[-1].upper()  
        response = requests.get(f"http://localhost:5000/complaints/{complaint_id}")
        if response.status_code == 200:
            result = response.json()
            return f"""Complaint ID: {result['complaint_id']}
Name: {result['name']}
Phone: {result['phone_number']}
Email: {result['email']}
Details: {result['complaint_details']}
Created At: {result['created_at']}"""
        else:
            return "No complaint found with that ID."
    return None
