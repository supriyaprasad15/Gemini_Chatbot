


import os
import streamlit as st
from dotenv import load_dotenv
from google import genai
from PIL import Image

# ---------------- Configuration ----------------

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

st.set_page_config(
    page_title="Gemini AI Chat",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------- Light Theme ----------------

st.markdown(
    """
    <style>
    .stApp {
        background: #f7f9fc;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    .main-title {
        font-size: 2.2rem;
        font-weight: 750;
        color: #202938;
        margin-bottom: 4px;
    }

    .subtitle {
        color: #667085;
        margin-bottom: 24px;
    }

    .welcome-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
    }

    div.stButton > button {
        border-radius: 10px;
        min-height: 40px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- Session State ----------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "pending_image" not in st.session_state:
    st.session_state.pending_image = None

if "image_uploader_key" not in st.session_state:
    st.session_state.image_uploader_key = 0

# ---------------- Sidebar ----------------

with st.sidebar:
    st.markdown("## ✨ Gemini AI")
    st.caption("Your personal AI assistant")
    st.divider()

    if st.button("＋ New Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.pending_image = None
        st.session_state.image_uploader_key += 1
        st.rerun()

    st.markdown("### About")
    st.caption("Ask questions or upload an image.")
    st.divider()
    st.caption("Powered by Google Gemini")

# ---------------- Header ----------------

st.markdown(
    '<div class="main-title">✨ Gemini AI Chat</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Ask anything. Learn something new.</div>',
    unsafe_allow_html=True,
)

# ---------------- API Key ----------------

if not api_key:
    st.error("API key not found. Check your .env file.")
    st.stop()

try:
    client = genai.Client(api_key=api_key)
except Exception as error:
    st.error(f"Could not connect to Gemini: {error}")
    st.stop()

# ---------------- Image Upload ----------------

st.markdown("### 📎 Add an image (optional)")

uploaded_file = st.file_uploader(
    "Choose an image for your next question",
    type=["png", "jpg", "jpeg", "webp"],
    key=f"image_uploader_{st.session_state.image_uploader_key}",
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Image ready for your next question", width=300)

        # Keep the selected image temporarily for the next message only.
        st.session_state.pending_image = image

    except Exception:
        st.error("Unable to read this image. Please upload another one.")
        st.session_state.pending_image = None

# ---------------- Display Chat History ----------------

if not st.session_state.messages:
    st.markdown(
        """
        <div class="welcome-card">
            <h3>👋 Hello! How can I help you?</h3>
            <p>Type a message below, or upload an image first.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("image") is not None:
            st.image(message["image"], caption="Image sent with this message", width=300)

        st.markdown(message["content"])

# ---------------- Chat Input ----------------

question = st.chat_input("Message Gemini...")

if question:
    question = question.strip()

    # Capture the image for THIS message only.
    current_image = st.session_state.pending_image

    # Remove it from pending state immediately so it cannot be reused.
    st.session_state.pending_image = None

    # Reset the uploader so the same image isn't selected for the next question.
    st.session_state.image_uploader_key += 1

    user_message = {
        "role": "user",
        "content": question,
        "image": current_image,
    }

    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(question)
        if current_image is not None:
            st.image(current_image, caption="Image sent with this message", width=300)

    # Send only this question and its attached image to Gemini.
    contents = [question]

    if current_image is not None:
        contents.append(current_image)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=contents,
                )

                answer = response.text or "Gemini returned an empty response."
                st.markdown(answer)

                st.session_state.messages.append(
                    {
                        "role": "assistant",
                        "content": answer,
                        "image": None,
                    }
                )

            except Exception as error:
                st.error(f"Gemini request failed: {error}")

    st.rerun()
