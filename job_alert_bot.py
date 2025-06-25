# job_alert_bot.py

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
import requests
import json
import os
import asyncio

user_preferences = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        "👋 Welcome to Job Alert Bot!\n\n"
        "Use /setcategory to choose your job category.\n"
        "Then use /getjobs to get job listings."
    )

async def set_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    categories = [
        ["Software Dev", "Marketing", "Customer Support"],
        ["Design", "Product", "Sales"]
    ]
    await update.message.reply_text(
        "Choose a category:",
        reply_markup=ReplyKeyboardMarkup(categories, one_time_keyboard=True, resize_keyboard=True)
    )

async def save_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    category = update.message.text
    user_preferences[user_id] = category
    await update.message.reply_text(f"✅ Category saved as: {category}\nNow use /getjobs to fetch jobs.")

async def get_jobs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    category = user_preferences.get(user_id)

    if not category:
        await update.message.reply_text("❗ You haven't set a category yet. Use /setcategory")
        return

    category = category.replace(" ", "%20")
    url = f"https://services.india.gov.in/feed/rss?cat_id=2&ln=en"
    response = requests.get(url)

    if response.status_code != 200:
        await update.message.reply_text("⚠️ Failed to fetch jobs. Try again later.")
        return

    data = response.json()
    jobs = data.get("jobs", [])[:5]

    if not jobs:
        await update.message.reply_text("🚫 No jobs found in that category today.")
        return

    for job in jobs:
        message = f"📌 *{job['title']}*\nCompany: {job['company_name']}\nLocation: {job['candidate_required_location']}\n[Apply Here]({job['url']})"
        await update.message.reply_markdown(message)

def send_daily_alerts(app):
    scheduler = BackgroundScheduler()

    async def job_sender():
        for user_id in user_preferences:
            try:
                chat = await app.bot.send_message(chat_id=user_id, text="📬 Daily Job Alert:")
                dummy_update = type("Dummy", (), {"effective_user": type("User", (), {"id": user_id}), "message": chat})
                await get_jobs(dummy_update, None)
            except Exception as e:
                print(f"❗ Error sending job to {user_id}: {e}")

    def run_async_job():
        asyncio.run(job_sender())

    scheduler.add_job(run_async_job, 'interval', days=1)
    scheduler.start()

def main():
    TOKEN = os.getenv("BOT_TOKEN") or "7790659128:AAHfMZ0I3YsUqLuCk8BnM2UUPhE7k_IwiJw"

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("setcategory", set_category))
    app.add_handler(CommandHandler("getjobs", get_jobs))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_category))

    send_daily_alerts(app)
    print("🤖 Job Alert Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
