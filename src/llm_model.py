import os
import ssl

import httpx
import streamlit as st
from dotenv import load_dotenv
from google import genai

ssl._create_default_https_context = ssl._create_unverified_context
# Khởi tạo đối tượng GeminiAI với API key của bạn
load_dotenv()

client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}


def analysis_with_ai(df, prompt):
    if st.button("Phân tích dữ liệu với AI"):
        prompt = f"Đóng vai trò là một chuyên viên phân tích tài chính. Tôi sẽ cung cấp bảng dữ liệu dưới dạng bảng Markdown. Hãy đọc, xử lý và phân tích dữ liệu đó, cung cấp các nhận định về tình hình tài chính hoặc xu hướng dựa trên số liệu trong bảng trả lời dưới dạng bảng markdown. {prompt}.Dữ liệu chi tiết:  {df.to_string()} "
        res = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
        return res.text
