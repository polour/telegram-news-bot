import asyncio
import logging
import requests
import openai
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 🔐 اطلاعات API
TELEGRAM_BOT_TOKEN = "8128158054:AAG5Y4acYdrBT3Lgu2p0cp-crYk0H2Anpxk"
CHANNEL_ID = "@firsttnews"
OPENAI_API_KEY = "32d31caef139494eaf34536cec853989"
GNEWS_API_KEY = "cd8bac877e90fe11cb7049cd991b0468"

openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_news():
    url = f"https://gnews.io/api/v4/top-headlines?lang=fa&max=5&token={GNEWS_API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json().get("articles", [])
    except Exception as e:
        logger.error("❌ خطا در دریافت خبر: %s", e)
        return []

def summarize_text(text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": f"این خبر را به صورت کوتاه و قابل فهم خلاصه کن:\n{text}"
            }],
            max_tokens=80
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ خطای GPT: {e}"

def format_news(article):
    title = article.get("title", "")
    description = article.get("description", "")
    url = article.get("url", "")
    summary = summarize_text(description or title)
    return f"📰 {title}\n📄 خلاصه: {summary}\n🔗 {url}"

sent_messages = set()

async def send_to_telegram(bot):
    logger.info("📡 در حال دریافت اخبار از GNews...")
    news_list = fetch_news()
    for article in news_list:
        msg = format_news(article)
        if msg not in sent_messages:
            try:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg)
                sent_messages.add(msg)
                logger.info("✅ پیام ارسال شد")
            except Exception as e:
                logger.error("❌ خطا در ارسال پیام: %s", e)

async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    await send_to_telegram(bot)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_to_telegram, 'interval', minutes=5, args=[bot])
    scheduler.start()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())