import telebot
from flask import Flask, request
from telebot import types

app = Flask(__name__)

SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
STARTED = 'start'
BACK_TO_MAIN_MENU = 'back_to_main_menu'


@app.post('/aif/admin/webhook')
def webhook():
    data = request.get_json()
    token = data.get('token')
    chat_id = data.get('chat_id')
    text = data.get('text')
    callback_data = data.get('callback')

    try:
        bot = telebot.TeleBot(token)
        keyboard = types.InlineKeyboardMarkup()

        if not callback_data:
            if text == BACK_TO_MAIN_MENU:
                keyboard = createMainMenu()
            else:
                keyboard = createMainMenu()

            bot.send_message(chat_id, text='✅ Меню', reply_markup=keyboard)
        else:
            keyboard.add(createBackToMainMenu())
            bot.send_message(chat_id, text=f'✅ {text}')

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


def createMainMenu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='🛅 Мои боты', callback_data='my_bots'))
    keyboard.add(types.InlineKeyboardButton(text='💰 Купить бота', callback_data='buy_bot'))

    return keyboard


def createBackToMainMenu():
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=BACK_TO_MAIN_MENU)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
