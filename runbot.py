import os
import threading
import subprocess
import sys
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup

# ================= [ TELEGRAM CONFIGURATION ] =================
API_TOKEN = "8775404946:AAFgmDA_2wOwmZZnC8ZhAiyc9Bv1ucvtAoA"
ADMIN_ID = 7074774446
CHANNEL_LINK = "https://t.me/kyaltaryarsky"
CHANNEL_USERNAME = "@kyaltaryarsky"
# =============================================================

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)

# Run နေသော ဖိုင်များနှင့် ပတ်သက်သည့် အခြေအနေများကို မှတ်ထားရန်
running_processes = {}
file_store = ["bot1bot1.py", "global Trx bot.html"] # ဗီဒီယိုထဲကအတိုင်း နမူနာဖိုင်များ

# --- UptimeRobot အတွက် Web Server ---
@app.route('/')
def home():
    return "🤖 Bot is running 24/7 with all libraries!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- Channel Join စစ်ဆေးခြင်း ---
def check_channel_join(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return False

# --- Main Menu ပြသခြင်း ---
def send_main_menu(chat_id, user_id):
    welcome_text = (
        f"🥳 Welcome!\n"
        f"🆔 Your User ID: {user_id}\n"
        f"ℹ️ Your Status: 🆓 Free User\n"
        f"📁 Files Uploaded: {len(file_store)} / 6\n\n"
        f"🛸 Host & run Python (.py) or HTML (.html) scripts\n"
        f"backgrounds.\n\n"
        f"👇 Use buttons or type commands."
    )
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("📢 Updates Channel")
    markup.add("📤 Upload File", "📁 Check Files")
    
    bot.send_message(chat_id, welcome_text, reply_markup=markup)

# --- Start Command ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    
    if not check_channel_join(user_id):
        markup = InlineKeyboardMarkup(row_width=1)
        btn_join = InlineKeyboardButton("📢 Join Channel 🚀", url=CHANNEL_LINK)
        markup.add(btn_join)
        
        bot.send_message(
            message.chat.id, 
            f"⚠️ ကျွန်ုပ်တို့၏ Channel ကို အောက်ကကလုတ်ကိုနှိပ်ပြီး Join ထားနိုင်ပါတယ်ခင်ဗျာ-", 
            reply_markup=markup
        )
        return

    send_main_menu(message.chat.id, user_id)

# --- Reply Keyboard Buttons ကလစ်နှိပ်မှုများ ---
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    user_id = message.from_user.id
    
    if not check_channel_join(user_id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📢 Join Channel 🚀", url=CHANNEL_LINK))
        bot.send_message(message.chat.id, "⚠️ ကျွန်ုပ်တို့၏ Channel ကို အောက်ကကလုတ်ကိုနှိပ်ပြီး Join ထားနိုင်ပါတယ်ခင်ဗျာ-", reply_markup=markup)
        return

    if message.text == "📁 Check Files":
        handle_back_to_files(message)
        
    elif message.text == "📤 Upload File":
        bot.send_message(message.chat.id, "🕹️ Send your Python ('.py') or HTML ('.html') file.")
        
    elif message.text == "📢 Updates Channel":
        err_msg = (
            f"❌မှားယွင်းနေပါသည်၊ ' .py ' သို့မဟုတ် ' .html ' ဖိုင်များကို\n"
            f"သာ ပို့ပေးရပါမယ်။"
        )
        bot.send_message(message.chat.id, err_msg)

# --- Inline Keyboard Callbacks ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    filename = call.data.replace("view_", "").replace("start_", "").replace("stop_", "").replace("delete_", "")
    
    if call.data.startswith("view_"):
        status = "Running 🟢" if filename in running_processes else "Stopped 🔴"
        
        markup = InlineKeyboardMarkup(row_width=2)
        btn_stop = InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{filename}")
        btn_del = InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{filename}")
        btn_logs = InlineKeyboardButton("📄 View Logs", callback_data=f"logs_{filename}")
        btn_back = InlineKeyboardButton("🔙 Back to Files", callback_data="back_to_files")
        
        markup.add(btn_stop, btn_del)
        markup.add(btn_logs, btn_back)
        
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=f"⚙️ Controls for <b>{filename}</b>:\nStatus: <b>{status}</b>",
            parse_mode='HTML',
            reply_markup=markup
        )
        
    elif call.data.startswith("stop_"):
        if filename in running_processes:
            proc = running_processes[filename]
            proc.terminate()
            del running_processes[filename]
            bot.answer_callback_query(call.id, "🛑 စက်ကို ရပ်တန့်လိုက်ပါပြီ။")
        else:
            bot.answer_callback_query(call.id, "⚠️ စက်သည် ရပ်တန့်ပြီးသားဖြစ်သည်။")
            
        status = "Running 🟢" if filename in running_processes else "Stopped 🔴"
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(InlineKeyboardButton("🛑 Stop", callback_data=f"stop_{filename}"), InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{filename}"))
        markup.add(InlineKeyboardButton("📄 View Logs", callback_data=f"logs_{filename}"), InlineKeyboardButton("🔙 Back to Files", callback_data="back_to_files"))
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"⚙️ Controls for <b>{filename}</b>:\nStatus: <b>{status}</b>", parse_mode='HTML', reply_markup=markup)

    elif call.data.startswith("delete_"):
        if filename in running_processes:
            running_processes[filename].terminate()
            del running_processes[filename]
        if filename in file_store:
            file_store.remove(filename)
            if os.path.exists(filename):
                os.remove(filename)
            
        bot.answer_callback_query(call.id, "🗑️ ဖိုင်ကို ဖျက်လိုက်ပါပြီ။")
        handle_back_to_files(call.message, is_callback=True)

    elif call.data == "back_to_files" or call.data == "check_files_refresh":
        handle_back_to_files(call.message, is_callback=True)

def handle_back_to_files(message, is_callback=False):
    markup = InlineKeyboardMarkup(row_width=1)
    for filename in file_store:
        emoji = "🟢 🐍" if filename in running_processes else "🔴 🐍" if filename.endswith('.py') else "🔴 🌐"
        btn = InlineKeyboardButton(f"{emoji} {filename}", callback_data=f"view_{filename}")
        markup.add(btn)
    markup.add(InlineKeyboardButton("📥 Upload File", callback_data="upload_action"))
    markup.add(InlineKeyboardButton("📁 Check Files", callback_data="check_files_refresh"))
    
    if is_callback:
        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message.message_id,
            text="📁 Your Files:\nClick to manage.",
            reply_markup=markup
        )
    else:
        bot.send_message(message.chat.id, "📁 Your Files:\nClick to manage.", reply_markup=markup)

# --- ဖိုင်လက်ခံခြင်း ---
@bot.message_handler(content_types=['document'])
def handle_docs(message):
    user_id = message.from_user.id
    if not check_channel_join(user_id): return
    
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
            
        bot.reply_to(message, f"✅ {filename} ကို လက်ခံရရှိပါပြီ။ စတင် Run နိုင်ပါပြီ။")
        
        # သက်ဆိုင်ရာ Library တွေအားလုံးကို သုံးပြီး သီးခြား Background Process အဖြစ် Auto Run ပေးခြင်း
        try:
            if filename.endswith('.py'):
                proc = subprocess.Popen([sys.executable, filename])
                running_processes[filename] = proc
        except Exception:
            pass
    else:
        bot.reply_to(message, "❌ ကျေးဇူးပြု၍ .py သို့မဟုတ် .html ဖိုင်များကိုသာ တင်ပေးပါ။")

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_web_server)
    server_thread.daemon = True
    server_thread.start()
    
    print("🤖 Bot is pooling with custom requirements...")
    bot.polling(none_stop=True)
