from peewee import *
from telethon import TelegramClient, events, types
import uuid

db = SqliteDatabase('users.db')

class User(Model):
    user_id = IntegerField()
    username = CharField(null=True)
    access_hash = BigIntegerField(null=True)
    full_data = TextField(null=True)

    class Meta:
        database = db

class UserMessage(Model):
    user_id = IntegerField()
    file_id = BigIntegerField()
    parts = IntegerField()
    name = CharField()
    md5_checksum = CharField()

    class Meta:
        database = db

db.connect()
db.create_tables([User, UserMessage], safe=True)

client = TelegramClient('ULTRA', 21976053, '2411fa843fae9dedf312d81ad3129ddc').start(bot_token='6535025308:AAGqLL8L3MohAvT9L8soyCgawCrWLLwWvwU')
client.parse_mode='html'

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    if event.is_private:
        user_data = await client.get_entity(event.sender_id)
        user_id = user_data.id
        username = user_data.username
        access_hash = user_data.access_hash
        full_data = str(user_data)

        exists = User.select().where((User.user_id == user_id) & (User.username == username)).exists()

        if not exists:
            User.create(user_id=user_id, username=username, access_hash=access_hash, full_data=full_data)
        await event.reply("Привет! Я бот, который может конвертировать ваше сообщение в HTML файл. Создатель - killstreakov.t.me")
        raise events.StopPropagation

@client.on(events.InlineQuery)
async def handler(event):
    query = event.text
    user_id = event.query.user_id

    if query.startswith("-id"):
        try:
            file_id = int(query.split()[1])
        except (IndexError, ValueError):
            await event.answer([])
            return

        try:
            user_message = UserMessage.get(UserMessage.file_id == file_id)
        except UserMessage.DoesNotExist:
            await event.answer([])
            return

        file_info_message = f'ID: {user_message.file_id}\nMD5: {user_message.md5_checksum}'

        file_to_send = types.InputFile(
            id=user_message.file_id,
            parts=user_message.parts,
            name=user_message.name,
            md5_checksum=user_message.md5_checksum
        )
        builder = event.builder
        result = builder.document(file_to_send,
                                  title="Отправить готовый файл в этот чат",
                                  text=file_info_message,
                                  mime_type='text/plain')
        await event.answer([result])

    else:
        formatted_query = query.replace('\n', '<br>')
        html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{formatted_query}</body></html>'
        file_content = html_content.encode('utf-8')
        file_name = f'file_{uuid.uuid4()}.html'
        file = await client.upload_file(file_content, file_name=file_name)
        file_info_message = f'ID: {file.id}\nMD5: {file.md5_checksum}'
        builder = event.builder
        result = builder.document(file,
                                  title="Отправить файл в этот чат",
                                  text=file_info_message,
                                  mime_type='text/plain')
        await event.answer([result])
        UserMessage.create(
            user_id=user_id,
            file_id=file.id,
            parts=file.parts,
            name=file.name,
            md5_checksum=file.md5_checksum
        )

@client.on(events.NewMessage(incoming=True))
async def message_handler(event):
    if event.is_private:
        query = event.text
        formatted_query = query.replace('\n', '<br>')
        html_content = f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body>{formatted_query}</body></html>'
        file_content = html_content.encode('utf-8')
        file_name = f'file_{uuid.uuid4()}.html'
        file = await client.upload_file(file_content, file_name=file_name)

        user_id = event.sender_id

        UserMessage.create(
            user_id=user_id,
            file_id=file.id,
            parts=file.parts,
            name=file.name,
            md5_checksum=file.md5_checksum
        )

        file_info_message = f'ID: {file.id}\nMD5: {file.md5_checksum}'
        await event.reply(file=file, message=file_info_message)

client.start()
client.run_until_disconnected()