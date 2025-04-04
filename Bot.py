import telebot
from telebot import types
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime
import os #Для проверки наличия файла
import re

BOT_TOKEN = 'BOT_TOKEN'

# Путь к JSON-файлу
CREDENTIALS_FILE = os.path.abspath("details-of-registered-users-4b69d0c0cf11.json")


# ID Google Sheets таблицы
SPREADSHEET_ID = '10VZltxul4XS5VCHiA9-GeMvA58W-I_N0nzzem7Nsz5Q'

# название листа в таблице
WORKSHEET_NAME = 'Лист1'

bot = telebot.TeleBot(BOT_TOKEN)
# Словарь для хранения состояний пользователей (шаг регистрации)
user_states = {}

#Словарь для хранения данных пользователей
user_data = {}

available_events = {
    "event1": "Конференция по AI",
    "event2": "Мастер-класс по Python",
    "event3": "Вебинар по маркетингу",
    "event4": "Спортивное мероприятие",
    "event5": "Благотворительный концерт",
}
def setup_google_sheets():
    """Аутентификация в Google Sheets и открытие таблицы."""
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    print("33333")
    #Проверяем, существует ли файл.
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"Ошибка: Файл {CREDENTIALS_FILE} не найден. Пожалуйста, убедитесь, что путь к файлу указан верно.")
        return None

    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
        gc = gspread.service_account(filename=CREDENTIALS_FILE)
        sh = gc.open_by_key(SPREADSHEET_ID)
        worksheet = sh.worksheet(WORKSHEET_NAME)
        return worksheet
    except Exception as e:
        print(f"Ошибка при аутентификации или открытии Google Sheets: {e}")
        return None


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Регистрация на мероприятие") # Делается с божьей помощью (Ксюхой и Софой)
    btn2 = types.KeyboardButton("Отмена регистрации")
    btn3 = types.KeyboardButton("Информация о лекции") # Делает Петя
    btn4 = types.KeyboardButton("Написать отзыв")
    btn5 = types.KeyboardButton('Показать команды')
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id,
                     text="{0.first_name}! Вас приветствует бот Отдела развития карьеры! Выберите действие:".format(
                         message.from_user), reply_markup=markup)
    print(message.chat.id)


@bot.message_handler(func=lambda message: message.text == "Регистрация на мероприятие")
def register(message):
    #Запуск процесса регистрации: выбор мероприятия.
    chat_id = message.chat.id
    user_states[chat_id] = "choosing_event"  # Устанавливаем состояние "выбор мероприятия"
    user_data[chat_id] = {}  # Инициализируем словарь для данных пользователя

    # Создаем клавиатуру с вариантами мероприятий
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) #one_time_keyboard чтобы скрыть кнопки после выбора
    for event_code, event_name in available_events.items():
        markup.add(types.KeyboardButton(event_name)) #Добавляем название мероприятия на кнопку

    bot.send_message(chat_id, "Пожалуйста, выберите мероприятие, на которое хотите зарегистрироваться:", reply_markup=markup)

# Обработчик текстовых сообщений (выбор мероприятия)
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "choosing_event")
def choose_event(message):
    """Обработка выбора мероприятия."""
    chat_id = message.chat.id
    selected_event_name = message.text

    # Ищем код мероприятия по названию
    event_code = None
    for code, name in available_events.items():
        if name == selected_event_name:
            event_code = code
            break

    if event_code:
        user_data[chat_id]['event_code'] = event_code #Сохраняем выбранный event_code (уникальный идентификатор)
        user_data[chat_id]['event_name'] = selected_event_name  #Сохраняем имя выбранного события
        user_states[chat_id] = "getting_name" #Переходим к следующему шагу
        bot.send_message(chat_id, f"Вы выбрали мероприятие: {selected_event_name}.\nТеперь, пожалуйста, введите ваше ФИО:")
    else:
        bot.send_message(chat_id, "Некорректный выбор мероприятия. Пожалуйста, выберите мероприятие из списка.")
        return #Завершаем работу обработчика

    #Удаляем клавиатуру после выбора мероприятия
    markup = types.ReplyKeyboardRemove()
    bot.send_message(chat_id, "Ожидаю ваше ФИО...", reply_markup=markup)

# Обработчик имени пользователя
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "getting_name")
def get_name(message):
    """Получение имени пользователя."""
    chat_id = message.chat.id
    user_data[chat_id]['name'] = message.text #Сохраняем имя
    user_states[chat_id] = "getting_email" #Переходим к запросу email
    bot.send_message(chat_id, "Спасибо! Теперь введите ваш email:")


# Обработчик email пользователя
@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "getting_email")
def get_email(message):
    chat_id = message.chat.id
    email = message.text

    # Регулярное выражение для проверки email
    #  Объяснение:
    #  - ^:  Начало строки
    #  - [a-zA-Z0-9._%+-]+:  Один или несколько символов: буквы (a-z, A-Z), цифры (0-9), точки, подчеркивания, знаки процента, плюсы или минусы.
    #  - @:  Символ @
    #  - [a-zA-Z0-9.-]+:  Один или несколько символов: буквы, цифры, точки или дефисы.
    #  - \.:  Точка (экранированная обратным слешем, так как точка имеет специальное значение в regex)
    #  - [a-zA-Z]{2,}:  Две или более буквы (для домена верхнего уровня, например, "com", "ru").
    #  - $:  Конец строки
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if re.match(email_pattern, email):
        user_data[chat_id]['email'] = email
        user_states[chat_id] = "confirming_registration"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True) #one_time_keyboard чтобы скрыть кнопки после выбора
        btn_yes = types.KeyboardButton("Да")
        btn_no = types.KeyboardButton("Нет")
        markup.add(btn_yes, btn_no)
        bot.send_message(chat_id, f"Подтвердите регистрацию на {user_data[chat_id]['event_name']} \nИмя: {user_data[chat_id]['name']}\nEmail: {user_data[chat_id]['email']}?", reply_markup=markup)
    else:
        bot.send_message(chat_id, "Неверный формат email. Пожалуйста, введите корректный email:")
        # Остаемся в состоянии getting_email, чтобы пользователь мог ввести email заново
        #  Можно добавить лимит попыток, если это необходимо


@bot.message_handler(func=lambda message: user_states.get(message.chat.id) == "confirming_registration")
def confirm_registration(message):
    chat_id = message.chat.id
    worksheet = None
    print(message.text)
    if message.text == "Да":
        print("ура он выбрал да")
    #Сохраняем данные в Google Sheets
        worksheet = setup_google_sheets()
        if worksheet:
          try:
            # Формируем строку данных для записи в Google Sheets
            row = [
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # Дата и время регистрации
                user_data[chat_id]['event_name'],  # Название мероприятия
                user_data[chat_id]['name'],  # Имя
                user_data[chat_id]['email'], #Email
                str(chat_id), #ID пользователя
                user_data[chat_id].get('event_code', 'N/A') #Код мероприятия
            ]
            worksheet.append_row(row)
            bot.send_message(chat_id, "Вы успешно зарегистрированы! Данные сохранены.")

          except Exception as e:
            bot.send_message(chat_id, f"Ошибка при записи в Google Sheets: {e}")

        else:
            bot.send_message(chat_id, "Произошла ошибка при подключении к Google Sheets. Попробуйте позже.")

        # Очищаем данные пользователя и состояние
            del user_states[chat_id]
            del user_data[chat_id]

    elif message.text == "Нет":
        bot.send_message(chat_id, "Регистрация отменена.")
    # Очищаем данные пользователя и состояние
        del user_states[chat_id]
        del user_data[chat_id]
    else:
        bot.send_message(chat_id, "Некорректный выбор. Пожалуйста, начните регистрацию заново командой /register.")
        # Очищаем данные пользователя и состояние
        del user_states[chat_id]
        del user_data[chat_id]

@bot.message_handler(content_types=['text'])
def func(message):

    if (message.text == "Информация о лекции"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Лекция в 12:00")
        btn2 = types.KeyboardButton("Лекция в 14:00")
        btn3 = types.KeyboardButton("Лекция в 16:00")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, text="О какой именно лекции ты хочешь узнать?", reply_markup=markup)

    if (message.text == "Узнать про другие лекции"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Лекция в 12:00")
        btn2 = types.KeyboardButton("Лекция в 14:00")
        btn3 = types.KeyboardButton("Лекция в 16:00")
        markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, text="О какой именно лекции ты хочешь узнать?", reply_markup=markup)


    elif (message.text == "Лекция в 12:00"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Перейти в главное меню")
        btn2 = types.KeyboardButton("Узнать про другие лекции")

        markup.add(back, btn2)

        bot.send_photo(message.chat.id,  open('C:/Users/User/Desktop/ИНСТИТУТСКАЯ ФИГНЯ/опд/БОТ/Карточка мероприятия.png', 'rb'), caption='Информация о супер крутой лекции будет тут',reply_markup=markup)



    elif (message.text == "Лекция в 14:00"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Перейти в главное меню")
        btn2 = types.KeyboardButton("Узнать про другие лекции")

        markup.add(back, btn2)
        bot.send_photo(message.chat.id,  open('C:/Users/User/Desktop/ИНСТИТУТСКАЯ ФИГНЯ/опд/БОТ/Карточка мероприятия.png', 'rb'), caption='Информация о супер крутой лекции будет тут',reply_markup=markup)

    elif (message.text == "Лекция в 16:00"):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        back = types.KeyboardButton("Перейти в главное меню")
        btn2 = types.KeyboardButton("Узнать про другие лекции")
        markup.add(back,btn2)
        bot.send_photo(message.chat.id, open('C:/Users/User/Desktop/ИНСТИТУТСКАЯ ФИГНЯ/опд/БОТ/Карточка мероприятия.png', 'Информация о супер крутой лекции будет тут'), caption='xdsfsdfsfz',reply_markup=markup)
    elif (message.text == "Показать команды"):
        bot.send_message(message.chat.id, text='Список команд:\n/start - Начало работы с ботом')


bot.infinity_polling()
