from telethon import TelegramClient, events
import re
import asyncio
import nest_asyncio

nest_asyncio.apply()

# ===== بيانات تسجيل الدخول =====
api_id = 24700178
api_hash = '53439b01dc0a48298d1d755abc75436d'
phone_number = '+213794897379'

# ===== إعدادات القنوات =====
source_channels = [
    'zedstoreonline',
    'Aliextoday',
    'buyfromaliexpresss',
    'dzcouponcoins',
    'bestdealOone',
    'rtdealss',
    'Aliexpress_With_Amine',
    'medaliexpress',
    'aliexstor'
]

my_channel = 'best4uoffers'
forward_channels = ['ziamoamed', 'aligroupedz', 'AliexpressOffers99']

extra_text = """
لاتنسوا استخدام بوت التخفيضات
https://t.me/Aliexpress_4ubot

للمزيد اشتركوا في قناتنا
https://t.me/best4uoffers
"""

bot_username = 'Aliexpress_4ubot'

client = TelegramClient('session_name', api_id, api_hash)

# ===== تعبيرات منتظمة =====
ALI_CLICK_FULL_RE = re.compile(r'https?://s\.click\.aliexpress\.com/e/[^\s]+', re.IGNORECASE)
ALI_CLICK_BARE_RE = re.compile(r's\.click\.aliexpress\.com/e/[^\s]+', re.IGNORECASE)

# ===== الدوال =====
def extract_all_links(message):
    if not message:
        return []
    combined_text = message.raw_text or ""
    return re.findall(r'(https?://[^\s]+)', combined_text)

def extract_aliexpress_link_pair(text):
    m1 = ALI_CLICK_FULL_RE.search(text)
    if m1:
        link = m1.group(0)
        return link, link
    
    m2 = ALI_CLICK_BARE_RE.search(text)
    if m2:
        raw_link = m2.group(0)
        normalized = 'https://' + raw_link if not raw_link.lower().startswith('http') else raw_link
        return raw_link, normalized
    
    return None, None

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

def contains_bundle_or_multiple(text):
    if re.search(r'\bbundle\b', text, re.IGNORECASE) or 'باندل' in text:
        return True
    return False

def contains_currency_discount(text):
    return 'التخفيض بالعملات' in text or 'coins discount' in text.lower()

def normalize_for_compare(s: str) -> str:
    if s is None:
        return ""
    s = s.replace('\u00A0', ' ')
    s = re.sub(r'\s+', ' ', s).strip()
    return s.lower()

def dedupe_consecutive_lines(text: str) -> str:
    if not text:
        return text
    lines = text.splitlines()
    new_lines = []
    prev_norm = None
    for line in lines:
        norm = line.strip()
        if norm == "":
            if not new_lines or new_lines[-1].strip() != "":
                new_lines.append("")
            continue
        if prev_norm is None or norm != prev_norm:
            new_lines.append(line)
            prev_norm = norm
    while new_lines and new_lines[-1].strip() == "":
        new_lines.pop()
    return "\n".join(new_lines)

# ===== تخزين الرسائل =====
pending_requests = {}
MAX_RETRIES = 3
RETRY_DELAY = 60  # ثانية

async def retry_sending(msg_id):
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

# ===== الاستماع لرسائل القنوات =====
@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    original_text = event.message.raw_text or ""
    original_media = event.message.media

    raw_link, original_link = extract_aliexpress_link_pair(original_text)
    if not original_link:
        return

    print(f"📌 الرابط الأصلي: {original_link}")

    pending_requests[event.id] = {
        "text": original_text,
        "media": original_media,
        "raw_link": raw_link,
        "original_link": original_link,
        "retries": 0
    }

    await client.send_message(bot_username, original_link)
    await asyncio.sleep(3)  # الانتظار بعد إرسال الرسالة للبوت
    client.loop.create_task(retry_sending(event.id))

# ===== رد البوت =====
@client.on(events.NewMessage(from_users=bot_username))
async def bot_response(event):
    for msg_id, data in list(pending_requests.items()):
        links_from_bot = extract_all_links(event.message)
        if not links_from_bot:
            print("⚠️ No new links found in the bot's response.")
            return

        if contains_currency_discount(data["text"]):
            chosen_link = links_from_bot[0]
        elif contains_bundle_or_multiple(data["text"]):
            chosen_link = links_from_bot[-1]
        else:
            chosen_link = links_from_bot[0]

        print(f"🔗 رابط التخفيض الجديد: {chosen_link}")

        intro_text = extract_intro_text_before_link(data["text"], data["raw_link"])
        intro_text = dedupe_consecutive_lines(intro_text)

        price_text = extract_price(data["text"])
        final_intro = intro_text
        if price_text and normalize_for_compare(price_text) not in normalize_for_compare(intro_text):
            final_intro = (final_intro + "\n\n" + price_text) if final_intro.strip() else price_text

        final_intro = dedupe_consecutive_lines(final_intro)
        modified_text = f"{final_intro}\n\n{chosen_link}\n\n{extra_text}"

        try:
            # نشر الرسالة المعدلة في قناتك
            sent_msg = await client.send_message(my_channel, modified_text, file=data["media"])
        except Exception as e:
            print(f"خطأ في النشر إلى قناتك: {e}")
            del pending_requests[msg_id]
            return

        # فوروورد من قناتك للقنوات الصغيرة
        for ch in forward_channels:
            try:
                await client.forward_messages(ch, sent_msg)
            except Exception as e:
                print(f"خطأ في إعادة التوجيه إلى {ch}: {e}")

        print("✅ تم النشر مع الصورة والنص + عمل فوروورد للقنوات الصغيرة")
        del pending_requests[msg_id]
        break

# ===== نبض الحياة =====
async def print_heartbeat():
    while True:
        print("🤖 the bot works now... ")
        await asyncio.sleep(600)

# ===== تشغيل البوت =====
async def main():
    await client.start(phone_number)
    print("🚀 the bot starts...")
    client.loop.create_task(print_heartbeat())
    await client.run_until_disconnected()

# تشغيل في Google Colab
asyncio.get_event_loop().run_until_complete(main())
