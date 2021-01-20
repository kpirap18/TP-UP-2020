import telebot
import mongoengine
import multiprocessing
import schedule
import time

from random import seed, randint
from datetime import datetime

import config
import info
from dbinstances import User, Theme2

bot = telebot.TeleBot(info.TOKEN)

mongoengine.connect(
    db=info.DB_NAME,
    username=info.DB_USER,
    password=info.DB_PASS,
    host=info.DB_HOST,
    port=info.DB_PART
)


def button_makeup(button, keys):
    """
        Функция, чтобы кнопочки располагались в столбики.
    """

    markup = telebot.types.InlineKeyboardMarkup()

    for text_btn, text2_btn, key, key2 in zip(button[::2], button[1::2],
                                              keys[::2], keys[1::2]):
        markup.add(
            telebot.types.InlineKeyboardButton(text=text_btn,
                                               callback_data=key),
            telebot.types.InlineKeyboardButton(text=text2_btn,
                                               callback_data=key2)
        )

    return markup


def send_theory(user):
    """
        Отправка теории
    """

    num = user.user_number_theme
    theme = Theme2.objects(number=num).first()
    print(theme)
    msg = f"_Тема {theme.number}-{theme.name}_\n\n {theme.theory}"
    msg += "\n\n\nДля продолжения нажми /theme\n"
    bot.send_message(user.user_id,
                     msg,
                     parse_mode="markdown"
                     )
    user.user_status = "questions"
    user.save()
    print(user.user_status)


def send_questions(user):
    """
        Функция отправки вопроса пользователю.
    """
    i = user.user_count_theme
    arr_number_questions = user.user_number_theme
    question = Theme2.objects(number=arr_number_questions).first()

    message = f"{question.text[i]} \n\n"

    buttons = button_makeup(list(question.answers[i]),
                            list(config.BUTTON_ANS.keys()))

    bot.send_message(user.user_id,
                     message,
                     reply_markup=buttons,
                     parse_mode="markdown"
                     )

    if i == config.PORTION_QUE - 1:
        user.user_status = "questions"
    user.save()
    print(user.user_status)


@bot.callback_query_handler(lambda call: call.data in config.BUTTON_ANS)
def button_handler_questions(call):
    """
        Вывод ответа правильно или неправильно ответил пользователь.
    """

    bot.answer_callback_query(call.id)
    user = User.objects(user_id=call.message.chat.id).first()
    number = user.user_number_theme
    i = user.user_count_theme
    question = Theme2.objects(number=number).first()

    if user.user_status == "questions":

        user_answer = question.answers[i][config.BUTTON_ANS[call.data] - 1]
        correct_answer = question.correct_answer[i]

        print(user_answer)
        print(correct_answer)
        print(user_answer == correct_answer)

        if user_answer in correct_answer:
            bot.send_message(call.message.chat.id,
                             text=config.CORRECT_MSG
                             )
        else:
            bot.send_message(call.message.chat.id,
                             text=config.WRONG_MSG
                             )

            user.user_wrong_answer += f"{user.user_count_theme} "
            user.user_wrong_answer_count += 1
            user.save()
    print(user.user_count_theme)
    if user.user_count_theme == config.PORTION_QUE:
        user.user_count_theme = 0

        if user.user_wrong_answer_count > (config.PORTION_QUE / 2):
            bot.send_message(call.message.chat.id,
                             text=config.END2_MSG + "\n\n\nДля продолжения нажми /theme или /tips\n"
                             )
            user.user_status = "tips"
        elif user.user_wrong_answer_count == 0:
            bot.send_message(call.message.chat.id,
                             text=config.END2_MSG + "\n\n\nДля продолжения нажми /theme\n"
                             )
            user.user_status = "task"
        else:
            bot.send_message(call.message.chat.id,
                             text=config.END2_MSG + "\n\n\nДля продолжения нажми /theme или /tips\n"
                             )
            user.user_status = "tips"

        user.save()
    else:
        user.user_count_theme += 1

        user.save()
        send_questions(user)


def send_tips(user):
    """
        После ответа на вопросы приходит сообщение о подсказках,
        тем у кого были ошибки и стоит статус "tips".
    """
    wrong_ans = user.user_wrong_answer.split(" ")
    wrong_ans = wrong_ans[:len(wrong_ans) - 1]
    wrong_ans2 = set(wrong_ans)
    user.user_wrong_answer_count = len(wrong_ans2)
    user.save()
    wrong_ans = list(wrong_ans2)
    question = Theme2.objects(number=user.user_number_theme).first()

    if len(wrong_ans):

        message = "Повтори эти вопросы, чтобы лучше запомнить\n"

        for i in range(len(wrong_ans)):
            print(i)
            message += f"\nВОПРОС: {question.text[i]}\nОТВЕТ: {question.correct_answer[i]} \n"
            print(message)

        message += "\n\n\nДля продолжения нажми /theme\n"
        bot.send_message(user.user_id,
                         text=message,
                         parse_mode="markdown"
                         )

        user.user_wrong_answer = ""
        user.user_status = "task"
        user.user_wrong_answer_count = 0
        user.save()
    elif user.user_status == "tips":
        user.user_wrong_answer = ""
        user.user_status = "task"
        user.user_wrong_answer_count = 0
        user.save()
        bot.send_message(user.user_id,
                         text=config.TIPS1_MSG + "\n\n\nДля продолжения нажми /theme\n",
                         parse_mode="markdown"
                         )


def send_task(user):
    question = Theme2.objects(number=user.user_number_theme).first()
    task = question.task
    task += "\n\n\nДля продолжения нажми /theme\n"
    bot.send_message(user.user_id,
                     text=task,
                     parse_mode="markdown"
                     )
    user.user_status = "task_right"
    user.save()


def send_task_right(user):
    question = Theme2.objects(number=user.user_number_theme).first()
    task = "Примерное решение задачи\n"
    task += question.task_answer
    task += "\n\n\nДля продолжения нажми /theme\n"
    bot.send_message(user.user_id,
                     text=task,
                     parse_mode="markdown"
                     )
    user.user_status = "theme"
    user.user_number_theme += 1
    user.save()


@bot.message_handler(commands=["theme"])
def theme_messages(message):
    """
        Взависимости от статуса пользователя ему будет
        выдано:
        <статус> - <что выдано>
        theme - теория по теме
        questions - вопросы по теме
        tips - подсказки, если были неверно отвеченные вопросы
        task - задача
        task_right - возможное решение
    """

    if User.objects(user_id=message.chat.id):
        user = User.objects(user_id=message.chat.id).first()
        if Theme2.objects(number=user.user_number_theme):
            print(message.chat.id, user, user.user_status)
            if user.user_status == "theme":
                send_theory(user)
            elif user.user_status == "questions":
                send_questions(user)
            elif user.user_status == "tips":
                print(1122)
                send_tips(user)
            elif user.user_status == "task":
                send_task(user)
            elif user.user_status == "task_right":
                send_task_right(user)
        else:
            bot.send_message(message.chat.id,
                             text=config.NOT_THEME
                             )
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


@bot.message_handler(commands=["choice"])
def choice_messages(message):
    """
        Выбор темы для изучения.
    """

    if User.objects(user_id=message.chat.id):
        print("choice")
        print(message.chat.id)
        message1 = "Выбери какую хочешь тему изучать\n"

        for i in range(config.COUNT_QUE):
            theme = Theme2.objects(number=i + 1).first()
            message1 += f"_Тема {theme.number}-{theme.name}_\n"

        msg = bot.send_message(message.chat.id,
                               text=message1,
                               parse_mode="markdown"
                               )
        bot.register_next_step_handler(msg, theme_choice)
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


def theme_choice(message):
    """
        Выбор номера темы.
    """

    if type(message.text) == str:
        user_number_theme = int(message.text)

        user = User.objects(user_id=message.chat.id).first()
        user.user_number_theme = user_number_theme
        user.save()

        bot.send_message(message.chat.id,
                         text="Тема выбрана!!!\n\n\nДля продолжения нажми /theme\n"
                         )


@bot.message_handler(commands=["theory"])
def theory_messages(message):
    """
        Теория по теме.
    """

    if User.objects(user_id=message.chat.id):
        user = User.objects(user_id=message.chat.id).first()
        user.user_status = "theme"
        user.save()
        theme_messages(message)
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


@bot.message_handler(commands=["questions"])
def questions_messages(message):
    """
        Вопросы минуя теорию по номеру темы.
    """

    if User.objects(user_id=message.chat.id):
        user = User.objects(user_id=message.chat.id).first()
        user.user_status = "questions"
        user.save()
        theme_messages(message)
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


@bot.message_handler(commands=["tips"])
def tips_messages(message):
    """
        Подсказки.
    """

    if User.objects(user_id=message.chat.id):
        user = User.objects(user_id=message.chat.id).first()
        user.user_status = "tips"
        user.save()
        theme_messages(message)
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


@bot.message_handler(commands=["task"])
def task_messages(message):
    """
        Задача.
    """

    if User.objects(user_id=message.chat.id):
        user = User.objects(user_id=message.chat.id).first()
        user.user_status = "task"
        user.save()
        theme_messages(message)
    else:
        bot.send_message(message.chat.id,
                         text="Сначала надо нажать /start"
                         )


@bot.message_handler(commands=["start"])
def start_messages(message):
    """
        Запись некоторых данных пользователя в бд.
    """

    if not User.objects(user_id=message.chat.id):
        msg = bot.send_message(message.chat.id,
                               text=config.HELLO_MESSAGE
                               )

        bot.register_next_step_handler(msg, name_ask)

    else:
        bot.send_message(message.chat.id,
                         text="А мы уже знакомы 😄"
                         )


def generate():
    """
        Создание братьев R2-D2.
    """

    seed(datetime.now())
    return f"R{randint(0, 100)}-D{randint(0, 100)}"


def name_ask(message):
    """
        Запись данных в саму базу данных.
    """

    if type(message.text) == str:
        user_name = message.text

        user = User(
            user_id=message.chat.id,
            user_name=user_name,
            user_status="theme",
            user_count_theme=0,
            user_number_theme=1,
            user_wrong_answer="",
            user_wrong_answer_count=0
        )
        if message.chat.username is None:
            user.user_login = f"[{generate()}](tg://user?id={str(message.chat.id)})"
        else:
            user.user_login = message.chat.username
        user.save()

        bot.send_message(message.chat.id,
                         text="👋 Привет, " + user_name +
                              config.START_REG_MSG
                         )
    else:
        msg = bot.send_message(message.chat.id,
                               text="😔 Прости, я тебя не понимаю,"
                                    "попробуй еще раз"
                               )

        bot.register_next_step_handler(msg, name_ask)


@bot.message_handler(commands=["help"])
def help_messages(message):
    """
        Информация о помощи.
    """

    keyboard = telebot.types.InlineKeyboardMarkup()

    button1 = telebot.types.InlineKeyboardButton(
        config.HELP_BUTTON,
        url='telegram.me/k_ira_18')
    keyboard.add(button1)

    bot.send_message(message.chat.id,
                     text=config.HELP_MESSAGE,
                     reply_markup=keyboard
                     )


@bot.message_handler(commands=["info"])
def developers_messages(message):
    """
        Информация о боте и разработчиках.
    """

    keyboard = telebot.types.InlineKeyboardMarkup()

    button1 = telebot.types.InlineKeyboardButton(
        config.HELP_BUTTON,
        url='telegram.me/k_ira_18')
    keyboard.add(button1)

    bot.send_message(message.chat.id,
                     text=config.INFO_MESSAGE,
                     reply_markup=keyboard
                     )


@bot.message_handler(content_types=["text"])
def repeat_all_messages(message):
    """
        Если пользователь прислал просто текст.
    """

    keyboard = telebot.types.InlineKeyboardMarkup()

    button1 = telebot.types.InlineKeyboardButton(
        config.HELP_BUTTON,
        url='telegram.me/k_ira_18')
    keyboard.add(button1)
    bot.send_message(message.chat.id,
                     text=config.UNDERSTAND_MSG,
                     reply_markup=keyboard
                     )


def schedule__():
    """
        Время отправки сообщений про готовность.
    """

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    multiprocessing.Process(target=schedule__, args=()).start()
    bot.polling(none_stop=True, interval=0)
