import telebot
import subprocess
import os
import shutil
import threading
import time
from telebot import types

# إعدادات البوت
TOKEN = '7586425607:AAGd-m0dXMkUCmES6-csL9anaGGGMN0ZOY4'
OWNER_ID = 7661505696  
bot = telebot.TeleBot(TOKEN)
uploaded_files_dir = 'uploaded_bots'
users_file = 'users.txt'  # ملف لتخزين المستخدمين

# إنشاء المجلد إذا لم يكن موجودًا
if not os.path.exists(uploaded_files_dir):
    os.makedirs(uploaded_files_dir)

# تحميل قائمة المستخدمين من الملف
def load_users():
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            return set(line.strip() for line in f)
    return set()

# حفظ قائمة المستخدمين إلى الملف
def save_users(users):
    with open(users_file, 'w') as f:
        for user in users:
            f.write(f"{user}\n")

running_bots = {}  
stopped_bots = set()  
deleted_bots = set()  
users = load_users()  # تحميل المستخدمين عند بدء البوت

# دالة تشغيل البوت
def run_script(script_path, chat_id, folder_name):
    if folder_name in stopped_bots or folder_name in deleted_bots:
        return  

    bot.send_message(chat_id, f"🚀 جاري تشغيل البوت {folder_name}...")
    
    process = subprocess.Popen(['python3', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    running_bots[folder_name] = {'process': process, 'script_path': script_path, 'chat_id': chat_id}
    
    bot.send_message(chat_id, f"✅ تم تشغيل البوت {folder_name} بنجاح!")

# دالة إيقاف البوت يدويًا
def stop_running_bot(folder_name, chat_id):
    if folder_name in running_bots:
        running_bots[folder_name]['process'].terminate()
        del running_bots[folder_name]  
        stopped_bots.add(folder_name)  
        bot.send_message(chat_id, f"🔴 تم إيقاف البوت {folder_name}.")

# دالة إعادة تشغيل البوت
def restart_running_bot(folder_name, chat_id):
    if folder_name in deleted_bots:
        bot.send_message(chat_id, f"⚠️ البوت {folder_name} غير موجود. لا يمكن إعادة تشغيله.")
        return

    if folder_name in stopped_bots:
        stopped_bots.remove(folder_name)  

    if folder_name not in running_bots:  
        folder_path = os.path.join(uploaded_files_dir, folder_name)
        if os.path.exists(folder_path):
            py_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
            if py_files:
                script_path = os.path.join(folder_path, py_files[0])  
                run_script(script_path, chat_id, folder_name)
            else:
                bot.send_message(chat_id, f"⚠️ لم يتم العثور على أي ملف .py داخل {folder_name}.")
        else:
            bot.send_message(chat_id, f"⚠️ مجلد البوت {folder_name} غير موجود.")
    else:
        bot.send_message(chat_id, f"⚠️ البوت {folder_name} قيد التشغيل بالفعل.")

# دالة حذف البوت
def delete_uploaded_file(folder_name, chat_id):
    if folder_name in running_bots:
        stop_running_bot(folder_name, chat_id)

    folder_path = os.path.join(uploaded_files_dir, folder_name)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
        deleted_bots.add(folder_name)  
        if folder_name in running_bots:
            del running_bots[folder_name]  
        bot.send_message(chat_id, f"🗑️ تم حذف البوت {folder_name} بالكامل.")
    else:
        bot.send_message(chat_id, "⚠️ الملفات غير موجودة.")

    # تأكد من إزالة اسم المجلد من stopped_bots أيضًا
    stopped_bots.discard(folder_name)

# مراقبة وإعادة تشغيل البوتات المتوقفة بسبب خطأ فقط
def monitor_bots():
    while True:
        for folder_name, bot_data in list(running_bots.items()):
            process = bot_data['process']
            if process.poll() is not None and folder_name not in stopped_bots:  
                chat_id = bot_data['chat_id']
                bot.send_message(chat_id, f"⚠️ بوت {folder_name} توقف بسبب خطأ. جارٍ إعادة تشغيله...")
                run_script(bot_data['script_path'], chat_id, folder_name)
        time.sleep(10)

monitor_thread = threading.Thread(target=monitor_bots, daemon=True)
monitor_thread.start()

# أوامر التحكم
@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in users:
        bot.send_message(message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    markup = types.InlineKeyboardMarkup()
    upload_button = types.InlineKeyboardButton('📤 رفع ملف بوت', callback_data='upload')
    list_bots_button = types.InlineKeyboardButton('📜 قائمة البوتات', callback_data='list_bots')
    markup.add(upload_button, list_bots_button)

    if message.from_user.id == OWNER_ID:
        manage_users_button = types.InlineKeyboardButton('👥 إدارة المستخدمين', callback_data='manage_users')
        markup.add(manage_users_button)

    bot.send_message(message.chat.id, "مرحبا بك في استضافة بوتات  لرفع ملفات استخدم ازرار ادناه", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'manage_users')
def manage_users(call):
    if call.from_user.id != OWNER_ID:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return

    markup = types.InlineKeyboardMarkup()
    add_user_button = types.InlineKeyboardButton('➕ إضافة مستخدم', callback_data='add_user')
    remove_user_button = types.InlineKeyboardButton('➖ حذف مستخدم', callback_data='remove_user')
    list_users_button = types.InlineKeyboardButton('📜 رؤية قائمة المستخدمين', callback_data='list_users')
    markup.add(add_user_button, remove_user_button, list_users_button)

    bot.send_message(call.message.chat.id, "اختر ما تريد القيام به:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == 'add_user')
def ask_user_id_to_add(call):
    if call.from_user.id != OWNER_ID:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    bot.send_message(call.message.chat.id, "📥 أرسل معرف المستخدم (ID) الذي تريد إضافته.")

@bot.message_handler(func=lambda message: message.from_user.id == OWNER_ID and message.text.isdigit())
def add_user(message):
    user_id = int(message.text)
    if user_id not in users:
        users.add(user_id)
        save_users(users)
        bot.send_message(message.chat.id, f"✅ تم إضافة المستخدم {user_id} بنجاح!")
    else:
        bot.send_message(message.chat.id, "⚠️ المستخدم موجود بالفعل.")

@bot.callback_query_handler(func=lambda call: call.data == 'remove_user')
def ask_user_id_to_remove(call):
    if call.from_user.id != OWNER_ID:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    bot.send_message(call.message.chat.id, "📤 أرسل معرف المستخدم (ID) الذي تريد حذفه.")

@bot.message_handler(func=lambda message: message.from_user.id == OWNER_ID and message.text.isdigit())
def manage_user(message):
    user_id = int(message.text)

    # التحقق مما إذا كانت الرسالة تتعلق بإضافة أو حذف مستخدم
    if message.reply_to_message and message.reply_to_message.text.startswith("📥 أرسل معرف المستخدم (ID) الذي تريد إضافته"):
        # إضافة مستخدم
        if user_id not in users:
            users.add(user_id)
            save_users(users)
            bot.send_message(message.chat.id, f"✅ تم إضافة المستخدم {user_id} بنجاح!")
        else:
            bot.send_message(message.chat.id, "⚠️ المستخدم موجود بالفعل.")

    elif message.reply_to_message and message.reply_to_message.text.startswith("📤 أرسل معرف المستخدم (ID) الذي تريد حذفه"):
        # حذف مستخدم
        if user_id in users:
            users.remove(user_id)
            save_users(users)
            bot.send_message(message.chat.id, f"🗑️ تم حذف المستخدم {user_id} بنجاح!")
        else:
            bot.send_message(message.chat.id, "⚠️ المستخدم غير موجود.")

@bot.callback_query_handler(func=lambda call: call.data == 'list_users')
def list_users(call):
    if call.from_user.id != OWNER_ID:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    if not users:
        bot.send_message(call.message.chat.id, "❌ لا توجد مستخدمين مضافين.")
        return

    user_list = "\n".join(map(str, users))
    bot.send_message(call.message.chat.id, f"📜 قائمة المستخدمين:\n{user_list}")

@bot.callback_query_handler(func=lambda call: call.data == 'upload')
def ask_to_upload_file(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in users:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    bot.send_message(call.message.chat.id, "📄 أرسل ملف البوت الذي تريد رفعه (zip أو .py)")

@bot.message_handler(content_types=['document'])
def handle_file(message):
    if message.from_user.id != OWNER_ID and message.from_user.id not in users:
        bot.send_message(message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    try:
        file_id = message.document.file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = message.document.file_name

        folder_name = file_name.replace('.zip', '').replace('.py', '')
        folder_path = os.path.join(uploaded_files_dir, folder_name)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # إزالة اسم المجلد من قائمة المحذوفات
        if folder_name in deleted_bots:
            deleted_bots.remove(folder_name)

        if file_name.endswith('.zip'):
            shutil.unpack_archive(file_path, folder_path)
            os.remove(file_path)

            py_files = [f for f in os.listdir(folder_path) if f.endswith('.py')]
            if py_files:
                run_script(os.path.join(folder_path, py_files[0]), message.chat.id, folder_name)
            else:
                bot.send_message(message.chat.id, "⚠️ لم يتم العثور على أي ملف .py.")

        elif file_name.endswith('.py'):
            run_script(file_path, message.chat.id, folder_name)

        else:
            bot.send_message(message.chat.id, "⚠️ فقط ملفات .py أو zip مدعومة.")

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")

@bot.callback_query_handler(func=lambda call: call.data == 'list_bots')
def list_running_bots(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in users:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return
    
    if not running_bots:
        bot.send_message(call.message.chat.id, "❌ لا توجد بوتات قيد التشغيل.")
        return

    markup = types.InlineKeyboardMarkup()
    for folder_name in running_bots:
        control_buttons = [
            types.InlineKeyboardButton(f"🔴 إيقاف {folder_name}", callback_data=f'stop_{folder_name}'),
            types.InlineKeyboardButton(f"♻️ إعادة تشغيل {folder_name}", callback_data=f'restart_{folder_name}'),
            types.InlineKeyboardButton(f"🗑️ حذف {folder_name}", callback_data=f'delete_{folder_name}')
        ]
        markup.add(*control_buttons)

    bot.send_message(call.message.chat.id, "📜 قائمة البوتات:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith(('stop_', 'restart_', 'delete_')))
def handle_bot_controls(call):
    if call.from_user.id != OWNER_ID and call.from_user.id not in users:
        bot.send_message(call.message.chat.id, "🚫 لا تملك إذن استخدام البوت.")
        return

    action, folder_name = call.data.split('_', 1)
    chat_id = call.message.chat.id

    if action == 'stop':
        stop_running_bot(folder_name, chat_id)
    elif action == 'restart':
        restart_running_bot(folder_name, chat_id)
    elif action == 'delete':
        delete_uploaded_file(folder_name, chat_id)

bot.infinity_polling()