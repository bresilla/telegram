import logging
from aiogram import Bot, Dispatcher, executor, types, md
from aiogram.dispatcher import FSMContext
from aiogram.utils import executor
import sqlite3

class UserDatabase:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self.conn = self.create_connection()
        self.create_table()
        self.user_policy_possible_values = ['ctrl_unlimited', 'ctrl', 'auto']
        self.admin_policy_possible_values = ['ctrl_unlimited', 'ctrl', 'auto']
        self.__initial_policy()

    def create_connection(self):
        return sqlite3.connect(self.db_name)

    def create_table(self):
        cursor = self.conn.cursor()
        create_table_query = '''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            chat_id INTEGER NOT NULL,
            admin INTEGER DEFAULT 0,
            approved INTEGER DEFAULT 0,
            updates INTEGER DEFAULT 1,
            blocked INTEGER DEFAULT 0,
            requests INTEGER DEFAULT 0
        );
        '''
        cursor.execute(create_table_query)

        create_policy_table_query = '''
        CREATE TABLE IF NOT EXISTS policy (
            id INTEGER PRIMARY KEY,
            user_policy TEXT NOT NULL,
            admin_policy TEXT NOT NULL,
            user_max_requests INTEGER DEFAULT 3,
            admin_max_requests INTEGER DEFAULT 3
        );
        '''
        cursor.execute(create_policy_table_query)

        self.conn.commit()
        cursor.close()

    def __initial_policy(self):
        cursor = self.conn.cursor()
        if len(cursor.execute('SELECT * FROM policy;').fetchall()) > 0: return
        insert_query = 'INSERT INTO policy (user_policy, admin_policy) VALUES (?, ?);'
        cursor.execute(insert_query, (self.user_policy_possible_values[0], self.admin_policy_possible_values[0]))
        self.conn.commit()
        cursor.close()

    def get_policy(self, admin=False):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM policy WHERE id = 1;'
        cursor.execute(select_query)
        policy = cursor.fetchall()
        cursor.close()
        return policy[0][2 if admin else 1]
    
    def set_policy(self, policy, admin=False):
        policy_possible_values = self.admin_policy_possible_values if admin else self.user_policy_possible_values
        if policy not in policy_possible_values: return False
        cursor = self.conn.cursor()
        if admin:
            cursor.execute('UPDATE policy SET admin_policy = ? WHERE id = 1;', (policy,))
        else:
            cursor.execute('UPDATE policy SET user_policy = ? WHERE id = 1;', (policy,))

        self.conn.commit()
        cursor.close()
        return True
    
    def get_max_requests(self, admin=False):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM policy WHERE id = 1;'
        cursor.execute(select_query)
        policy = cursor.fetchall()
        cursor.close()
        return policy[0][4 if admin else 3]
    
    def print_policies(self):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM policy WHERE id = 1;'
        cursor.execute(select_query)
        policy = cursor.fetchall()
        cursor.close()
        print(policy)

    def print_users(self):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users;'
        cursor.execute(select_query)
        users = cursor.fetchall()
        cursor.close()
        print(users)

    def insert_user(self, username, chat_id, admin=0, approved=0, updates=1, blocked=0):
        cursor = self.conn.cursor()
        insert_query = 'INSERT INTO users (username, chat_id, admin, approved, updates, blocked, requests) VALUES (?, ?, ?, ?, ?, ?, ?);'
        cursor.execute(insert_query, (username, chat_id, admin, approved, updates, blocked, 0))
        self.conn.commit()
        cursor.close()

    def remove_user(self, username):
        cursor = self.conn.cursor()
        delete_query = 'DELETE FROM users WHERE username = ?;'
        cursor.execute(delete_query, (username,))
        self.conn.commit()
        cursor.close()

    def get_users(self):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users;'
        cursor.execute(select_query)
        users = cursor.fetchall()
        cursor.close()
        return users
    
    def user_exists(self, username):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return len(users) > 0
    
    def user_approved(self, username):
        if not self.user_exists(username): return False
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return users[0][4] == 1
    
    def approve_user(self, username):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        update_query = 'UPDATE users SET approved = ? WHERE username = ?;'
        cursor.execute(update_query, (1, username))
        self.conn.commit()
        cursor.close()

    def block_user(self, username):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        update_query = 'UPDATE users SET blocked = ? WHERE username = ?;'
        cursor.execute(update_query, (1, username))
        self.conn.commit()
        cursor.close()

    def is_blocked(self, username):
        if not self.user_exists(username): return False
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return users[0][6] == 1

    def increment_requests(self, username):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        requests = users[0][7]
        requests += 1
        update_query = 'UPDATE users SET requests = ? WHERE username = ?;'
        cursor.execute(update_query, (requests, username))
        self.conn.commit()
        cursor.close()

    def get_requests(self, username):
        if not self.user_exists(username): return False
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return users[0][7]
    
    def is_admin(self, username):
        if not self.user_exists(username): return False
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return users[0][3] == 1

    def reciving_updates(self, username):
        if not self.user_exists(username): return False
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        cursor.close()
        return users[0][4] == 1
    
    def flip_updates(self, username):
        cursor = self.conn.cursor()
        select_query = 'SELECT * FROM users WHERE username = ?;'
        cursor.execute(select_query, (username,))
        users = cursor.fetchall()
        updates = users[0][4]
        updates = 1 - updates
        update_query = 'UPDATE users SET updates = ? WHERE username = ?;'
        cursor.execute(update_query, (updates, username))
        self.conn.commit()
        cursor.close()

    def close_connection(self):
        self.conn.close()


API_TOKEN = "<yours>"
PASSWORD = "batman"
PASSWORD_ADMIN = "superman"

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
user_db = UserDatabase()


async def msg(text, username=None, to_all=False):
    users = user_db.get_users()
    for user in users:
        if to_all:
            await bot.send_message(user[2], text)
            continue
        if user[4] == 1 and user[5] == 1 and user[1] != username:
            await bot.send_message(user[2], text)


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("Hi!\nI'm OXBO-BOT!\n")
    await message.reply("Please, type /register 'password' to register or /help to see all commands")


@dp.message_handler(commands=['user_policy'])
async def user_policy(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    policy_type = message.get_args()
    if policy_type == '': 
        await message.answer(f"Current {message.text}: {user_db.get_policy()}")
        return
    if user_db.set_policy(policy_type):
        await message.answer(f"Policy set to {policy_type}")
    else:
        await message.answer(f"Wrong policy value. Possible values: {user_db.user_policy_possible_values}")


@dp.message_handler(commands=['admin_policy'])
async def admin_policy(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    policy_type = message.get_args()
    if policy_type == '': 
        await message.answer(f"Current {message.text}: {user_db.get_policy(admin=True)}")
        return
    if user_db.set_policy(policy_type, admin=True):
        await message.answer(f"Policy set to {policy_type}")
    else:
        await message.answer(f"Wrong policy value. Possible values: {user_db.admin_policy_possible_values}")


@dp.message_handler(commands=['register'])
async def register(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    passwd = message.get_args()
    if passwd != PASSWORD and passwd != PASSWORD_ADMIN:
        await message.reply("Wrong password")
        #report to admins
        for user in user_db.get_users():
            if user[3] == 1:
                await bot.send_message(user[2], f"User *{message.from_user.username}* tried to register with wrong password")
        return
    username = message.from_user.username
    if username is None:
        await message.reply("Please, set username first in the settings")
        return
    chat_id = message.from_user.id
    admin = 1 if passwd == PASSWORD_ADMIN else 0
    approved = 1
    if admin != 1:
        policy = user_db.get_policy()
        if policy == 'auto':
            approved = 1
        elif policy == 'ctrl':
            approved = 0
        elif policy == 'ctrl_unlimited':
            approved = 0

    #tell admins about new user and if it is admin
    for user in user_db.get_users():
        if user[3] == 1:
            await bot.send_message(user[2], f"New user *{username}* registered")
            if admin == 1:
                await bot.send_message(user[2], f"User *{username}* is admin")

    user_db.insert_user(username, chat_id, admin, approved)
    await message.reply(f"Wellcome *{username}*! You have been registered")
    await message.answer(f"Please, type /help to see all commands")


@dp.message_handler(commands=['approve'])
async def approve(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    username = message.get_args()
    if not user_db.user_exists(username): await message.reply(f"User {username} not registered"); return
    user_db.approve_user(username)
    await message.answer(f"User {username} approved")
    #notify user
    for user in user_db.get_users():
        if user[1] == username:
            await bot.send_message(user[2], f"Your account has been approved by *{message.from_user.username}*")


async def approve_request(message: types.Message, username):
    users = user_db.get_users()
    for user in users:
        if user[3] == 1:
            inline_keyboard_markup = types.InlineKeyboardMarkup()
            inline_keyboard_markup.add(types.InlineKeyboardButton("Yes", callback_data=f"button_approve__{username}"))
            inline_keyboard_markup.add(types.InlineKeyboardButton("No", callback_data=f"button_reject__{username}"))
            inline_keyboard_markup.add(types.InlineKeyboardButton("Ignore", callback_data=f"button_ignore__{username}"))
            await bot.send_message(user[2], f"User {username} is asking for approval. Approve it?", reply_markup=inline_keyboard_markup)
            break


@dp.callback_query_handler(lambda c: c.data.startswith('button'))
async def process_button_click(callback_query: types.CallbackQuery):
    # Get the button data to identify which button was clicked
    callback_data = callback_query.data.split('__')
    #strip username from button data
    button_data, username = callback_data[0], callback_data[1]

    if button_data == "button_approve":
        user_db.approve_user(username)
        # await bot.answer_callback_query(callback_query.id, "User approved")
        for user in user_db.get_users():
            if user[1] == username:
                await bot.send_message(user[2], f"Your account has been approved by *{callback_query.from_user.username}*")
    elif button_data == "button_reject":
        user_db.block_user(username)
        # await bot.answer_callback_query(callback_query.id, "User blocked")
        for user in user_db.get_users():
            if user[1] == username:
                await bot.send_message(user[2], f"Your account has been blocked by *{callback_query.from_user.username}*")
    elif button_data == "button_ignore":
        await bot.answer_callback_query(callback_query.id, "Ignored")


@dp.message_handler(commands=['block'])
async def block(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    username = message.get_args()
    if not user_db.user_exists(username): await message.reply(f"User {username} not registered"); return
    user_db.block_user(username)
    await message.answer(f"User {username} blocked")


@dp.message_handler(commands=['ask_approval'])
async def ask_approval(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    username = message.from_user.username
    if user_db.user_approved(username): await message.reply("You are already approved"); return
    #notify admins
    if user_db.get_policy() == 'ctrl': 
        user_db.increment_requests(username)
        #remaining requests
        await message.reply(f"Your request has been sent to admins. Remaining requests: {user_db.get_max_requests() - user_db.get_requests(username)}")
        if user_db.get_requests(username) >= user_db.get_max_requests() and user_db.get_policy() == 'ctrl':
            user_db.block_user(username)
            await message.answer("You have been blocked for too many requests")
            #notify user
            for user in user_db.get_users():
                if user[1] == username:
                    await bot.send_message(user[2], f"Your account has been blocked for too many requests")
    elif user_db.get_policy() == 'auto':
        user_db.approve_user(username)
        await message.answer("You have been approved")
        #notify user
        for user in user_db.get_users():
            if user[1] == username:
                await bot.send_message(user[2], f"Your account has been approved by admins")
    else:
        await approve_request(message, username)




@dp.message_handler(commands=['users'])
async def users(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    await message.answer(f"Users: {user_db.get_users()}")


@dp.message_handler(commands=['remove'])
async def remove(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    username = message.get_args()
    if not user_db.user_exists(username): await message.reply(f"User {username} is not registered"); return
    user_db.remove_user(username)
    await message.answer(f"User {username} removed")


@dp.message_handler(commands=['unregister'])
async def unregister(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    username = message.from_user.username
    user_db.remove_user(username)
    await message.answer(f"User {username} removed")


@dp.message_handler(commands=['updates'])
async def updates(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.user_approved(message.from_user.username): await message.reply("You have limited access until approved by admins"); return
    username = message.from_user.username
    user_db.flip_updates(username)
    await message.answer(f"Updates turned {'on' if user_db.reciving_updates(username) else 'off'}")


@dp.message_handler(commands=['info'])
async def info(message: types.Message):
    username = message.from_user.username
    locale = message.from_user.locale
    registered = user_db.user_exists(username)
    chat_id = message.from_user.id
    is_admin = user_db.is_admin(username)
    reciving_updates = user_db.reciving_updates(username)
    approved = user_db.user_approved(username)
    blocked = user_db.is_blocked(username)

    info_message = {
        "Username": username,
        "Registered": registered,
        "Approved": approved,
        "Blocked": blocked,
        "Locale": locale,
        "ChatID": chat_id
    }

    if info_message["Registered"]:
        info_message["Admin"] = is_admin
        info_message["Updates"] = reciving_updates

    await message.reply(f"Info about you:\n" + "\n".join([f"🔸 {key}: {value}" for key, value in info_message.items()]))
    

@dp.message_handler(commands=['notify'])
async def notify(message: types.Message):
    username = message.from_user.username
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.user_approved(message.from_user.username): await message.reply("You have limited access until approved by admins"); return
    # if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    await msg(f"Message from *{username}*: {message.get_args()}", username)


@dp.message_handler(commands=['announce'])
async def announce(message: types.Message):
    username = message.from_user.username
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if not user_db.is_admin(message.from_user.username): await message.reply("You are not admin"); return
    await msg(f"Announcement from *{username}*: {message.get_args()}", username, to_all=True)


@dp.message_handler(commands=['img'])
async def sendphoto(message: types.Message):
    camera_number = message.get_args()
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    if camera_number is None:
        await message.answer("Please, type /img 'camera_id' to see photos")
        return
    try:
        camera_number = int(camera_number)
    except ValueError:
        await message.answer("Please, type /img [0-9] to see photos")
        return
    if camera_number < 0 or camera_number > 9:
        await message.answer("Please, type /img [0-9] to see photos")
        return
    await message.reply_photo(open(f"/home/bresilla/down/{camera_number}.jpg", 'rb'))


@dp.message_handler(commands=['logs'])
async def read_file(message: types.Message):
    if user_db.is_blocked(message.from_user.username): await message.reply("You are blocked"); return
    if not user_db.user_exists(message.from_user.username): await message.reply("Not registered, please use /help"); return
    await message.answer("Reading file...")
    with open(".envrc", "r") as file:
        await message.answer(file.read())


@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    username = message.from_user.username
    management_commands = {
        '/info': 'see info about you',
        '/help': 'see all commands',
        '/register': 'register your username',
    }

    operations_commands = {
        '/img [0-9]': 'see photos from camera',
        '/logs': 'see logs from server',
    }

    if user_db.user_exists(username):
        management_commands['/unregister'] = 'unregister yourself'
        management_commands['/updates'] = 'turn on/off updates'
        management_commands['/notify [message]'] = 'notify all users with updates \'on\''
        management_commands['/ask_approval'] = 'ask admins for approval'
        management_commands.pop('/register')
        # command_description.pop('/help')

    if user_db.is_admin(username):
        management_commands['/announce [message]'] = 'send announcement to all users'
        management_commands['/users'] = 'see all registered users'
        management_commands['/approve [username]'] = 'approve user'
        management_commands['/block [username]'] = 'block user'
        management_commands['/remove [username]'] = 'remove user from database'
        management_commands[f"/user_policy {user_db.user_policy_possible_values}"] = 'get/set policy for user approval'
        management_commands[f"/admin_policy {user_db.admin_policy_possible_values}"] = 'get/set policy for admin approval'
        
    if user_db.user_approved(username):
        management_commands.pop('/ask_approval')


    await message.answer(f"Management Commands:\n" + "\n".join([f"{command} - {description}" for command, description in management_commands.items()]))
    if user_db.user_exists(username) and user_db.user_approved(username):
        await message.answer(f"Operations Commands:\n" + "\n".join([f"{command} - {description}" for command, description in operations_commands.items()]))


@dp.message_handler()
async def echo(message: types.Message):
    await message.reply("type /help to see all commands")

if __name__ == '__main__':
    executor.start(dp, msg("I am awake and ready to work."))
    executor.start_polling(dp, skip_updates=True)