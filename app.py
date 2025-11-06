import telebot
from flask import Flask, request
from telebot import types

app = Flask(__name__)

SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'


@app.post('/aif/admin/webhook')
def webhook():
    data = request.get_json()
    token = data.get('token')
    chat_id = data.get('chat_id')

    try:
        bot = telebot.TeleBot(token)

        keyboard = types.InlineKeyboardMarkup()
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_message(chat_id, text='ok', reply_markup=keyboard)

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


# @bot.message_handler(content_types=['text'])
# def get_message(message):
#     print(message)
#     keyboard = types.InlineKeyboardMarkup()  # наша клавиатура
#     key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')  # кнопка «Да»
#     keyboard.add(key_yes)  # добавляем кнопку в клавиатуру
#     key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
#     keyboard.add(key_no)
#     bot.send_message(message.from_user.id, text='ok', reply_markup=keyboard)
#
#
# @bot.callback_query_handler(func=lambda call: True)
# def callback_worker(call):
#     if call.data == "yes":  # call.data это callback_data, которую мы указали при объявлении кнопки
#         bot.send_message(call.message.chat.id, '1')
#     elif call.data == "no":
#         bot.send_message(call.message.chat.id, '2')
#
#
# # bot.set_webhook()
# bot.polling(none_stop=True, interval=0)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
