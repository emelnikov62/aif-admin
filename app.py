import psycopg2
import telebot
from flask import Flask, request
from telebot import types

app = Flask(__name__)

SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
STARTED = 'start'
BACK_TO_MAIN_MENU = 'back_to_main_menu'
BACK_TO_MY_BOTS_MENU = 'back_to_my_bots_menu'
BACK_TO_BUY_BOTS_MENU = 'back_to_buy_bots_menu'
MY_BOTS = 'my_bots'
BUY_BOT = 'buy_bot'
BOT_CREATE = 'bot_create'
BOT_RECORD_CLIENTS = 'recording_clients'
BOT_CONNECT_TOKEN = 'bot_connect_token'
DELIMITER = ';'


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
            if len(text) == 46 and ':' in text:
                text = '✅ TOKEN бота привзяан'
                keyboard.add(createBack(BACK_TO_MY_BOTS_MENU))
            else:
                text = '✅ Меню'
                keyboard = createMainMenu()

            bot.send_message(chat_id, text=text, reply_markup=keyboard)
        else:
            if text == BACK_TO_MAIN_MENU:
                text = '✅ Меню'
                keyboard = createMainMenu()
            elif text == MY_BOTS or text == BACK_TO_MY_BOTS_MENU or BOT_CREATE in text:
                print(text)
                if BOT_CREATE in text:
                    createBot(text, chat_id)

                text = '✅ Меню'
                keyboard.add(createMyBotsMenu())
                keyboard.add(createBack(BACK_TO_MAIN_MENU))
            elif text == BUY_BOT or text == BACK_TO_BUY_BOTS_MENU:
                text = '✅ Выберите бота'
                keyboard = createBuyBotsMenu()
                keyboard.add(createBack(BACK_TO_MAIN_MENU))
            elif BOT_CONNECT_TOKEN in text:
                text = '✏ Отправьте в сообщении TOKEN бота'
                keyboard.add(createBack(BACK_TO_MY_BOTS_MENU))
            else:
                keyboard.add(createBack(BACK_TO_MAIN_MENU))

            bot.send_message(chat_id, text=f'{text}', reply_markup=keyboard)

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


def createMainMenu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='📦 Мои боты', callback_data=MY_BOTS))
    keyboard.add(types.InlineKeyboardButton(text='🌐 Подключить бота', callback_data=BUY_BOT))

    return keyboard


def createBuyBotsMenu():
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute('select b.type, b.description from n8n_test.aif_bots b where b.active')

        if cursor.rowcount == 0:
            return types.InlineKeyboardMarkup()

        rows = cursor.fetchall()
        connection.close()
        keyboard = types.InlineKeyboardMarkup()
        for row in rows:
            keyboard.add(
                types.InlineKeyboardButton(text=f'✅ {row[1]}', callback_data=f'{BOT_CREATE}{DELIMITER}{row[0]}'))

        return keyboard
    except Exception as e:
        print(e)
        return types.InlineKeyboardMarkup()


def getDbParams():
    return {'database': 'n8n_db', 'user': 'n8n_user', 'password': 'Mery1029384756$',
            'host': 'amvera-emelnikov62-cnpg-n8n-db-rw', 'port': '5432'}


def createBot(text, id):
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        sql = f'insert into n8n_test.aif_users(tg_id) values({id}) returning id'
        cursor.execute(sql)
        idRecord = cursor.fetchone()[0]
        print(idRecord)
        if idRecord is not None:
            type = text.split(DELIMITER)[1]
            print(type)
            cursor.execute('select * from n8n_test.aif_bots t where t.type = %s', (type))
            idBot = cursor.fetchone()[0]
            print(idBot)

            if idBot is not None:
                sql = f'insert into n8n_test.aif_user_bots(aif_user_id, aif_bot_id) values({idRecord}, {idBot}) returning id'
                cursor.execute(sql)
                idUserBot = cursor.fetchone()[0]
                print(idUserBot)

        connection.close()
    except Exception as e:
        print(e)


def createConnectBot(type):
    return types.InlineKeyboardButton(text='✅ Привязать TOKEN', callback_data=f'{BOT_CONNECT_TOKEN}{DELIMITER}{type}')


def createBack(type):
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=type)


def createMyBotsMenu():
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=BACK_TO_MAIN_MENU)


def createManualAddBot():
    return ('📋 Инструкция по подключению бота:\n\n'
            '   ✅ создать бота при помощи @BotFather\n\n'
            '   ✅ по кнопке "Привязать TOKEN" привязать токен бота\n\n'
            '   ✅ настроить бота после привязки под свою специфику\n\n')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
