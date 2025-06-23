import asyncio
import logging
import requests
import feedparser
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

TELEGRAM_BOT_TOKEN = "8128158054:AAG5Y4acYdrBT3Lgu2p0cp-crYk0H2Anpxk"
CHANNEL_ID = "@firsttnews"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                image_url = None

                if 'media_content' in entry:
                    image_url = entry.media_content[0].get('url')
                elif 'media_thumbnail' in entry:
                    image_url = entry.media_thumbnail[0].get('url')
                elif 'image' in entry:
                    image_url = entry.image.get('href')
                elif 'enclosures' in entry and entry.enclosures:
                    image_url = entry.enclosures[0].get('href')

                articles.append({
                    "title": title,
                    "link": link,
                    "source": source_name,
                    "image_url": image_url
                })
        except Exception as e:
            logger.error(f"خطا در RSS ({source_name}): {e}")
    return articles

def format_article(article):
    return f"{article['source']}\n📰 {article['title']}\n🔗 {article['link']}"

def load_sent_links():
    try:
        with open("sent_links.txt", "r", encoding="utf-8") as f:
            return set(line.strip() for line in f.readlines())
    except FileNotFoundError:
        return set()

def save_sent_link(link):
    with open("sent_links.txt", "a", encoding="utf-8") as f:
        f.write(link + "\n")

async def send_to_telegram(bot):
    logger.info("📡 بررسی خبرهای جدید آغاز شد...")
    sent_links = load_sent_links()
    articles = fetch_rss_articles()
    has_new = False

    for article in articles:
        if article["link"] in sent_links:
            continue
        msg = format_article(article)
        try:
            if article.get("image_url"):
                await bot.send_photo(chat_id=CHANNEL_ID, photo=article["image_url"], caption=msg)
            else:
                await bot.send_message(chat_id=CHANNEL_ID, text=msg)
            save_sent_link(article["link"])
            logger.info("✅ پیام ارسال شد")
            has_new = True
        except Exception as e:
            logger.error("❌ خطا در ارسال پیام: %s", e)

    if not has_new:
        logger.info("📭 هیچ خبر جدیدی ارسال نشد.")

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