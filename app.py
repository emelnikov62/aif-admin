import telebot
from flask import Flask, request
from telebot import types

app = Flask(__name__)

SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
STARTED = 'start'
BACK_TO_MAIN_MENU = 'back_to_main_menu'
MY_BOTS = 'my_bots'
BUY_BOT = 'buy_bot'
BOT_RECORD_CLIENTS = 'bot_recording_clients'


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
            keyboard = createMainMenu()
            bot.send_message(chat_id, text='✅ Меню', reply_markup=keyboard)
        else:
            if text == BACK_TO_MAIN_MENU:
                keyboard = createMainMenu()
                text = 'Меню'
            elif text == MY_BOTS:
                text = '...'
                keyboard.add(createBackToMainMenu())
            elif text == BUY_BOT:
                text = 'Выберите бота'
                keyboard = createBuyBotsMenu()
                keyboard.add(createBackToMainMenu())
            else:
                keyboard.add(createBackToMainMenu())

            bot.send_message(chat_id, text=f'✅ {text}', reply_markup=keyboard)

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


def createMainMenu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='🛅 Мои боты', callback_data=MY_BOTS))
    keyboard.add(types.InlineKeyboardButton(text='💰 Купить бота', callback_data=BUY_BOT))

    return keyboard


def createBuyBotsMenu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='📝 Бот записи клиентов', callback_data=BOT_RECORD_CLIENTS))

    return keyboard


def createBackToMainMenu():
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=BACK_TO_MAIN_MENU)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
