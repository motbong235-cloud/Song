"""
🎵 Song Search Bot — ស្វែងរក និងទាញយកចម្រៀងពី YouTube តាមចំណងជើង
Requirements: python-telegram-bot>=20.0, yt-dlp

Run:
    pip install -r requirements.txt
    export BOT_TOKEN="your_token_here"
    python bot.py
"""

import os
import logging
import asyncio
from pathlib import Path

import yt_dlp
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode, ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ─────────────────────────────
# ការកំណត់
# ─────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "PUT_YOUR_TOKEN_HERE")
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)
MAX_RESULTS = 6  # ចំនួនលទ្ធផលស្វែងរកអតិបរមា

# ផ្លូវទៅ cookies.txt (Netscape format) — ត្រូវការនៅពេល YouTube ស្នើសុំ "Sign in to confirm you're not a bot"
COOKIES_FILE = os.environ.get("COOKIES_FILE", "").strip() or None

# PO Token provider (bgutil-ytdlp-pot-provider) — ជម្រើសជំនួស cookies
# ត្រូវរត់ provider server ដាច់ដោយឡែក (Node.js/Docker) — មើល README
POT_PROVIDER_URL = os.environ.get("POT_PROVIDER_URL", "").strip() or None


def _base_ydl_opts() -> dict:
    extractor_args = {"youtube": {"player_client": ["android", "web"]}}
    if POT_PROVIDER_URL:
        extractor_args["youtubepot-bgutilhttp"] = {"base_url": [POT_PROVIDER_URL]}

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extractor_args": extractor_args,
    }
    if COOKIES_FILE and Path(COOKIES_FILE).exists():
        opts["cookiefile"] = COOKIES_FILE
    return opts

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ទុកលទ្ធផលស្វែងរកបណ្តោះអាសន្នតាម user (in-memory)
search_cache: dict[int, list[dict]] = {}


# ─────────────────────────────
# YouTube search / download (yt-dlp)
# ─────────────────────────────
def yt_search(query: str, limit: int = MAX_RESULTS) -> list[dict]:
    ydl_opts = {
        **_base_ydl_opts(),
        "extract_flat": True,
        "skip_download": True,
    }
    search_query = f"ytsearch{limit}:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(search_query, download=False)
        entries = info.get("entries", []) if info else []
        logger.info("yt_search('%s') → %d entries raw", query, len(entries))

    results = []
    for e in entries:
        if not e:
            continue
        duration = e.get("duration") or 0
        mins, secs = divmod(int(duration), 60)
        results.append(
            {
                "id": e.get("id"),
                "title": e.get("title", "គ្មានចំណងជើង"),
                "uploader": e.get("uploader", "N/A"),
                "duration": f"{mins}:{secs:02d}" if duration else "N/A",
                "url": f"https://www.youtube.com/watch?v={e.get('id')}",
            }
        )
    return results


def yt_download_mp3(video_url: str, out_path: Path) -> Path:
    ydl_opts = {
        **_base_ydl_opts(),
        "format": "bestaudio/best",
        "outtmpl": str(out_path / "%(id)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        file_id = info.get("id")
        return out_path / f"{file_id}.mp3"


# ─────────────────────────────
# Handlers
# ─────────────────────────────
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 *សូមស្វាគមន៍មកកាន់ Song Search Bot*\n\n"
        "វាយឈ្មោះចម្រៀង ឬចំណងជើងដែលអ្នកចង់ស្វែងរក ខ្ញុំនឹងស្វែងរកឱ្យពី YouTube!\n\n"
        "ឧទាហរណ៍៖ `ភ្លៀងធ្លាក់`",
        parse_mode=ParseMode.MARKDOWN,
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *របៀបប្រើប្រាស់*\n\n"
        "/start — ចាប់ផ្តើម\n"
        "វាយឈ្មោះចម្រៀង → ជ្រើសរើសពីលទ្ធផល → ទទួល MP3\n",
        parse_mode=ParseMode.MARKDOWN,
    )


async def search_song(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.message.text.strip()
    if not query:
        return

    msg = await update.message.reply_text(f"🔍 កំពុងស្វែងរក៖ *{query}*...", parse_mode=ParseMode.MARKDOWN)
    await update.message.chat.send_action(ChatAction.TYPING)

    try:
        results = await asyncio.to_thread(yt_search, query)
    except Exception as e:
        logger.exception("Search failed")
        await msg.edit_text(f"❌ ស្វែងរកមិនបានទេ៖ {e}")
        return

    if not results:
        await msg.edit_text("😔 រកមិនឃើញចម្រៀងដែលត្រូវនឹងចំណងជើងនេះទេ។")
        return

    user_id = update.effective_user.id
    search_cache[user_id] = results

    buttons = []
    for idx, r in enumerate(results):
        label = f"{r['title'][:45]} ({r['duration']})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"dl:{idx}")])

    await msg.edit_text(
        f"🔎 លទ្ធផលសម្រាប់៖ *{query}*\nសូមជ្រើសរើសចម្រៀង៖",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    results = search_cache.get(user_id)
    if not results:
        await query.edit_message_text("⚠️ សម័យស្វែងរកបានផុតកំណត់ សូមស្វែងរកម្តងទៀត។")
        return

    try:
        idx = int(query.data.split(":")[1])
        song = results[idx]
    except (IndexError, ValueError):
        await query.edit_message_text("⚠️ មានបញ្ហា សូមព្យាយាមម្តងទៀត។")
        return

    await query.edit_message_text(f"⬇️ កំពុងទាញយក៖ *{song['title']}*...", parse_mode=ParseMode.MARKDOWN)
    await query.message.chat.send_action(ChatAction.UPLOAD_VOICE)

    try:
        file_path = await asyncio.to_thread(yt_download_mp3, song["url"], DOWNLOAD_DIR)
        with open(file_path, "rb") as audio_file:
            await query.message.chat.send_audio(
                audio=audio_file,
                title=song["title"],
                performer=song["uploader"],
                caption=f"🎶 {song['title']}",
            )
        await query.edit_message_text(f"✅ បានផ្ញើ៖ *{song['title']}*", parse_mode=ParseMode.MARKDOWN)
    except Exception as e:
        logger.exception("Download failed")
        await query.edit_message_text(f"❌ ទាញយកមិនបានទេ៖ {e}")
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


def main():
    if BOT_TOKEN == "PUT_YOUR_TOKEN_HERE":
        raise SystemExit("❌ សូមកំណត់ BOT_TOKEN (environment variable) មុននឹងចាប់ផ្តើម bot!")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CallbackQueryHandler(handle_download_callback, pattern=r"^dl:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search_song))

    logger.info("🎵 Song Search Bot កំពុងដំណើរការ...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
