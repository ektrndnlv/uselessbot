import discord
import json
import requests
import datetime
import random


class PyBot:
    settings = {
        'API': 'https://some-random-api.ml/',
    }
    client = discord.Client()
    commands_hot_phrases = [
        {'words': ['смешно', 'харош', 'рофл', 'ахах', 'анекдот'], 'action': 'edit', 'payload': 'joke'},
        {'words': ['аниме', 'тян'], 'action': 'image', 'payload': 'anime'},
        {'words': ['нападение', 'вторжение', 'белорусь'], 'action': 'native_image', 'payload': 'lykash'}
        ]
    last_data = {
        'message': None,
        'user': {id: 0},
    }
    channel = None

    revert_chances = [0,0,0,0,1]

    comment_list = ['разрывная', 'у меня от такой шутки дед умер', 'жоска']
    comment_author = [{'src': 'https://i.ytimg. com/vi/FWnWwZashaQ/maxresdefault.jpg', 'name': 'Скала Джонсон'},
                      {'src': 'https://i.mycdn.me/i?r=AzEPZsRbOZEKgBhR0XGMT1RkCoIbOC2fWwIzowCUaUzgQaaKTM5SRkZCeTgDn6uOyic', 'name': 'Лукашенко'}]
    images = {
        'anime': {
            'type': ['wink', 'pat', 'hug'],
            'msg': ['аниме на аве, а продолжение сами знаете...', 'so horny 🤤', 'опа, попался анимешник']
        },
    }

    native_images = {
        'lykash': {
            'src': 'https://memepedia.ru/wp-content/uploads/2022/03/lukashenko-mem-a-ja-sejchas-vam-pokazhu-otkuda-gotovilos-napadenie-768x512.jpg',
            'msg': 'Я сейчас вам покажу, откуда готовилось нападение...'
        }
    }
#конструктор бота
    def __init__(self, **config):
        #достаем токен и клиент ид
        token, client_id = config.items()
        #проверяем, ЕСЛИ ЕСТЬ ТОКЕН И КЛИЕНТ ИД, ТО ЗАПИСЫВАЕМ ИХ В НАШ КЛАСС
        if token and client_id:
            self.settings['token'] = token[1]
            self.settings['client_id'] = client_id[1]
        else:
            print('Pass token and client_id')

    def __initialize_events__(self):
        print('Initialize client events')
       #реализация события готовности бота
        @self.client.event
        async def on_ready():
            print("Initialized at {date}".format(date=datetime.datetime.now()))
        #реализация события ответного действия на сообщение
        @self.client.event
        async def on_message(message):
            #проверка на то, что сообщение было не от бота
            if not message.author.bot:
                #записываем данные по последнему сообщению
                author = message.author
                content = message.content
                self.last_data['message'] = content
                self.last_data['user'] = author
                self.channel = message.channel
                #вызываем метод, который проверяет на наличие в сообщении определенного слова для вызова действия на
                #слово
                await self.__action_resolver__(content)

    async def __get_user_by_id__(self, user_id):
        return await self.client.fetch_user(user_id)

    def __get_media__(self, request, with_body=True):
        response = requests.get(self.settings['API'] + request)
        print(response)
        #если 200, то все хорошо
        if response.status_code == 200:
            #если виз бади тру, то приходит ссылка, если фолс, то картинка
            if with_body:
                #получаем объект ответа сервера
                json_data = json.loads(response.text)
                embed = discord.Embed()
                embed.set_image(url=json_data['link'])
                return {'embed': embed, 'file': None}
            else:
                #получаем картинку
                json_data = response.content
                #сохраняем картинку в компьютер
                open('memes.png', 'wb').write(json_data)
                file = discord.File('memes.png')
                embed = discord.Embed()
                embed.set_image(url="attachment://memes.png")
                return {'embed': embed, 'file': file}
        else:
            return None

    def __message_to_action__(self, message):
        #получаем каждое слово из сообщения
        for word in message.split():
            #из списка возможных команд получаем все возможные слова
            for phrase in self.commands_hot_phrases:
                #проверяем, если слово есть в списке фраз, то возвращаем наше действие
                if word.lower() in phrase['words']:
                    return {'action': phrase['action'], 'payload': phrase['payload']}
        return None

    async def __edit_action__(self, payload):
        request_path = None
        if payload == 'joke':
            author = random.choice(self.comment_author)
            request_path = 'canvas/youtube-comment?avatar={avatar}&comment={comment}&username={username}'.format(
                avatar=author['src'], comment=random.choice(self.comment_list), username=author['name'])
        if request_path:
            edit = self.__get_media__(request_path, False)
            if edit:
                file = edit['file']
                embed = edit['embed']
                await self.channel.send(embed=embed, file=file)
            else:
                await self.channel.send('Чорт, санкции не дали контент сделать(')

    async def __image_action__(self, payload):
        request_path = None
        msg = None
        if payload == 'anime':
            request_path = 'animu/{anime}'.format(anime=random.choice(self.images[payload]['type']))
            msg = random.choice(self.images[payload]['msg'])
        if request_path:
            edit = self.__get_media__(request_path)
            embed = edit['embed']
            if edit:
                await self.channel.send(msg, embed=embed)
            else:
                await self.channel.send('Чорт, санкции не дали контент сделать(')

    async def __native_image__(self, payload):
        src = self.native_images[payload]['src']
        msg = self.native_images[payload]['msg']
        embed = discord.Embed()
        embed.set_image(url=src)
        await self.channel.send(msg, embed=embed)

    async def __revert_action__(self):
        msg = self.last_data['message']
        user = self.last_data['user']
        if msg and user:
            await self.channel.send('{user} {msg}'.format(msg=msg[::-1], user=user.mention))

    async def __action_resolver__(self, message):
        #с вероятностью 1 к 5 переворачиваем все сообщение
        if random.choice(self.revert_chances):
            await self.__revert_action__()
            #получаем из сообщения определенное действие, которое боту нужно выполнить
        action_type = self.__message_to_action__(message)
        #если у нас есть действие и канал, то вызываем наше действие
        if action_type and self.channel:
            action = action_type['action']
            payload = action_type['payload']
            if action == 'edit':
                await self.__edit_action__(payload)
            elif action == 'image':
                await self.__image_action__(payload)
            elif action == 'native_image':
                await self.__native_image__(payload)

    def start(self):
        print('Starting bot with client id: {client_id}'.format(client_id=self.settings['client_id']))
        #инициализируем события библиотеки дискорд для взаимодействия с дисом
        self.__initialize_events__()
        #запускаем нашего бота
        self.client.run(self.settings['token'])


bot = PyBot(
    token="OTgwNDg2Njg4MjU2MTkyNTgy.Gn1lUI.lwPMYkWPvlQnjblYOuhnhGNtGqs1sft99SOTK0",
    client_id=980486688256192582
)
bot.start()
