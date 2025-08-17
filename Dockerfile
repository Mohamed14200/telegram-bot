# استخدم Python الرسمي
FROM python:3.12-slim

# إعداد مجلد العمل
WORKDIR /app

# نسخ المتطلبات وتنصيبها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود كامل
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]
