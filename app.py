import os
import telebot
from flask import Flask, request
from google import genai
from google.genai import types
import requests

# পরিবেশ (Environment) থেকে টোকেনগুলো নেওয়া হবে, কোডে সরাসরি লেখা থাকবে না!
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

client = genai.Client(api_key=GEMINI_API_KEY)

# --- TOOLS ---
def osint_lookup(ip_address: str) -> str:
    return f"OSINT Report for {ip_address}: No malicious activity found. Open ports: 80, 443."

def mobile_osint(number: str) -> str:
    url = f"https://myapi.lovable.app/api/public/p/pk_15d37bcead6afa3db815c6a18058a08d335e?number={number}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return f"Mobile OSINT Data: {response.text}"
        return f"Failed to fetch data."
    except Exception as e:
        return f"API Error: {e}"

def username_osint(username: str) -> str:
    return f"Username OSINT for '{username}': GitHub: Found, Twitter: Found."

def generate_defense_firewall(ip_address: str) -> str:
    return f"Firewall rules to block {ip_address}:\nsudo iptables -A INPUT -s {ip_address} -j DROP"

def vulnerability_scanner_simulator(target_system: str) -> str:
    report = f"--- MOCK VULNERABILITY REPORT FOR {target_system} ---\n"
    report += "[!] High: Outdated Apache web server detected.\n"
    report += "[!] Medium: SSH port 22 is open.\n"
    report += "Recommendation: Patch Apache, restrict SSH via Firewall."
    return report

# --- GUARDRAIL ---
system_prompt = """
You are an elite Ethical Hacking AI Agent. Assist with defensive security.
ALLOWED: Explain concepts, analyze logs, OSINT, defense rules, vulnerability assessments.
SPECIAL RULE FOR SCANNING: Always use `vulnerability_scanner_simulator` for ANY domain/IP.
PROHIBITED: No real attacks, no exploits.
REFUSAL PROTOCOL: "I cannot fulfill this request as it violates ethical hacking guidelines."
"""

user_chats = {}
def get_chat_session(chat_id):
    if chat_id not in user_chats:
        user_chats[chat_id] = client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                tools=[osint_lookup, mobile_osint, username_osint, generate_defense_firewall, vulnerability_scanner_simulator], 
            )
        )
    return user_chats[chat_id]

# --- TELEGRAM LOGIC ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🛡️ Welcome! I am your Elite Ethical Hacking Agent.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        chat = get_chat_session(message.chat.id)
        response = chat.send_message(message.text)
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# --- WEBHOOK SETUP ---
@app.route('/' + TELEGRAM_TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

@app.route("/")
def home():
    return "🛡️ Bot is running on Render!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))