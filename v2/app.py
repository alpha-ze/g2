import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from logic import handle_message
from config import TELEGRAM_BOT_TOKEN

# Create uploads folder if not exists
os.makedirs("uploads", exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    # Optional: reset state on /start
    from logic import clear_state
    clear_state(chat_id)

    reply = (
        "Welcome to Grievance Redressal System\n"
        "1. Register Grievance\n"
        "2. Track Status\n\n"
        "You can also send an image as part of your grievance."
    )
    await update.message.reply_text(reply)


async def handle_message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.message.chat_id)

    # 🖼 IMAGE MESSAGE
    if update.message.photo:
        photo = update.message.photo[-1]  # highest resolution
        file = await photo.get_file()

        file_path = f"uploads/{chat_id}_{photo.file_unique_id}.jpg"
        await file.download_to_drive(file_path)

        reply = handle_message(chat_id, "[IMAGE]", image_path=file_path)
        await update.message.reply_text(reply)
        return

    # 📝 TEXT MESSAGE
    if update.message.text:
        user_message = update.message.text.strip()
        reply = handle_message(chat_id, user_message)
        await update.message.reply_text(reply)


def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message_router))

    print("Telegram bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
