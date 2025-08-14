import telebot
from telebot import types
from tokens import TELEGRAM_BOT_TOKEN 
import os
import json
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

user_story_maker_data = {}
DATA_FILE = 'tasks.json'


#Маркапы клавиатур:

def main_menu_markup():
        keyboard = types.InlineKeyboardMarkup() #определяем какой вид клавиатуры испльзовать
        calculator_button = types.InlineKeyboardButton(text='🧮 Калькулятор', callback_data='calculator') 
        keyboard.add(calculator_button) #добавляем кнопку в клавиатуру
        repeater_button= types.InlineKeyboardButton(text='🔁 Повторялка', callback_data='repeater')
        keyboard.add(repeater_button)
        story_maker_button = types.InlineKeyboardButton(text='📖 Сочинялка историй', callback_data='story_maker')
        keyboard.add(story_maker_button) 
        notes_button = types.InlineKeyboardButton(text="📜 Заметки", callback_data="notes")
        keyboard.add(notes_button)
        return keyboard


def notes_markup():
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("➕ Добавить задачу", callback_data="add_note")
            markup.add(btn1)
            btn2 = types.InlineKeyboardButton("📝 Посмотреть список задач", callback_data="note_list")
            markup.add(btn2)
            btn3 = types.InlineKeyboardButton("❌ Удалить задачу", callback_data="delete_note")
            markup.add(btn3)
            btn4 = types.InlineKeyboardButton("✅ Отметить выполнение задачи", callback_data="complete_note")
            markup.add(btn4)
            btn5 = types.InlineKeyboardButton("↩ Вернуться в меню", callback_data="back_to_menu")
            markup.add(btn5)
            return markup

@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    if message.text.lower() == "/start":
        choose_modules(message)
    else:
        bot.send_message(message.chat.id, "Ты чё несешь мабой, напиши '/start'")

def choose_modules(message):
        bot.send_message(message.from_user.id, text='Выбери модуль который тебя интересует:', reply_markup=main_menu_markup())


@bot.callback_query_handler(func=lambda call: True) #Обработка нажатия кнопок
def callback_worker(call):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    if call.data == "calculator": 
        msg = bot.send_message(call.message.chat.id, "Введите первое число:")
        bot.register_next_step_handler(msg, get_first_operand)
    elif call.data == "repeater":       
        bot.send_message(call.message.chat.id, "Напиши 'стоп' чтобы остановить цикл")
        msg = bot.send_message(call.message.chat.id, "Напиши что тебе повторить (текст, гифка, фото и т.п)")
        bot.register_next_step_handler(msg, repeat)
    elif call.data == "story_maker":
        msg = bot.send_message(call.message.chat.id, "Напиши имя персонажа")
        bot.register_next_step_handler(msg, story_maker)
        user_story_maker_data[msg.chat.id] = {"step": "name"}
    elif call.data == "notes":
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Для управления заметками используйте команды ниже:",
                reply_markup=notes_markup())
    elif call.data == "back_to_menu":
                bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text="Выбери модуль который тебя интересует:'",
                reply_markup=main_menu_markup())
    elif call.data == "add_note":
            msg = bot.send_message(call.message.chat.id, "Введите текст новой задачи:")
            bot.register_next_step_handler(msg, process_add_step)
    elif call.data == "note_list":
        user_tasks = get_user_tasks(call.message.chat.id)
    
        if not user_tasks:
            bot.send_message(call.message.chat.id, "У вас пока нет задач.")
            return
        
        tasks_text = "Ваши задачи:\n"
        for task in user_tasks:
            status = "✅" if task["completed"] else "❌"
            tasks_text += f"{task['id']}. {task['task']} {status}\n"
        
        
        bot.send_message(call.message.chat.id, tasks_text)
    elif call.data == "delete_note":
        user_tasks = get_user_tasks(call.message.chat.id)

        if not user_tasks:
            bot.send_message(call.message.chat.id, "У вас пока нет задач для удаления.")
            return
        
        markup = types.InlineKeyboardMarkup()
        for task in user_tasks:
            markup.add(types.InlineKeyboardButton(
                text=f"{task['id']}. {task['task']}",
                callback_data=f"delete_{task['id']}"
            ))
        
        bot.send_message(
            call.message.chat.id,
            "Выберите задачу для удаления:",
            reply_markup=markup
        )
    elif call.data.startswith("delete_"):
            task_id = int(call.data.split('_')[1])
            delete_user_task(call.message.chat.id, task_id)
            bot.send_message(call.message.chat.id, f"Задача #{task_id} удалена.")
            # Удаляем inline-клавиатуру после выбора
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=None
            )
    elif call.data == "complete_note":
             user_tasks = get_user_tasks(call.message.chat.id)


             incomplete_tasks = [task for task in user_tasks if not task["completed"]]
            
             if not incomplete_tasks:
                 bot.send_message(call.message.chat.id, "У вас нет невыполненных задач.")
                 return
            
             markup = types.InlineKeyboardMarkup()
             for task in incomplete_tasks:
                 markup.add(types.InlineKeyboardButton(
                     text=f"{task['id']}. {task['task']}",
                     callback_data=f"complete_{task['id']}"
                 ))
            
             bot.send_message(
                 call.message.chat.id,
                 "Выберите задачу для отметки как выполненную:",
                 reply_markup=markup
             )
    elif call.data.startswith("complete_"):
         task_id = int(call.data.split('_')[1])
         update_user_task(call.message.chat.id, task_id, completed=True)
         bot.send_message(call.message.chat.id, f"Задача #{task_id} отмечена как выполненная!")
         # Удаляем inline-клавиатуру после выбора
         bot.edit_message_reply_markup(
             chat_id=call.message.chat.id,
             message_id=call.message.message_id,
             reply_markup=None
         )





##########Функции

def get_first_operand(message):
    try:
        operand_1 = float(message.text)
        msg = bot.send_message(message.chat.id, "Введите второе число:")
        bot.register_next_step_handler(msg, lambda message: get_second_operand(message, operand_1))
    except:
        msg = bot.send_message(message.chat.id, "Цифрами пожалуйста")
        bot.register_next_step_handler(msg, get_first_operand)
    
def get_second_operand(message, operand_1):
    try:
        operand_2 = float(message.text)
        msg = bot.send_message(message.chat.id, "Введите оператор( *, /, +, - ):")
        bot.register_next_step_handler(msg, lambda message: calculate_result(message, operand_1, operand_2))
    except:
        msg = bot.send_message(message.chat.id, "Цифрами пожалуйста")
        bot.register_next_step_handler(msg, lambda m: get_second_operand(m, operand_1))

def calculate_result(message, operand_1, operand_2):
    operator = message.text
    try:
        if operator == "+":
            result = operand_1 + operand_2
        elif operator == "-":
            result = operand_1 - operand_2
        elif operator == "*":
            result = operand_1 * operand_2
        elif operator == "/":
            if operand_2 == 0:
                raise ZeroDivisionError
            result = operand_1 / operand_2  # Исправлено с % на /
        else:
            raise ValueError("Неправильный оператор")
        
        bot.send_message(message.chat.id, f"Результат: {result}")
        
        
    except ZeroDivisionError:
        bot.send_message(message.chat.id, "Ошибка: деление на ноль!")
        # Повторно запрашиваем оператор с сохранением операндов
        msg = bot.send_message(message.chat.id, "Введите оператор (+, -, *, /):")
        bot.register_next_step_handler(msg, lambda m: calculate_result(m, operand_1, operand_2))
        
    except ValueError:
        bot.send_message(message.chat.id, "Неправильный оператор! Используйте +, -, *, /")
        # Повторно запрашиваем оператор с сохранением операндов
        msg = bot.send_message(message.chat.id, "Введите оператор (+, -, *, /):")
        bot.register_next_step_handler(msg, lambda m: calculate_result(m, operand_1, operand_2))

#--------------------------------------------------------------#

def repeat(message):
    if message.content_type == 'text' and message.text.lower() == "стоп":
        choose_modules(message)
        return
    
    # Обработка разных типов сообщений
    if message.content_type == 'text':
        msg = bot.send_message(message.chat.id, message.text)
        bot.register_next_step_handler(msg, repeat)
    elif message.content_type == 'sticker':
        msg = bot.send_sticker(message.chat.id, message.sticker.file_id)
        bot.register_next_step_handler(msg, repeat)
    elif message.content_type == 'photo':
        # Отправляем самое качественное фото из массива
        msg = bot.send_photo(message.chat.id, message.photo[-1].file_id)
        bot.register_next_step_handler(msg, repeat)    
    elif message.content_type == 'animation':  # Гифки
        msg = bot.send_animation(message.chat.id, message.animation.file_id)
        bot.register_next_step_handler(msg, repeat)
    elif message.content_type == 'video':
        msg = bot.send_video(message.chat.id, message.video.file_id)
        bot.register_next_step_handler(msg, repeat)
    elif message.content_type == 'voice':
        msg = bot.send_voice(message.chat.id, message.voice.file_id)
        bot.register_next_step_handler(msg, repeat)
    else:
        msg = bot.send_message(message.chat.id, "Nuh-uh☝")
        bot.register_next_step_handler(msg, repeat)

#--------------------------------------------------------------#

def story_maker(message):
    chat_id = message.chat.id
    if chat_id not in user_story_maker_data:
        return choose_modules(message)
    
    data = user_story_maker_data[chat_id]
    text = message.text
    
    if data["step"] == "name":
        data["name"] = text
        data["step"] = "place"
        msg = bot.send_message(chat_id, "Отлично! Где происходит действие? (например: 'в Лондоне', 'на планете X')")
    
    elif data["step"] == "place":
        data["place"] = text
        data["step"] = "year"
        msg = bot.send_message(chat_id, "В каком году? (например: '2023')")
    
    elif data["step"] == "year":
        data["year"] = text
        data["step"] = "guest"
        msg = bot.send_message(chat_id, "Кого пошёл(а) проведать персонаж? (например: 'друга', 'волшебника')")
    
    elif data["step"] == "guest":
        data["guest"] = text
        data["step"] = "event"
        msg = bot.send_message(chat_id, "Что произошло? Опиши событие:")
    
    elif data["step"] == "event":
        story = (
            f"В {data['year']} году {data['place']} жил(а) {data['name']}. "
            f"Однажды {data['name']} решил(а) навестить {data['guest']}. "
            f"И вот что случилось: {text}!"
        )
        bot.send_message(chat_id, f"📖 Ваша история:\n\n{story}")
        del user_story_maker_data[chat_id]
        return choose_modules(message)
    
    bot.register_next_step_handler(msg, story_maker)

#--------------------------------------------------------------#

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as file:
        json.dump(data, file, ensure_ascii=False, indent=4, separators=(',', ': '))

def get_user_tasks(chat_id):
    data = load_data()
    return data.get(str(chat_id), [])

def process_add_step(message): #Валидация текста введённой задачи и его передача в add_user_task 
    try:
        if message.content_type == 'text':
            add_user_task(message.from_user.id, message.text)
            bot.send_message(message.chat.id, f"Задача добавлена: {message.text}")
        else:
            msg = bot.send_message(message.chat.id, "Напишите текстом")
            bot.register_next_step_handler(msg, process_add_step)
    except Exception as e:
        bot.reply_to(message, "Ошибка при добавлении задачи.")

def update_user_task(user_id, task_id, new_task=None, completed=None):
    data = load_data()
    user_tasks = data.get(str(user_id), [])
    
    for task in user_tasks:
        if task["id"] == task_id:
            if new_task is not None:
                task["task"] = new_task
            if completed is not None:
                task["completed"] = completed
            break
    
    save_data(data)

def add_user_task(user_id, task): 
    data = load_data()
    if str(user_id) not in data:
        data[str(user_id)] = []
    data[str(user_id)].append({"id": len(data[str(user_id)]) + 1, "task": task, "completed": False})
    save_data(data)





def complete_task(message):
    user_tasks = get_user_tasks(message.from_user.id)
    
    # Фильтруем только невыполненные задачи
    incomplete_tasks = [task for task in user_tasks if not task["completed"]]
    
    if not incomplete_tasks:
        bot.send_message(message.chat.id, "У вас нет невыполненных задач.")
        return
    
    markup = types.InlineKeyboardMarkup()
    for task in incomplete_tasks:
        markup.add(types.InlineKeyboardButton(
            text=f"{task['id']}. {task['task']}",
            callback_data=f"complete_{task['id']}"
        ))
    
    bot.send_message(
        message.chat.id,
        "Выберите задачу для отметки как выполненную:",
        reply_markup=markup
    )



def delete_user_task(user_id, task_id):
    data = load_data()
    user_tasks = data.get(str(user_id), [])
    if not any(task["id"] == task_id for task in user_tasks):
        return False  # Задача не найдена
    
    # Удаляем задачу и пересчитываем ID
    updated_tasks = []
    new_id = 1
    for task in user_tasks:
        if task["id"] != task_id:
            task["id"] = new_id
            updated_tasks.append(task)
            new_id += 1
    
    data[str(user_id)] = updated_tasks
    save_data(data)
    return True





bot.infinity_polling()