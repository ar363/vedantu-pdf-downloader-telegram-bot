import os
import re
import telebot
import requests
from slugify import slugify
from bs4 import BeautifulSoup
from flask import Flask, request

heroku_app_name = os.environ.get('HEROKU_APP_NAME')
token = os.environ['TELEGRAM_TOKEN']

bot = telebot.TeleBot(token, parse_mode='HTML')
server = Flask(__name__)

welcome_message = """
<b>Vedantu PDF Download Bot</b>

<i>How to Use?</i>

Paste a valid Vedantu page URL that contains the <i>"Download PDF"</i> option and begins with <i>https://www.vedantu.com/</i>

Done! You would recieve the PDF file. No registration to Vedantu required.

View the code here: https://github.com/ar363/vedantu-pdf-downloader-telegram-bot
"""

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    global welcome_message
    bot.reply_to(message, welcome_message)

@bot.message_handler(regexp='^https\:\/\/www\.vedantu\.com\/.*?$')
def get_pdf_url(message):
    webpage_text = requests.get(message.text).text.replace('\n', '')
    pdf_link_search = re.search(r'var categoryDownloadLink = \"(.*?)\";', webpage_text)
    if pdf_link_search is None:
        bot.reply_to(message, 'No PDF link found. Please check the entered url has a \"Download PDF\" button')
    else:
        pdf_url = pdf_link_search.groups(1)[0]
        soup = BeautifulSoup(webpage_text, 'html.parser')
        title = soup.find('title').text
        bot.send_document(message.chat.id, pdf_url, reply_to_message_id=message.id, caption=title)

@bot.message_handler(func=lambda m: True)
def catch_all(message):
    bot.reply_to(message, 'Please enter a valid URL that begins with https://www.vedantu.com/')

@server.route(f'/{token}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return ':)', 200

@server.route(f'/{token}/resetWebhookUrl')
def reset_webhook_url():
    global heroku_app_name
    global token
    bot.remove_webhook()
    bot.set_webhook(url=f'https://{heroku_app_name}.herokuapp.com/{token}')
    return 'done', 200

@server.route('/')
def index():
    return '<h1><a href="https://github.com/ar363/vedantu-pdf-downloader-telegram-bot">Bot is Up</a></h1>'

if __name__ == '__main__':
    if 'DYNO' in os.environ: # which means we are running in heroku production
        server.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
    else:
        bot.polling()
