import threading
import queue
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters, Application

import config
from utils import call_luma_api_text_to_video

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

task_queue = queue.Queue()


async def three_d_long_running_task(context: ContextTypes.DEFAULT_TYPE, chat_id: int | str, prompt: str):
    video_urls, status = await call_luma_api_text_to_video(prompt=prompt)
    if status:
        await context.bot.send_video(chat_id=chat_id, video=video_urls[0])
    else:
        await context.bot.send_message(chat_id=chat_id, text="We are facing an issue generating 3D video at this moment.")


def process_queue(loop, context: ContextTypes.DEFAULT_TYPE):
    while not task_queue.empty():
        chat_id, task_type, prompt = task_queue.get()
        if task_type == "3d":
            asyncio.run_coroutine_threadsafe(
                three_d_long_running_task(context, chat_id, prompt), loop)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Help", callback_data="help")],
        [InlineKeyboardButton("Send Prompt", callback_data="text_to_3d")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Welcome! Choose an option:", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("This bot helps you generate 3D videos from text prompts. Use /send_prompt to get started!")


async def text_to_3d(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please provide a prompt to generate a 3D image.")
    context.user_data["awaiting_3d_prompt"] = True


async def handle_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    prompt = update.message.text
    if context.user_data.get("awaiting_3d_prompt"):
        await update.message.reply_text("Generating a 3D image, it may take up to 6 minutes.")
        context.user_data["awaiting_3d_prompt"] = False
        task_queue.put((chat_id, "3d", prompt))
        loop = asyncio.get_running_loop()
        threading.Thread(target=process_queue, args=(loop, context)).start()


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "help":
        await help_command(query, context)
    elif query.data == "text_to_3d":
        await text_to_3d(query, context)


async def post_init(application: Application):
    # Configure commands in the bot menu
    await application.bot.set_my_commands([
        ("help", "Get help information"),
        ("send_prompt", "Generate a 3D image from a text prompt"),
    ])


def main():
    application = ApplicationBuilder().token(
        config.TELEGRAM_BOT_TOKEN).post_init(post_init=post_init).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("send_prompt", text_to_3d))

    application.add_handler(CallbackQueryHandler(button_handler))

    application.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND, handle_prompt))

    application.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
