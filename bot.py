import asyncio
import logging
import requests
import openai
import feedparser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TELEGRAM_BOT_TOKEN = "8128158054:AAG5Y4acYdrBT3Lgu2p0cp-crYk0H2Anpxk"
CHANNEL_ID = "@firsttnews"
OPENAI_API_KEY = "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"  # ← جایگزین شود با کلید معتبر
openai.api_key = OPENAI_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# منابع خبری با نام + ایموجی
RSS_FEEDS = {
    "https://www.isna.ir/rss": ("🟢 ایسنا",),
    "https://www.farsnews.ir/rss": ("🔴 فارس‌نیوز",),
    "https://mehrnews.com/rss": ("🟠 مهر",),
    "https://www.bbc.com/persian/index.xml": ("🟦 BBC فارسی",),
    "https://www.iranintl.com/fa/rss": ("🟥 ایران اینترنشنال",),
}

def fetch_rss_articles():
    articles = []
    for feed_url, (source_name,) in RSS_FEEDS.items():
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:3]:
                title = entry.title
                link = entry.link
                description = getattr(entry, 'description', '')
                articles.append({
                    "title": title,
                    "link": link,
                    "description": description,
                    "source": source_name
                })
        except Exception as e:
            logger.error(f"خطا در RSS ({source_name}): {e}")
    return articles

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

def format_article(article):
    summary = summarize_text(article["description"] or article["title"])
    return f"{article['source']}\n📰 {article['title']}\n📄 خلاصه: {summary}\n🔗 {article['link']}"

sent_messages = set()

async def send_to_telegram(bot):
    logger.info("📡 در حال دریافت اخبار از منابع...")
    articles = fetch_rss_articles()
    for article in articles:
        msg = format_article(article)
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