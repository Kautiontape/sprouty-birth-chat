import logging
import os

from telegram import BotCommand, Update
from telegram.constants import ChatAction, ParseMode
from telegram.ext import Application, ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from bot.chat import respond
from bot.storage import (
    generate_link_code,
    get_partner_id,
    link_partner,
    list_documents,
    load_memories,
    save_document,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = str(update.message.chat_id)
    text = update.message.text

    log.info("Message from %s: %s", chat_id, text[:80])

    try:
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await respond(chat_id, text)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
        log.info("Replied to %s", chat_id)
    except Exception:
        log.exception("Error handling message from %s", chat_id)
        await update.message.reply_text(
            "Sorry, something went wrong. Try again in a moment."
        )


async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.document:
        return

    chat_id = str(update.message.chat_id)
    doc = update.message.document
    filename = doc.file_name or "unnamed_file"

    log.info("Document from %s: %s", chat_id, filename)

    try:
        file = await doc.get_file()
        data = await file.download_as_bytearray()
        result = save_document(chat_id, filename, bytes(data))
        log.info(result)

        caption = update.message.caption or f"I just uploaded a document called {filename}"
        await update.message.chat.send_action(ChatAction.TYPING)
        reply = await respond(chat_id, caption)
        await update.message.reply_text(reply, parse_mode=ParseMode.MARKDOWN)
    except Exception:
        log.exception("Error handling document from %s", chat_id)
        await update.message.reply_text(
            "Sorry, I couldn't process that file. Try again?"
        )


async def cmd_memory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    memories = load_memories(chat_id)

    if not memories:
        await update.message.reply_text("No memories saved yet. Just chat and I'll remember the important stuff!")
        return

    lines = ["*Saved memories:*\n"]
    for key, value in memories.items():
        lines.append(f"• *{key}*: {value}")

    partner = get_partner_id(chat_id)
    if partner:
        lines.append("\n_Shared with your partner_")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_docs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    docs = list_documents(chat_id)

    if not docs:
        await update.message.reply_text("No documents uploaded yet. Send me a file anytime!")
        return

    lines = ["*Uploaded documents:*\n"]
    for name in docs:
        escaped = name.replace("_", "\\_").replace("*", "\\*").replace("[", "\\[").replace("`", "\\`")
        lines.append(f"• `{escaped}`")

    partner = get_partner_id(chat_id)
    if partner:
        lines.append("\n_Shared with your partner_")

    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = str(update.message.chat_id)
    args = context.args

    if args:
        # Linking with a code
        code = args[0].upper()
        result = link_partner(code, chat_id)
        await update.message.reply_text(result)
    else:
        # Generate a code
        code = generate_link_code(chat_id)
        await update.message.reply_text(
            f"Share this code with your partner:\n\n"
            f"*{code}*\n\n"
            f"They should send `/link {code}` to connect.\n"
            f"You'll share memories and documents once linked.",
            parse_mode=ParseMode.MARKDOWN,
        )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "*Commands:*\n\n"
        "/memory — View all saved memories\n"
        "/docs — View uploaded documents\n"
        "/link — Generate a code to link your partner\n"
        "/link CODE — Link with your partner's code\n"
        "/help — Show this message\n\n"
        "You can also just send me a file to upload a document (birth plan, notes, etc).",
        parse_mode=ParseMode.MARKDOWN,
    )


async def post_init(application: Application) -> None:
    await application.bot.set_my_commands([
        BotCommand("memory", "View all saved memories"),
        BotCommand("docs", "View uploaded documents"),
        BotCommand("link", "Link with your partner"),
        BotCommand("help", "Show available commands"),
    ])


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).post_init(post_init).build()

    app.add_handler(CommandHandler("memory", cmd_memory))
    app.add_handler(CommandHandler("docs", cmd_docs))
    app.add_handler(CommandHandler("link", cmd_link))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("start", cmd_help))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    log.info("Birth Chat bot starting")
    app.run_polling()


if __name__ == "__main__":
    main()
