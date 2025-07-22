import telebot
from telebot import types
from tokens import TELEGRAM_BOT_TOKEN 
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

user_story_maker_data = {}
@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    if message.text.lower() == "/start":
        choose_modules(message)
    else:
        bot.send_message(message.chat.id, "Ты чё несешь мабой, напиши '/start'")

def choose_modules(message):
        keyboard = types.InlineKeyboardMarkup() #определяем какой вид клавиатуры испльзовать
        calculator_button = types.InlineKeyboardButton(text='🧮 Калькулятор', callback_data='calculator') 
        keyboard.add(calculator_button) #добавляем кнопку в клавиатуру
        repeater_button= types.InlineKeyboardButton(text='🔁 Повторялка текста', callback_data='repeater')
        keyboard.add(repeater_button)
        story_maker_button = types.InlineKeyboardButton(text='📖 Сочинялка историй', callback_data='story_maker')
        keyboard.add(story_maker_button) 
        question = 'Выбери модуль который тебя интересует:'
        bot.send_message(message.from_user.id, text=question, reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True) #Обработка нажатия кнопок
def callback_worker(call):
    if call.data == "calculator": 
        msg = bot.send_message(call.message.chat.id, "Введите первое число:")
        bot.register_next_step_handler(msg, get_first_operand)
    elif call.data == "repeater":       
        bot.send_message(call.message.chat.id, "Напиши 'стоп' чтобы остановить цикл")
        msg = bot.send_message(call.message.chat.id, "Напиши что тебе повторить")
        bot.register_next_step_handler(msg, repeat)
    elif call.data == "story_maker":
        msg = bot.send_message(call.message.chat.id, "Напиши имя персонажа")
        bot.register_next_step_handler(msg, story_maker)
        user_story_maker_data[msg.chat.id] = {"step": "name"}


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
        msg = bot.send_message(chat_id, "В каком году? (например: '2023', 'давным-давно')")
    
    elif data["step"] == "year":
        data["year"] = text
        data["step"] = "guest"
        msg = bot.send_message(chat_id, "К кому пошёл(а) в гости персонаж? (например: 'друга', 'волшебника')")
    
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
    




def repeat(message):
    if message.text.lower() == "стоп":
        choose_modules(message)
        return
    else:
        msg = bot.send_message(message.chat.id, message.text)
        bot.register_next_step_handler(msg, repeat)



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


bot.infinity_polling()