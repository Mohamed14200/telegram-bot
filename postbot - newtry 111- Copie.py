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
    'buyfromaliexpresss',
    'bestdealOone',
   
    'rtdealss',
    'dzcouponcoins'
]

my_channel = 'best4uoffers'
forward_channels = ['ziamoamed','aligroupedz', 'AliexpressOffers99']

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

# 🆕 إعدادات إعادة المحاولة
MAX_RETRIES = 3
RETRY_DELAY = 60  # ثانية

def normalize_for_compare(s: str) -> str:
    """Normalize text for comparison: replace NBSP, collapse whitespace, lower-case."""
    if s is None:
        return ""
    s = s.replace('\u00A0', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()

def dedupe_consecutive_lines(text: str) -> str:
    """Remove consecutive identical lines (ignoring leading/trailing spaces)."""
    if not text:
        return text
    lines = text.splitlines()
    new_lines = []
    prev_norm = None
    for line in lines:
        norm = line.strip()
        if norm == "":
            # keep single blank lines (but avoid many in a row)
            if not new_lines or new_lines[-1].strip() != "":
                new_lines.append("")
            continue
        if prev_norm is None or norm != prev_norm:
            new_lines.append(line)
            prev_norm = norm
        else:
            continue
    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()
    return "\n".join(new_lines)

async def retry_sending(msg_id):
    """إعادة إرسال الرابط إذا لم يرد البوت خلال مدة معينة"""
    await asyncio.sleep(RETRY_DELAY)
    if msg_id in pending_requests:
        data = pending_requests[msg_id]
        retries = data.get("retries", 0)
        if retries < MAX_RETRIES:
            pending_requests[msg_id]["retries"] = retries + 1
            print(f"⏳ لم يصل رد من البوت... إعادة المحاولة رقم {retries+1}")
            await client.send_message(bot_username, data["original_link"])
            client.loop.create_task(retry_sending(msg_id))
        else:
            print("❌ تجاوز عدد محاولات إعادة الإرسال.")

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    original_text = event.message.raw_text or ""
    original_media = event.message.media

    text_links = extract_all_links(event.message)
    if not text_links:
        return

    original_link = text_links[0]
    print(f"📌 الرابط الأصلي: {original_link}")

    pending_requests[event.id] = {
        "text": original_text,
        "media": original_media,
        "original_link": original_link,
        "retries": 0
    }

    # ⏳ إضافة انتظار 8 ثواني قبل إرسال الرابط للبوت
    await asyncio.sleep(8)

    await client.send_message(bot_username, original_link)
    client.loop.create_task(retry_sending(event.id))

@client.on(events.NewMessage(from_users=bot_username))
async def bot_response(event):
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

        intro_text = extract_intro_text_before_link(data["text"], data["original_link"])
        intro_text = dedupe_consecutive_lines(intro_text)

        price_text = extract_price(data["text"])
        final_intro = intro_text
        if price_text:
            if normalize_for_compare(price_text) not in normalize_for_compare(intro_text):
                if final_intro.strip():
                    final_intro = final_intro + "\n\n" + price_text
                else:
                    final_intro = price_text

        final_intro = dedupe_consecutive_lines(final_intro)
        modified_text = f"{final_intro}\n\n{new_link}\n\n{extra_text}"

        try:
            await client.send_message(
                my_channel,
                modified_text,
                file=data["media"]
            )
        except Exception as e:
            print(f"خطأ في النشر إلى قناتك: {e}")
            del pending_requests[msg_id]
            return

        for ch in forward_channels:
            try:
                await client.send_message(ch, modified_text, file=data["media"])
            except Exception as e:
                print(f"خطأ في إعادة النشر إلى {ch}: {e}")

        print("✅ تم النشر مع الصورة والنص")
        del pending_requests[msg_id]
        break

async def print_heartbeat():
    while True:
        print("🤖 البوت يعمل بنجاح ...")
        await asyncio.sleep(600)

async def main():
    await client.start(phone_number)
    print("🚀 البوت يعمل الآن...")
    client.loop.create_task(print_heartbeat())
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
