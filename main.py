import aiohttp
import asyncio
import telebot
import os
from dotenv import load_dotenv
from xml.etree import ElementTree

from pyexpat.errors import XML_ERROR_SYNTAX
from telebot import types

load_dotenv()
bot = telebot.TeleBot(f"{os.getenv("TOKEN")}")
chat_id = bot.bot_id

url = "http://www.cbr.ru/scripts/XML_daily.asp"


async def fetch():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                xml_data = await response.text()
                try:
                    root = ElementTree.fromstring(xml_data)
                    for i in root:
                        if i.attrib == {'ID': 'R01090B'}:
                            vunit = next(i.iter("VunitRate"))
                            vunit = float(str(vunit.text).replace(",", "."))
                            return vunit
                except XML_ERROR_SYNTAX:
                    print("Невалидный XML в ответе сервера.")
                    return 26.5
    except aiohttp.ClientError as e:
        print(f"Ошибка сети: {e}")
    except Exception as e:
        print(f"Неизвестная ошибка: {e}")

vunit = asyncio.run(fetch())


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    chat_id = message.chat.id
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    button_artist = types.KeyboardButton("BYN -> RUB")
    button_name= types.KeyboardButton("RUB -> BYN")
    markup.add(button_artist, button_name)
    text = \
f'''Текущий курс белорусского рубля: 1 BYN = {vunit} RUB
                
Напишите команду в формате 
25 бун
100 руб
                
Или выберите вариант конвертации:'''
    bot.send_message(chat_id, text, reply_markup=markup)

@bot.message_handler(func=lambda msg: msg.text in ["BYN -> RUB", "RUB -> BYN"])
def on_click(message):
    chat_id = message.chat.id
    if message.text == "BYN -> RUB":
        bot.send_message(chat_id, "Введите сумму в бунах")
        bot.register_next_step_handler(message, lambda m: convert_currency(m, "BYN_RUB"))
    elif message.text == "RUB -> BYN":
        bot.send_message(chat_id, "Введите сумму в рублях")
        bot.register_next_step_handler(message, lambda m: convert_currency(m, "RUB_BYN"))

def convert_currency(message, conversion_type):
    chat_id = message.chat.id

    try:
        value = message.text
        if "," in value:
            value = value.replace(",", ".")
        value = float(value)
        if conversion_type == "BYN_RUB":
            result = value*vunit
            bot.send_message(chat_id, f"{value} BYN = {round(result, 2)} RUB")
        elif conversion_type == "RUB_BYN":
            result = value/vunit
            bot.send_message(chat_id, f"{value} RUB = {round(result, 2)} BYN")
    except ValueError:
        bot.send_message(chat_id, "Введите число!")

@bot.message_handler(content_types=["text"])
def get_value(message):
    chat_id = message.chat.id
    value = message.text.strip().lower()
    try:
        if "бун" in value:
            value = float(value.replace("бун", ""))
            result = value * vunit
            bot.send_message(chat_id, f"{value} BYN = {round(result, 2)} RUB")
        elif "руб" in value:
            value = float(value.replace("руб", ""))
            result = value / vunit
            bot.send_message(chat_id, f"{value} RUB = {round(result, 2)} BYN")
        else:
            bot.send_message(chat_id, 'Команда должна быть в формате "(значение) бун" или "(значение) руб"!')
    except ValueError:
        bot.send_message(chat_id, 'Команда должна быть в формате "(значение) бун" или "(значение) руб"!')



# def converter(value: int):

bot.infinity_polling()
