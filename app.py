import streamlit as st
from google import genai
from dotenv import load_dotenv
import os
#python -m streamlit run app.py
load_dotenv()

st.set_page_config(page_title="Psikorehber", page_icon="🧠")
st.title("🧠 Psikorehber")
st.caption("Bilimsel temelli psikolojik yönlendirme asistanı")

with open("sistem_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read()

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Nasıl hissediyorsun?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    client = genai.Client(api_key=os.getenv("API_KEY"))
    
    history = []
    for msg in st.session_state.messages[:-1]:
        role = "model" if msg["role"] == "assistant" else "user"
        history.append({
            "role": role,
            "parts": [{"text": msg["content"]}]
    })

    chat = client.chats.create(
        model="gemini-2.5-flash",
        config={"system_instruction": SYSTEM_PROMPT},
        history=history
    )

    response = chat.send_message(prompt)
    answer = response.text

    st.session_state.messages.append({"role": "assistant", "content": answer})
    with st.chat_message("assistant"):
        st.markdown(answer)