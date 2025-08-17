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
    'buyfromaliexpresss'
]

my_channel = 'best4uoffers'
forward_channels = ['buyfromaliexpresss']

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

def clean_text_until_link(text, product_link):
    """
    يحتفظ بالنص حتى نهاية رابط المنتج فقط ويحذف كل شيء بعده
    """
    idx = text.find(product_link)
    if idx == -1:
        return text  # إذا لم يجد الرابط، يعيد النص كاملا
    end_idx = idx + len(product_link)
    return text[:end_idx].strip()

@client.on(events.NewMessage(chats=source_channels))
async def handler(event):
    # حفظ النص والصورة من الرسالة الأصلية
    original_text = event.message.raw_text or ""
    original_media = event.message.media

    # استخراج أول رابط من الرسالة الأصلية
    text_links = extract_all_links(event.message)
    if not text_links:
        return
    original_link = text_links[0]
    print(f"📌 الرابط الأصلي: {original_link}")

    # إرسال الرابط للبوت
    await client.send_message(bot_username, original_link)

    try:
        # انتظار رد البوت
        @client.on(events.NewMessage(from_users=bot_username))
        async def bot_response(bot_event):
            links_from_bot = extract_all_links(bot_event.message)
            if not links_from_bot:
                print("⚠️ لم يتم العثور على روابط جديدة في رد البوت.")
                return

            # تحديد الرابط الجديد حسب شروطك (يمكن تطوير هنا حسب نوع الرابط)
            new_link = links_from_bot[0]  # مثلا الرابط الأول بشكل افتراضي
            print(f"🔗 رابط التخفيض الجديد: {new_link}")

            # قص النص حتى نهاية الرابط الجديد فقط
            cleaned_text = clean_text_until_link(original_text, new_link)

            # استبدال الرابط القديم بالجديد في النص المقصوص
            modified_text = cleaned_text.replace(original_link, new_link)

            # إضافة النص الإضافي
            modified_text += "\n\n" + extra_text

            # نشر الرسالة في القناة مع الصورة الأصلية
            posted_message = await client.send_message(
                my_channel,
                modified_text,
                file=original_media
            )

            # إعادة نشر للقنوات الإضافية
            for ch in forward_channels:
                await client.forward_messages(ch, posted_message)

            print("✅ تم النشر مع الصورة والرابط الجديد")

        await asyncio.sleep(15)

    except asyncio.TimeoutError:
        print("⚠️ لم يرد البوت في الوقت المحدد.")
        return

async def main():
    await client.start(phone_number)
    print("🚀 البوت يعمل الآن...")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
