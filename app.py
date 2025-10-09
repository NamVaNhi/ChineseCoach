import streamlit as st
import pandas as pd
import json
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
import base64
import requests
# Cấu hình trang
st.set_page_config(page_title="Trợ lý AI Hán–Việt", layout="centered", page_icon="📘")

# CSS giao diện dark mode + chat
st.markdown("""
    <style>
        body {
            background-color: #0f1117;
            color: #f0f0f0;
        }
        .main-title {
            text-align: center;
            font-size: 36px;
            color: #00c6ff;
            margin-bottom: 20px;
        }
        .response-box {
            background-color: #1c1f26;
            border-left: 5px solid #00c6ff;
            padding: 20px;
            border-radius: 10px;
            margin-top: 20px;
            font-size: 16px;
            color: #f0f0f0;
        }
        .chat-bubble {
            background-color: #1c1f26;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 10px;
            font-size: 16px;
            border-left: 4px solid #00c6ff;
        }
        .footer {
            text-align: center;
            font-size: 12px;
            color: #888;
            margin-top: 40px;
        }
        .stTextInput > div > input {
            background-color: #1c1f26;
            color: #f0f0f0;
            border: 1px solid #444;
        }
        .history-item {
            background-color: #1c1f26;
            padding: 8px;
            border-radius: 6px;
            margin-bottom: 5px;
            color: #00c6ff;
            cursor: pointer;
        }
        .speak-button {
            background-color: #00c6ff;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 14px;
            margin-top: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Tiêu đề
st.markdown("<div class='main-title'>Trợ lý AI Hán–Việt</div>", unsafe_allow_html=True)

# Tải dữ liệu
@st.cache_resource
def load_data():
    df = pd.read_excel("ngu_lieu_nckh.xlsx")
    docs = []
    for _, row in df.iterrows():
        parts = [f"{col}: {row[col]}" for col in df.columns if pd.notna(row[col])]
        docs.append(" | ".join(parts))
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_texts(docs, embeddings)
    return db, docs

db, documents = load_data()

# Gọi Gemini
def generate_answer(context, query):
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=AIzaSyAFZMhrgHbzztNuxTYbaxBUGantk8dq-eQ"
    headers = {'Content-Type': 'application/json'}
    prompt = f"""
Bạn là trợ lý Hán–Việt. Dựa trên dữ liệu sau, hãy giải thích rõ ràng, tự nhiên:

[DỮ LIỆU]:
{context}

[CÂU HỎI]:
{query}

Trả lời theo cấu trúc:
• Mặt chữ
• Nghĩa tiếng Trung
• Từ loại
• Ngữ cảnh
• Từ Hán Việt
• Nghĩa tiếng Việt hiện đại
• Từ loại tiếng Việt
• Ngữ cảnh tiếng Việt
• Ghi chú

Kết thúc bằng một câu trò chuyện nhẹ nhàng.
"""
    data = {"contents": [{"parts": [{"text": prompt}]}]}
    res = requests.post(url, headers=headers, data=json.dumps(data))
    return res.json()['candidates'][0]['content']['parts'][0]['text']

# Phát âm (giả lập bằng Google Translate)
def speak(text):
    # Tạo URL TTS
    url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text}&tl=vi&client=tw-ob"

    # Tải dữ liệu âm thanh
    response = requests.get(url)
    if response.status_code == 200:
        b64 = base64.b64encode(response.content).decode()
        audio_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.components.v1.html(audio_html, height=0)
    else:
        st.warning("Không thể phát âm từ này.")


# Nhập liệu
query = st.text_input(
    "Nhập từ cần tra hoặc trò chuyện...",
    value=st.session_state.get("query_reload", ""),
    key="main_input"
)

# Khởi tạo lịch sử nếu chưa có
if "history" not in st.session_state:
    st.session_state.history = []

# Xử lý truy vấn
if db and documents and query:
    with st.spinner("🔍 Đang tra cứu..."):
        context = None

        # Tìm khớp chính xác
        for doc in documents:
            if query.lower() in doc.lower():
                context = doc
                break

        # Nếu không có khớp chính xác, tìm tương đồng
        if not context:
            results = db.similarity_search(query, k=3)
            relevant = [r.page_content for r in results if query.lower() in r.page_content.lower()]
            if relevant:
                context = "\n\n".join(relevant)

        # Kiểm tra và phản hồi
        if context:
            answer = generate_answer(context, query)
            if query not in st.session_state.history:
                st.session_state.history.append(query)
        else:
            answer = "❌ Không tìm thấy dữ liệu phù hợp trong ngữ liệu. Vui lòng thử từ khác hoặc kiểm tra chính tả."

        # Hiển thị như chat
        st.markdown(f"<div class='chat-bubble'>{answer}</div>", unsafe_allow_html=True)

        # Nút phát âm (chỉ khi có kết quả hợp lệ)
        if "❌" not in answer and st.button("🔊 Phát âm từ", key="speak_button"):
            speak(query)

# Hiển thị lịch sử tra cứu (dùng chỉ số để tránh trùng key)
if st.session_state.history:
    st.markdown("### 📜 Lịch sử tra cứu")
    for i, item in enumerate(st.session_state.history[::-1]):
        if st.button(item, key=f"history_{i}"):
            st.session_state.query_reload = item


# Footer
st.markdown("<div class='footer'>© 2025 NCKH - ChineseCoach</div>", unsafe_allow_html=True)
