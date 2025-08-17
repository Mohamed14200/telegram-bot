from telethon import TelegramClient, events
import re
import asyncio

# ===== بيانات تسجيل الدخول =====
api_id = 24700178
api_hash = '53439b01dc0a48298d1d755abc75436d'
phone_number = '+213794897379'

# ===== إعدادات القنوات =====
source_channels = [
    'zedstoreonline',
    'Aliextoday',
    'couponsb',
    'ziamoamed',
    'buyfromaliexpresss',
    'rgh2pOW9NbdhNGZk',
    'dzcouponcoins'
]

my_channel = 'best4uoffers'
forward_channels = ['aligroupedz', 'AliexpressOffers99']

extra_text = """
لاتنسوا استخدام بوت التخفيضات
https://t.me/Aliexpress_4ubot

للمزيد اشتركوا في قناتنا
https://t.me/best4uoffers
"""

bot_username = 'Aliexpress_4ubot'

client = TelegramClient('session_name', api_id, api_hash)

def extract_all_links(message):
    if not message:
        return []
    combined_text = message.raw_text or ""
    return re.findall(r'(https?://[^\s]+)', combined_text)

def extract_price(text):
    lines = text.splitlines()
    price_pattern = re.compile(r'(\$|السعر|price).{0,10}(\d+(\.\d+)?)', re.IGNORECASE)
    for line in lines:
        if price_pattern.search(line):
            return line.strip()
    return ""

def extract_intro_text_before_link(text, product_link):
    idx_link = text.find(product_link) if product_link else -1
    if idx_link == -1:
        return text.strip()
    return text[:idx_link].strip()

# تخزين الرسائل التي تنتظر رد البوت
pending_requests = {}

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    original_text = event.message.raw_text or ""
    original_media = event.message.media

    text_links = extract_all_links(event.message)
    if not text_links:
        return

    original_link = text_links[0]
    print(f"📌 الرابط الأصلي: {original_link}")

    # حفظ البيانات مؤقتًا لحين وصول رد البوت
    pending_requests[event.id] = {
        "text": original_text,
        "media": original_media,
        "original_link": original_link
    }

    await client.send_message(bot_username, original_link)

@client.on(events.NewMessage(from_users=bot_username))
async def bot_response(event):
    # نبحث عن الطلب الذي أرسل للبوت
    for msg_id, data in list(pending_requests.items()):
        links_from_bot = extract_all_links(event.message)
        if not links_from_bot:
            print("⚠️ لم يتم العثور على روابط جديدة في رد البوت.")
            return

        new_link = None
        for link in links_from_bot:
            if link.startswith("https://s.click.aliexpress.com/e/"):
                new_link = link
                break

        if not new_link:
            print("⚠️ لم يتم العثور على رابط منتج صالح في رد البوت.")
            return

        print(f"🔗 رابط التخفيض الجديد: {new_link}")

        price_text = extract_price(data["text"])
        intro_text = extract_intro_text_before_link(data["text"], data["original_link"])
        modified_text = f"{intro_text}\n\n{price_text}\n\n{new_link}\n\n{extra_text}"

        # نشر الرسالة في قناتك
        posted_message = await client.send_message(
            my_channel,
            modified_text,
            file=data["media"]  # إذا كانت الصورة مرفقة يتم إرسالها
        )

        # إعادة النشر في القنوات الأخرى
        for ch in forward_channels:
            try:
                await client.send_message(ch, modified_text, file=data["media"])
            except Exception as e:
                print(f"خطأ في إعادة النشر إلى {ch}: {e}")

        print("✅ تم النشر مع الصورة والنص")

        # حذف الطلب من القائمة
        del pending_requests[msg_id]
        break

async def main():
    await client.start(phone_number)
    print("🚀 البوت يعمل الآن...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
