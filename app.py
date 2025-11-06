import telebot
from flask import Flask, request

app = Flask(__name__)

@app.post('/aif/admin/webhook')
def webhook():
    data = request.get_json()
    print(data)

    try:
        bot = telebot.TeleBot(data.get('token'))
        bot.send_message(data.get('chat_id'), data.get('text'))
    except Exception as e:
        return {'type': 'FAIL', 'message': str(e)}

    return {'type': 'SUCCESS'}


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
