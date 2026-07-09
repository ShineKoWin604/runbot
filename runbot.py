import os
import threading
import subprocess
from flask import Flask
import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ================= [ TELEGRAM CONFIGURATION ] =================
API_TOKEN = "8775404946:AAFgmDA_2wOwmZZnC8ZhAiyc9Bv1ucvtAoA"
ADMIN_ID = 7074774446
CHANNEL_LINK = "https://t.me/kyaltaryarsky"
CHANNEL_USERNAME = "@kyaltaryarsky"
# =============================================================

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

running_processes = {}
file_store = []  # တင်ထားသော ဖိုင်စာရင်း

# --- 1. UptimeRobot အတွက် Web Server (Flask) ပိုင်း ---
@app.route('/')
def home():
    return "🤖 Bot is running 24/7 successfully!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- 2. Channel Join/Subscribe စစ်ဆေးသည့် လုပ်ဆောင်ချက် ---
def check_channel_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return False

# --- 3. Telegram Bot Commands & Handlers ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    
    if not check_channel_join(user_id):
        markup = telebot.types.InlineKeyboardMarkup()
        btn_join = telebot.types.InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)
        btn_check = telebot.types.InlineKeyboardButton("🔄 Check Join", callback_data="check_status")
        markup.add(btn_join)
        markup.add(btn_check)
        
        bot.send_message(
            message.chat.id, 
            f"❌ ကျွန်ုပ်တို့၏ Channel ကို အောက်က ခလုတ်ကနေ အရင် Join ပေးဖို့ လိုအပ်ပါတယ်ခင်ဗျာ။ Join ပြီးမှ စက်ကို အသုံးပြုနိုင်ပါမည်။", 
            reply_markup=markup
        )
        return

    show_main_menu(message.chat.id, user_id)

def show_main_menu(chat_id, user_id):
    total_files = len(file_store)
    welcome_text = (
        f"👋 Welcome!\n"
        f"🆔 Your Your User ID: <code>{user_id}</code>\n"
        f"ℹ️ Your Status: 🆓 Free User\n"
        f"📁 Files Uploaded: {total_files} / 6\n\n"
        f"🛸 Host & run Python (.py) or HTML (.html) scripts backgrounds.\n\n"
        f"👇 Use buttons or type commands."
    )
    
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🔄 Updates Channel", "📁 Check Files")
    markup.add("📤 Upload File", "⚡ Bot Speed")
    markup.add("📊 Statistics")
    
    bot.send_message(chat_id, welcome_text, parse_mode='HTML', reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_menu_buttons(message):
    user_id = message.from_user.id
    
    if not check_channel_join(user_id):
        bot.reply_to(message, "⚠️ ကျေးဇူးပြု၍ Channel ကို အရင် Join ပါ။")
        return

    if message.text == "📁 Check Files":
        file_store_refresh(message.chat.id)
        
    elif message.text == "📤 Upload File":
        bot.send_message(message.chat.id, "📤 Send your Python (.py) or HTML (.html) file.")
        
    elif message.text == "⚡ Bot Speed":
        bot.send_message(message.chat.id, "⚡ Bot Speed & Status:\n\n⏱️ API Response: 368.10 ms\n🔓 Status: Unlocked")
        
    elif message.text == "📊 Statistics":
        bot.send_message(message.chat.id, f"📊 Bot Statistics:\n\n👥 Total Users: 1\n📁 Total Files: {len(file_store)}\n🟢 Active Bots: {len(running_processes)}")
        
    elif message.text == "🔄 Updates Channel":
        bot.send_message(message.chat.id, f"❌ မှားယွင်းနေပါသည်။ .py သို့မဟုတ် .html ဖိုင်များကိုသာ ပို့ပေးပါမယ်။")

@bot.callback_query_handler(func=lambda call: True)
def handle_callback_queries(call):
    if call.data == "check_status":
        if check_channel_join(call.from_user.id):
            bot.answer_callback_query(call.id, "✅ Join ထားတာ အောင်မြင်ပါတယ်။")
            show_main_menu(call.message.chat.id, call.from_user.id)
        else:
            bot.answer_callback_query(call.id, "❌ Channel မဝင်ရသေးပါ!", show_alert=True)
            
    elif call.data.startswith("manage_"):
        filename = call.data.split("manage_")[1]
        status_text = "Running 🟢" if filename in running_processes else "Stopped 🔴"
        
        markup = telebot.types.InlineKeyboardMarkup(row_width=2)
        btn_start = telebot.types.InlineKeyboardButton("▶️ Start", callback_data=f"start_{filename}")
        btn_stop = telebot.types.InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{filename}")
        btn_del = telebot.types.InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{filename}")
        btn_back = telebot.types.InlineKeyboardButton("🔙 Back to Files", callback_data="back_to_files")
        markup.add(btn_start, btn_stop)
        markup.add(btn_del, btn_back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ Controls for <b>{filename}</b>:\nStatus: <b>{status_text}</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
        
    elif call.data.startswith("start_"):
        filename = call.data.split("start_")[1]
        if filename in running_processes:
            bot.answer_callback_query(call.id, "⚠️ စက်သည် ယခင်ကတည်းက Run လျက်ရှိသည်။", show_alert=True)
            return
            
        if filename.endswith('.py'):
            try:
                proc = subprocess.Popen(['python', filename], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                running_processes[filename] = proc
                bot.answer_callback_query(call.id, "✅ Script စတင် Run ပါပြီ။")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Error: {str(e)}", show_alert=True)
                
        elif filename.endswith('.html'):
            try:
                # Render (Linux Environment) အတွက် Chrome Settings များ ပြင်ဆင်ခြင်း
                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.binary_location = "/usr/bin/google-chrome" # Render Linux Native Chrome
                
                # Chromium Driver ကို Auto Install လုပ်ပြီး ဖွင့်ခြင်း
                driver_path = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                driver = webdriver.Chrome(service=Service(driver_path), options=chrome_options)
                
                file_path = os.path.abspath(filename)
                driver.get(f"file://{file_path}")
                
                running_processes[filename] = driver
                bot.answer_callback_query(call.id, "✅ HTML Script ကို Background တွင် ဖွင့်လိုက်ပါပြီ။")
            except Exception as e:
                bot.answer_callback_query(call.id, f"❌ Browser Error: {str(e)}", show_alert=True)
                
        bot.delete_message(call.message.chat.id, call.message.message_id)
        file_store_refresh(call.message.chat.id)

    elif call.data.startswith("stop_"):
        filename = call.data.split("stop_")[1]
        if filename in running_processes:
            proc = running_processes[filename]
            if filename.endswith('.py'):
                proc.terminate()
            elif filename.endswith('.html'):
                proc.quit()
            del running_processes[filename]
            bot.answer_callback_query(call.id, "🛑 စက်ကို ရပ်တန့်လိုက်ပါပြီ။")
        else:
            bot.answer_callback_query(call.id, "⚠️ စက်သည် ရပ်တန့်ပြီးသား ဖြစ်သည်။")
            
        bot.delete_message(call.message.chat.id, call.message.message_id)
        file_store_refresh(call.message.chat.id)

    elif call.data.startswith("delete_"):
        filename = call.data.split("delete_")[1]
        if filename in running_processes:
            proc = running_processes[filename]
            if filename.endswith('.py'): proc.terminate()
            elif filename.endswith('.html'): proc.quit()
            del running_processes[filename]
            
        if filename in file_store:
            file_store.remove(filename)
            if os.path.exists(filename):
                os.remove(filename)
        bot.answer_callback_query(call.id, "🗑️ ဖိုင်ကို ဖျက်သိမ်းပြီးပါပြီ။")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        file_store_refresh(call.message.chat.id)
        
    elif call.data == "back_to_files":
        bot.delete_message(call.message.chat.id, call.message.message_id)
        file_store_refresh(call.message.chat.id)

def file_store_refresh(chat_id):
    if not file_store:
        bot.send_message(chat_id, "🗂️ Your Files:\nClick to manage:\n\n(တင်ထားသော ဖိုင်မရှိသေးပါ)")
        return
    markup = telebot.types.InlineKeyboardMarkup()
    for filename in file_store:
        status_emoji = "🟢" if filename in running_processes else "🔴"
        btn = telebot.types.InlineKeyboardButton(f"{status_emoji} {filename}", callback_data=f"manage_{filename}")
        markup.add(btn)
    bot.send_message(chat_id, "📂 Your Files:\nClick to manage:", reply_markup=markup)

@bot.message_handler(content_types=['document'])
def handle_incoming_document(message):
    user_id = message.from_user.id
    if not check_channel_join(user_id):
        bot.reply_to(message, "⚠️ ဖိုင်မတင်မီ Channel ကို အရင် Join ပေးပါ။")
        return
        
    filename = message.document.file_name
    if filename.endswith('.py') or filename.endswith('.html'):
        if len(file_store) >= 6:
            bot.reply_to(message, "❌ ဖိုင်အကန့်အသတ် (၆) ခု ပြည့်သွားပါပြီ။")
            return
            
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        with open(filename, 'wb') as f:
            f.write(downloaded_file)
            
        if filename not in file_store:
            file_store.append(filename)
            
        bot.reply_to(message, f"✅ <b>{filename}</b> ကို အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။ '📁 Check Files' ခလုတ်ကို နှိပ်ပြီး စတင် Run နိုင်ပါပြီ။", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ မမှန်ကန်ပါ။ `.py` သို့မဟုတ် `.html` ဖိုင်များကိုသာ လက်ခံပါသည်။")

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🤖 Bot စတင်လည်ပတ်နေပါပြီ...")
    bot.polling(none_stop=True)
