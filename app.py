import psycopg2
import telebot
from flask import Flask, request
from telebot import types

app = Flask(__name__)

bot = telebot.TeleBot('7277396052:AAEIEaz200U8MXlRCy60aOsEkoFKC9Q2eds')

SUCCESS = 'SUCCESS'
FAILURE = 'FAILURE'
STARTED = 'start'
BACK_TO_MAIN_MENU = 'back_to_main_menu'
BACK_TO_MY_BOTS_MENU = 'back_to_my_bots_menu'
BACK_TO_BUY_BOTS_MENU = 'back_to_buy_bots_menu'
MY_BOTS = 'my_bots'
BUY_BOT = 'buy_bot'
BOT_CREATE = 'bot_create'
BOT_SELECT = 'bot_select'
BOT_RECORD_CLIENTS = 'recording_clients'
BOT_CONNECT_TOKEN = 'bot_connect_token'
BOT_DELETE = 'bot_delete'
BOT_STATS = 'bot_stats'
BOT_SETTINGS = 'bot_settings'
DELIMITER = ';'
BOT_LOGS_ID = -1002391679452


# webhook
@app.post('/aif/admin/webhook')
def webhook():
    data = request.get_json()
    chat_id = data.get('chat_id')
    text = data.get('text')
    callback_data = data.get('callback')
    message = None

    try:
        keyboard = types.InlineKeyboardMarkup()

        if not callback_data:
            if len(text) == 46 and ':' in text:
                if linkTokenBot(text):
                    message = '✅ TOKEN бота привзяан'
                else:
                    message = '❌ Не удалось привязать TOKEN бота. Попробуйте еще раз.'

                keyboard.add(createBack(BACK_TO_MY_BOTS_MENU))
            else:
                message = '✅ Меню'
                keyboard = createMainMenu()

            bot.send_message(chat_id, text=message, reply_markup=keyboard)
        else:
            if text == BACK_TO_MAIN_MENU:
                message = '✅ Меню'
                keyboard = createMainMenu()
            elif text == MY_BOTS or text == BACK_TO_MY_BOTS_MENU or BOT_CREATE in text or BOT_DELETE in text:
                if BOT_CREATE in text:
                    id_user_bot = createBot(text, chat_id)
                    if id_user_bot is None:
                        message = '❌ Не удалось создать бота. Попробуйте еще раз.'

                if BOT_DELETE in text:
                    if not deleteAifBot(text):
                        message = '❌ Не удалось удалить бота. Попробуйте еще раз.'

                if message is None:
                    message = '✅ Меню'

                keyboard = createMyBotsMenu(chat_id)
                if keyboard is None:
                    message = '✅ У Вас пока нет ботов'
                    keyboard = types.InlineKeyboardMarkup()

                keyboard.add(createBack(BACK_TO_MAIN_MENU))
            elif text == BUY_BOT or text == BACK_TO_BUY_BOTS_MENU:
                message = '✅ Выберите бота'
                keyboard = createBuyBotsMenu()
                keyboard.add(createBack(BACK_TO_MAIN_MENU))
            elif BOT_CONNECT_TOKEN in text:
                message = '✏ Отправьте в сообщении TOKEN бота'
                keyboard.add(createBack(BACK_TO_MY_BOTS_MENU))
            elif BOT_SELECT in text:
                message = '✅ Меню'
                keyboard = createSelectedBotMenu(text)
                keyboard.add(createBack(BACK_TO_MY_BOTS_MENU))
            else:
                keyboard.add(createBack(BACK_TO_MAIN_MENU))

            bot.send_message(chat_id, text=f'{message}', reply_markup=keyboard)

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


# create selected bot menu
def createSelectedBotMenu(text):
    keyboard = types.InlineKeyboardMarkup()

    params = text.split(DELIMITER)

    user_bot = getMyAifBot(params[1])
    if user_bot is None:
        return types.InlineKeyboardMarkup()

    if user_bot[4] is None:
        keyboard.add(types.InlineKeyboardButton(text=f'✅ Привязать TOKEN',
                                                callback_data=f'{BOT_CONNECT_TOKEN}{DELIMITER}{user_bot[0]}'))
    else:
        keyboard.add(
            types.InlineKeyboardButton(text=f'📊 Статистика', callback_data=f'{BOT_STATS}{DELIMITER}{user_bot[0]}'))
        keyboard.add(
            types.InlineKeyboardButton(text=f'🔧 Настройки', callback_data=f'{BOT_SETTINGS}{DELIMITER}{user_bot[0]}'))

    keyboard.add(types.InlineKeyboardButton(text=f'✅ Open', web_app='https://aif-admin-emelnikov62.amvera.io/test'))
    keyboard.add(types.InlineKeyboardButton(text=f'⛔ Удалить', callback_data=f'{BOT_DELETE}{DELIMITER}{user_bot[0]}'))

    return keyboard


# create main menu
def createMainMenu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='📦 Мои боты', callback_data=MY_BOTS))
    keyboard.add(types.InlineKeyboardButton(text='🌐 Подключить бота', callback_data=BUY_BOT))

    return keyboard


# create buy bots menu
def createBuyBotsMenu():
    try:
        keyboard = types.InlineKeyboardMarkup()

        botTypes = getAifBotTypes()
        if botTypes is not None:
            for botType in botTypes:
                keyboard.add(types.InlineKeyboardButton(text=f'✅ {botType[1]}',
                                                        callback_data=f'{BOT_CREATE}{DELIMITER}{botType[0]}'))

        return keyboard
    except Exception as e:
        sendLog(str(e))
        return types.InlineKeyboardMarkup()


# get aif bot types
def getAifBotTypes():
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute('select b.type, b.description from n8n_test.aif_bots b where b.active')

        if cursor.rowcount == 0:
            return None

        botTypes = cursor.fetchall()
        connection.close()

        return botTypes
    except Exception as e:
        sendLog(str(e))
        return None


# get user aif bots
def getMyAifBots(id):
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute(f"select aub.id, ab.type, ab.description, aub.active, aub.token "
                       f"  from n8n_test.aif_user_bots aub "
                       f"  join n8n_test.aif_bots ab on aub.aif_bot_id = ab.id "
                       f"  join n8n_test.aif_users au on au.id = aub.aif_user_id "
                       f" where au.tg_id = '{id}'")

        if cursor.rowcount == 0:
            return None

        myBots = cursor.fetchall()
        connection.close()

        return myBots
    except Exception as e:
        sendLog(str(e))
        return None


# get user aif bot by id
def getMyAifBot(id):
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute(f"select aub.id, ab.type, ab.description, aub.active, aub.token "
                       f"  from n8n_test.aif_user_bots aub "
                       f"  join n8n_test.aif_bots ab on aub.aif_bot_id = ab.id "
                       f"  join n8n_test.aif_users au on au.id = aub.aif_user_id "
                       f" where aub.id = '{id}'")

        if cursor.rowcount == 0:
            return None

        user_bot = cursor.fetchall()[0]
        connection.close()

        return user_bot

    except Exception as e:
        sendLog(str(e))
        return None


# link token to user bot
def linkTokenBot(text):
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)
        user_bot_id = text.split(DELIMITER)[1]
        user_bot_token = text.split(DELIMITER)[2]

        cursor = connection.cursor()
        cursor.execute(f"update n8n_test.aif_user_bots set token = '{user_bot_token}' where id = '{user_bot_id}'")

        if cursor.rowcount == 0:
            return False

        connection.commit()
        connection.close()

        return True

    except Exception as e:
        sendLog(str(e))
        return False


# get user aif bot by id
def deleteAifBot(text):
    try:
        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)
        user_bot_id = text.split(DELIMITER)[1]

        cursor = connection.cursor()
        cursor.execute(f"delete from n8n_test.aif_user_bots aub where aub.id = {user_bot_id}")

        if cursor.rowcount == 0:
            return False

        connection.commit()
        connection.close()

        return True

    except Exception as e:
        sendLog(str(e))
        return False


# get database param connection
def getDbParams():
    return {'database': 'n8n_db', 'user': 'n8n_user', 'password': 'Mery1029384756$',
            'host': 'amvera-emelnikov62-cnpg-n8n-db-rw', 'port': '5432'}


# create user bot
def createBot(text, id):
    try:
        id_user_bot = None
        id_user = None

        paramsDb = getDbParams()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        sql = f"select au.id from n8n_test.aif_users au where au.tg_id = '{id}'"
        cursor.execute(sql)
        if cursor.rowcount == 0:
            sql = f"insert into n8n_test.aif_users(tg_id) values('{id}') returning id"
            cursor.execute(sql)
            id_user = cursor.fetchone()[0]
        else:
            id_user = cursor.fetchone()[0]

        if id_user is not None:
            botType = text.split(DELIMITER)[1]
            cursor.execute(f"select t.id from n8n_test.aif_bots t where t.type = '{botType}'")
            id_bot = cursor.fetchone()[0]

            if id_bot is not None:
                sql = f'insert into n8n_test.aif_user_bots(aif_user_id, aif_bot_id) values({id_user}, {id_bot}) returning id'
                cursor.execute(sql)
                id_user_bot = cursor.fetchone()[0]

        if id_user_bot is not None:
            connection.commit()

        connection.close()
        return id_user_bot
    except Exception as e:
        sendLog(e)
        return None


# create connect bot button
def createConnectBot(type):
    return types.InlineKeyboardButton(text='✅ Привязать TOKEN', callback_data=f'{BOT_CONNECT_TOKEN}{DELIMITER}{type}')


# create back button
def createBack(type):
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=type)


# create my bots menu
def createMyBotsMenu(id):
    try:
        myBots = getMyAifBots(id)

        if myBots is None:
            return None

        keyboard = types.InlineKeyboardMarkup()
        for myBot in myBots:
            if myBot[3] and myBot[4] is not None:
                text = '✅'
            else:
                text = '❌'
            text = f'{text} {myBot[2]} (ID: {myBot[0]})'
            keyboard.add(types.InlineKeyboardButton(text=text,
                                                    callback_data=f'{BOT_SELECT}{DELIMITER}{myBot[0]}{DELIMITER}{myBot[1]}'))

        return keyboard
    except Exception as e:
        sendLog(str(e))
        return None


# create manual to add bot
def createManualAddBot():
    return ('📋 Инструкция по подключению бота:\n\n'
            '   ✅ создать бота при помощи @BotFather\n\n'
            '   ✅ по кнопке "Привязать TOKEN" привязать токен бота\n\n'
            '   ✅ настроить бота после привязки под свою специфику\n\n')


# send log to group TG
def sendLog(text):
    bot.send_message(BOT_LOGS_ID, text=text)


@app.get('/test')
def test():
    return '<div style="color: red">ok</div>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=True)
