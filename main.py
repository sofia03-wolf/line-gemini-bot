from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
import fitz  # PyMuPDF
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)
load_dotenv()

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_SHEET_CREDENTIAL_JSON = os.getenv("GOOGLE_SHEET_CREDENTIAL_JSON")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-pro")

def read_web_content(url):
    try:
        res = requests.get(url)
        soup = BeautifulSoup(res.content, 'html.parser')
        return soup.get_text().strip()
    except:
        return "❗️ไม่สามารถดึงข้อมูลจากเว็บไซต์ได้"

def read_pdf(path):
    doc = fitz.open(path)
    return "\n".join([page.get_text() for page in doc])

def read_excel(path):
    df = pd.read_excel(path)
    return df.to_string(index=False)

def log_to_sheet(question, answer):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEET_CREDENTIAL_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        sheet.append_row([question, answer])
    except Exception as e:
        print("❗️Log Google Sheets ผิดพลาด:", e)

@app.route("/")
def index():
    return "PSU Pattani Reg Bot ทำงานอยู่แล้ว!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_text = event.message.text.strip()

    if "เวลาเรียน" in user_text:
        reply_text = "คุณสามารถดูตารางเวลาได้ที่: https://regist.pn.psu.ac.th/"
    elif "ข่าว" in user_text:
        reply_text = read_web_content("https://regist.pn.psu.ac.th/main/index.php")
    elif "ไฟล์" in user_text:
        reply_text = read_pdf("บันทึกอุบัติการ-และถอดบทเรียนลงทะเบียนเรียน-Facebook.pdf")
    else:
        try:
            prompt = f"ดิฉันคือบอทแอดมิน ม.พะตง ยินดีช่วยเหลือค่ะ 😊\n\nคำถาม: {user_text}"
            response = model.generate_content(prompt)
            reply_text = response.text.strip()
        except Exception as e:
            reply_text = f"❗️เกิดข้อผิดพลาด: {e}"

    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=reply_text)
    )

    log_to_sheet(user_text, reply_text)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
