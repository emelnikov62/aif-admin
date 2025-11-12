import psycopg2
import requests
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


# webhook admin bot
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
            message = '✅ Меню'
            keyboard = create_main_menu()
            bot.send_message(chat_id, text=message, reply_markup=keyboard)
        else:
            if text == BACK_TO_MAIN_MENU:
                message = '✅ Меню'
                keyboard = create_main_menu()
            elif text == MY_BOTS or text == BACK_TO_MY_BOTS_MENU or BOT_CREATE in text or BOT_DELETE in text:
                if BOT_CREATE in text:
                    id_user_bot = create_bot(text, chat_id)
                    if id_user_bot is None:
                        message = '❌ Не удалось создать бота. Попробуйте еще раз.'

                if BOT_DELETE in text:
                    if not delete_aif_bot(text):
                        message = '❌ Не удалось удалить бота. Попробуйте еще раз.'

                if message is None:
                    message = '✅ Меню'

                keyboard = create_my_bots_menu(chat_id)
                if keyboard is None:
                    message = '✅ У Вас пока нет ботов'
                    keyboard = types.InlineKeyboardMarkup()

                keyboard.add(create_back_btn(BACK_TO_MAIN_MENU))
            elif text == BUY_BOT or text == BACK_TO_BUY_BOTS_MENU:
                message = '✅ Выберите бота'
                keyboard = create_buy_bots_menu()
                keyboard.add(create_back_btn(BACK_TO_MAIN_MENU))
            elif BOT_SELECT in text:
                message = '✅ Меню'
                keyboard = create_selected_bot_menu(text)
                keyboard.add(create_back_btn(BACK_TO_MY_BOTS_MENU))
            else:
                keyboard.add(create_back_btn(BACK_TO_MAIN_MENU))

            bot.send_message(chat_id, text=f'{message}', reply_markup=keyboard)

    except Exception as e:
        return {'type': FAILURE, 'message': str(e)}

    return {'type': SUCCESS}


# webhook client bot
@app.post('/aif/client/webhook')
def webhook_client():
    data = request.get_json()
    chat_id = data.get('chat_id')
    text = data.get('text')
    id = data.get('id')
    callback_data = data.get('callback')

    try:
        token = get_user_token(id)
        if token is not None:
            bot_client = telebot.TeleBot(token)
            bot_client.send_message(chat_id, text=f'📟 Привет!')

    except Exception as e:
        send_log(str(e))


# get user bot token
def get_user_token(id):
    try:
        paramsDb = get_db_params()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute(f"select token from n8n_test.aif_user_bots where id = '{id}'")

        if cursor.rowcount != 0:
            return cursor.fetchone()[0]

        return None
    except Exception as e:
        send_log(str(e))
        return None


# create selected bot menu
def create_selected_bot_menu(text):
    keyboard = types.InlineKeyboardMarkup()

    params = text.split(DELIMITER)

    user_bot = get_my_aif_bot(params[1])
    if user_bot is None:
        return types.InlineKeyboardMarkup()

    if user_bot[4] is None:
        keyboard.add(types.KeyboardButton(text=f'✅ Привязать TOKEN', web_app=types.WebAppInfo(
            f'https://aif-admin-emelnikov62.amvera.io/link-bot-form?id={params[1]}')))
    else:
        keyboard.add(
            types.InlineKeyboardButton(text=f'📊 Статистика', callback_data=f'{BOT_STATS}{DELIMITER}{user_bot[0]}'))
        keyboard.add(
            types.InlineKeyboardButton(text=f'🔧 Настройки', callback_data=f'{BOT_SETTINGS}{DELIMITER}{user_bot[0]}'))

    keyboard.add(types.InlineKeyboardButton(text=f'⛔ Удалить', callback_data=f'{BOT_DELETE}{DELIMITER}{user_bot[0]}'))

    return keyboard


# create main menu
def create_main_menu():
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(text='📦 Мои боты', callback_data=MY_BOTS))
    keyboard.add(types.InlineKeyboardButton(text='🌐 Подключить бота', callback_data=BUY_BOT))

    return keyboard


# create buy bots menu
def create_buy_bots_menu():
    try:
        keyboard = types.InlineKeyboardMarkup()

        botTypes = get_aif_bot_types()
        if botTypes is not None:
            for botType in botTypes:
                keyboard.add(types.InlineKeyboardButton(text=f'✅ {botType[1]}',
                                                        callback_data=f'{BOT_CREATE}{DELIMITER}{botType[0]}'))

        return keyboard
    except Exception as e:
        send_log(str(e))
        return types.InlineKeyboardMarkup()


# get aif bot types
def get_aif_bot_types():
    try:
        paramsDb = get_db_params()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute('select b.type, b.description from n8n_test.aif_bots b where b.active')

        if cursor.rowcount == 0:
            return None

        botTypes = cursor.fetchall()
        connection.close()

        return botTypes
    except Exception as e:
        send_log(str(e))
        return None


# get user aif bots
def get_my_aif_bots(id):
    try:
        paramsDb = get_db_params()
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
        send_log(str(e))
        return None


# get user aif bot by id
def get_my_aif_bot(id):
    try:
        paramsDb = get_db_params()
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
        send_log(str(e))
        return None


# link token to user bot
def link_token_bot(user_bot_id, user_bot_token):
    try:
        if len(user_bot_token) != 46:
            return False

        paramsDb = get_db_params()
        connection = psycopg2.connect(**paramsDb)

        cursor = connection.cursor()
        cursor.execute(f"update n8n_test.aif_user_bots set token = '{user_bot_token}' where id = '{user_bot_id}'")

        if cursor.rowcount == 0:
            return False

        connection.commit()
        connection.close()

        requests.get(
            f'https://api.telegram.org/bot{user_bot_token}/setwebhook?url=https://n8n-agent-emelnikov62.amvera.io/webhook/aif/client/webhook?id={user_bot_id}')

        return True

    except Exception as e:
        send_log(str(e))
        return False


# get user aif bot by id
def delete_aif_bot(text):
    try:
        paramsDb = get_db_params()
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
        send_log(str(e))
        return False


# get database param connection
def get_db_params():
    return {'database': 'n8n_db', 'user': 'n8n_user', 'password': 'Mery1029384756$',
            'host': 'amvera-emelnikov62-cnpg-n8n-db-rw', 'port': '5432'}


# create user bot
def create_bot(text, id):
    try:
        id_user_bot = None
        id_user = None

        paramsDb = get_db_params()
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
        send_log(e)
        return None


# create back button
def create_back_btn(type):
    return types.InlineKeyboardButton(text='⬅ Назад', callback_data=type)


# create my bots menu
def create_my_bots_menu(id):
    try:
        myBots = get_my_aif_bots(id)

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
        send_log(str(e))
        return None


# create manual to add bot
def create_manual_add_bot():
    return ('📋 Инструкция по подключению бота:\n\n'
            '   ✅ создать бота при помощи @BotFather\n\n'
            '   ✅ по кнопке "Привязать TOKEN" привязать токен бота\n\n'
            '   ✅ настроить бота после привязки под свою специфику\n\n')


# send log to group TG
def send_log(text):
    bot.send_message(BOT_LOGS_ID, text=text)


# link bot form
@app.get('/link-bot-form')
def link_bot_form():
    id = request.args.get('id')
    return ('<form method="post" action="https://aif-admin-emelnikov62.amvera.io/link-bot">'
            '<input type="text" name="token"/>'
            f'<input type="hidden" name="id" value="{id}"/>'
            '<input type="submit" value="Привязать"/>'
            '</form>')


# link bot update
@app.post('/link-bot')
def link_bot():
    data = request.form
    if link_token_bot(data.get('id'), data.get('token')):
        return '<div>ok</div>'
    else:
        return '<div>error</div>'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
