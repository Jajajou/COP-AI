import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage, AIMessage

from src.agent.clients.postgres import init_db
from src.agent.graph import graph
from src.agent.config import config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Per-chat conversation memory (in-memory, keyed by chat_id)
chat_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 20


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    await context.bot.send_message(
        chat_id=chat_id,
        text="Welcome to your AI Coffee Shop Assistant!\n\n"
             "I can help you manage:\n"
             "- Inventory (stock, ingredients)\n"
             "- Menu (items, recipes, categories)\n"
             "- Sales (sell items, track orders)\n"
             "- Reports (revenue, top sellers, stock alerts)\n"
             "- Knowledge (teach me facts, procedures)\n\n"
             "Try: 'Show menu', 'Check stock', 'Sell 2 Lattes', 'Show daily revenue'"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    history = chat_histories[chat_id]
    messages = []
    for entry in history:
        messages.append(HumanMessage(content=entry["human"]))
        messages.append(AIMessage(content=entry["ai"]))
    messages.append(HumanMessage(content=user_text))

    inputs = {"messages": messages}
    final_response = ""

    try:
        result = await graph.ainvoke(inputs)
        result_messages = result["messages"]
        for msg in reversed(result_messages):
            if not isinstance(msg, HumanMessage):
                final_response = msg.content
                break
        if not final_response:
            final_response = "I'm not sure how to respond to that."
    except Exception as e:
        logging.error(f"Error processing message for chat {chat_id}: {e}")
        final_response = f"An error occurred: {str(e)}"

    if not final_response:
        final_response = "Task completed (no output)."

    chat_histories[chat_id].append({"human": user_text, "ai": final_response})
    if len(chat_histories[chat_id]) > MAX_HISTORY:
        chat_histories[chat_id] = chat_histories[chat_id][-MAX_HISTORY:]

    await context.bot.send_message(chat_id=chat_id, text=final_response)


if __name__ == "__main__":
    try:
        config.validate()
    except ValueError as e:
        logging.error(f"Configuration Error: {e}")
        exit(1)

    init_db()
    logging.info("Database initialized.")

    application = ApplicationBuilder().token(config.TELEGRAM_TOKEN).build()

    start_handler = CommandHandler('start', start)
    message_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)

    application.add_handler(start_handler)
    application.add_handler(message_handler)

    logging.info("Bot is running...")
    application.run_polling()
