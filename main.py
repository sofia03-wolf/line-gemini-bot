from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os
from dotenv import load_dotenv

# โหลด ENV
app = Flask(__name__)
load_dotenv()

# อ่านค่าจาก Environment
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ตั้งค่า Line และ Gemini
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('models/gemini-pro')

# หน้า root
@app.route("/")
def index():
    return "PSU Pattani Reg Bot ทำงานอยู่แล้ว!"

# webhook จาก LINE
@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# ตอบกลับข้อความ
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    prompt = event.message.text
    try:
        response = model.generate_content(prompt)
        reply_text = response.text if response.text else "❗️Gemini ไม่ตอบกลับ"
    except Exception as e:
        reply_text = f"❗️เกิดข้อผิดพลาด: {str(e)}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

# รันแอป
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
