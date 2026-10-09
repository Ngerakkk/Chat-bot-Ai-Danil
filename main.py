import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Load environment variables dari file .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Inisialisasi Gemini Client
ai_client = genai.Client(api_key=GEMINI_KEY)

# 1. ATUR PERSONA BOT DI SINI
SYSTEM_INSTRUCTION = """
Kamu adalah Danil AI, asisten pribadi cerdas yang ramah, sopan, dan sangat membantu.
Gunakan bahasa Indonesia yang santai tapi tetap profesional.
Jawablah pertanyaan pengguna dengan jelas, akurat, dan ringkas.
"""

# 2. PENYIMPANAN MEMORI PERCAKAPAN (Berdasarkan Chat ID User)
user_chats = {}


def get_user_chat(chat_id):
    """Mendapatkan atau membuat objek chat history untuk pengguna tertentu"""
    if chat_id not in user_chats:
        user_chats[chat_id] = ai_client.chats.create(
            model="gemini-3.8-flash",
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.7,
            ),
        )
    return user_chats[chat_id]


# Command /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    chat_id = update.effective_chat.id

    # Reset riwayat obrolan saat menekan /start
    user_chats[chat_id] = ai_client.chats.create(
        model="gemini-3.8-flash",
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0.7,
        ),
    )

    await update.message.reply_text(
        f"Halo {user_name}! Saya Danil AI. Ada yang bisa saya bantu hari ini?"
    )


# Command /reset (Opsional: Untuk menghapus ingatan bot jika ganti topik)
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in user_chats:
        del user_chats[chat_id]
    await update.message.reply_text(
        "Memori ingatan kita telah di-reset! Silakan mulai topik baru."
    )


# Handle Pesan Teks
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        # Ambil objek sesi chat pengguna dan kirim pesan
        chat_session = get_user_chat(chat_id)
        response = chat_session.send_message(user_text)
        reply_text = response.text
    except Exception as e:
        reply_text = f"Maaf, terjadi kesalahan: {str(e)}"

    await update.message.reply_text(reply_text)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot Danil AI (dengan memori & persona) sedang berjalan...")
    app.run_polling()