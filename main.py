import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.agent.clients.postgres import init_db
from src.agent.graph import graph
from src.agent.config import config


def get_date_context() -> str:
    """Returns current date/time context in Vietnamese."""
    now = datetime.now()
    weekdays_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]
    weekday = weekdays_vi[now.weekday()]
    return f"[Thời gian hiện tại: {weekday}, {now.strftime('%d/%m/%Y %H:%M')}]"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Per-chat conversation memory (in-memory, keyed by chat_id)
chat_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 10


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_histories[chat_id] = []
    await context.bot.send_message(
        chat_id=chat_id,
        text="Chào mừng Sếp đến với Trợ lý Cafe Nhà Cọp!\n\n"
             "Em có thể giúp Sếp quản lý:\n"
             "- Kho hàng (tồn kho, nguyên liệu)\n"
             "- Menu (món ăn, công thức, phân loại)\n"
             "- Bán hàng (ghi đơn, theo dõi đơn hàng)\n"
             "- Báo cáo (doanh thu, món chạy nhất, cảnh báo kho)\n"
             "- Kiến thức (ghi nhớ thông tin, quy trình)\n\n"
             "Sếp thử nhé: 'Cho xem menu', 'Kiểm tra kho', 'Bán 2 Bạc xỉu', 'Doanh thu hôm nay thế nào?'"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if chat_id not in chat_histories:
        chat_histories[chat_id] = []

    history = chat_histories[chat_id]
    messages = [SystemMessage(content=get_date_context())]
    for entry in history:
        messages.append(HumanMessage(content=entry["human"]))
        messages.append(AIMessage(content=entry["ai"]))
    messages.append(HumanMessage(content=user_text))

    inputs = {"messages": messages}
    final_response = ""

    try:
        result = await graph.ainvoke(inputs)
        result_messages = result["messages"]
        # Find the last AI response (skip SystemMessage, HumanMessage, and tool messages)
        for msg in reversed(result_messages):
            if isinstance(msg, (HumanMessage, SystemMessage)):
                continue
            # Check if it's an AIMessage with actual content (not just tool calls)
            if hasattr(msg, 'content') and msg.content:
                content = msg.content
                # Nếu content là list (thường gặp trong Multimodal hoặc một số version LangChain)
                if isinstance(content, list):
                    content = " ".join([str(c.get("text", c)) if isinstance(c, dict) else str(c) for c in content])
                
                # Skip if it's just the date context echoed back
                if isinstance(content, str) and content.startswith("[Thời gian hiện tại:"):
                    continue
                final_response = content
                break
        if not final_response:
            final_response = "Em không hiểu yêu cầu của Sếp. Sếp thử diễn đạt lại được không ạ?"
    except Exception as e:
        logging.error(f"Error processing message for chat {chat_id}: {e}")
        final_response = f"Đã xảy ra lỗi: {str(e)}"

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
