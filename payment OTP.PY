import subprocess
import json
import os
import random
import time
import threading
import requests
from flask import Flask, jsonify, request
from telegram import Update, LabeledPrice
from telegram.ext import Updater, CommandHandler, CallbackContext, PreCheckoutQueryHandler, MessageHandler, Filters

# Replace with your bot token and admin ID
TELEGRAM_BOT_TOKEN = "7826363032:AAGMe8Th8Du4ewXciFR-uaYn1udNLPUevDM"
PAYMENT_PROVIDER_TOKEN = "https://imgur.com/a/i6Fz57I"  # From Stripe, PayPal, etc.
ADMIN_ID = 7509496491  # Replace with your Telegram user ID
OTP_PRICE = 12.00  # Price in USD or your currency

# Store OTPs and payments
otp_storage = {user.txt}
payment_storage = {payment.txt}

app = Flask(__name__)

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def start(update: Update, context: CallbackContext):
    """Start command"""
    update.message.reply_text("Welcome to OTP Bot!\nUse /buyotp to purchase an OTP.")

def buy_otp(update: Update, context: CallbackContext):
    """Initiate OTP purchase"""
    chat_id = update.message.chat_id

    title = "OTP Purchase"
    description = "Buy a one-time password (OTP) for verification."
    payload = f"user_{chat_id}_otp"
    currency = "USD"
    price = int(OTP_PRICE * 100)  # Convert to smallest unit (cents)

    prices = [LabeledPrice(title, price)]
    
    context.bot.send_invoice(
        chat_id, title, description, payload, PAYMENT_PROVIDER_TOKEN, currency, prices
    )

def precheckout_callback(update: Update, context: CallbackContext):
    """Confirm payment before finalizing"""
    query = update.pre_checkout_query
    if query.invoice_payload.startswith("user_"):
        query.answer(ok=True)
    else:
        query.answer(ok=False, error_message="Payment failed. Try again.")

def successful_payment(update: Update, context: CallbackContext):
    """Handle successful payment and generate OTP"""
    chat_id = update.message.chat_id

    otp = generate_otp()
    otp_storage[chat_id] = {'otp': otp, 'timestamp': time.time()}

    update.message.reply_text(f"✅ Payment successful! Your OTP: {otp} (Valid for 5 minutes)")

    # Notify admin
    context.bot.send_message(ADMIN_ID, f"🔔 New OTP purchase by user {chat_id}: {otp}")

def verify_otp(update: Update, context: CallbackContext):
    """Verify OTP"""
    user_id = update.message.chat_id
    args = context.args

    if not args:
        update.message.reply_text("Usage: /verifyotp <your_otp>")
        return

    entered_otp = args[0]

    if user_id not in otp_storage:
        update.message.reply_text("No OTP found! Use /buyotp first.")
        return

    stored_data = otp_storage[user_id]

    if time.time() - stored_data['timestamp'] > 300:  # 5-minute expiry
        del otp_storage[user_id]
        update.message.reply_text("OTP expired! Buy a new one.")
        return

    if stored_data['otp'] == entered_otp:
        del otp_storage[user_id]
        update.message.reply_text("✅ OTP Verified Successfully!")
    else:
        update.message.reply_text("❌ Invalid OTP. Try again!")

@app.route('/admin/otps', methods=['GET'])
def admin_otp_panel():
    """Admin panel to view OTP purchases"""
    return jsonify({str(user_id): data['otp'] for user_id, data in otp_storage.items()})

def run_flask():
    """Run Flask in a separate thread"""
    app.run(host="0.0.0.0", port=5000)

def main():
    """Run the Telegram bot"""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("buyotp", buy_otp))
    dp.add_handler(CommandHandler("verifyotp", verify_otp, pass_args=True))
    dp.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    dp.add_handler(MessageHandler(Filters.successful_payment, successful_payment))

    threading.Thread(target=run_flask).start()

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
