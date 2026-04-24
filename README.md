# UmidjonAcademy Telegram Bot

Aiogram 3.x asosida qurilgan ta'lim Telegram boti.

## Nega Vercel emas?

Vercel serverless platforma — u Telegram botlarini qollab-quvvatlamaydi. Vercel faqat HTTP so'rovlarga javob berib o'chadi. Polling asosidagi bot uchun doimo ishlab turuvchi server kerak.

## Railway orqali bepul deploy (24/7, uxlamaydi)

### 1-qadam: Railway hisobini yarating
- railway.app ga kiring
- GitHub orqali royxatdan oting (bepul)

### 2-qadam: Loyihani GitHub ga yuklang

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/umidjonacademy.git
git push -u origin main
```

### 3-qadam: Railway da yangi loyiha yarating
1. Railway dashboard → New Project
2. Deploy from GitHub repo → repongizni tanlang
3. Railway avtomatik Dockerfile ni topib build qiladi

### 4-qadam: Environment Variables (ENV) ni kiriting
Railway dashboard → Variables bolimiga kiring:

- BOT_TOKEN = BotFather dan olingan token
- ADMIN_ID = Sizning Telegram ID raqami

### 5-qadam: Volume qoshing (muhim!)
Volumesiz bot qayta ishga tushganda barcha malumotlar ochib ketadi.

1. Railway loyiha sahifasi → + Add a service → Volume
2. Volume mount path: /data
3. Hajm: 1 GB (bepul)

Bot endi /data/edubot.db da saqlaydi.

### 6-qadam: Deploy!
Railway avtomatik deploy qiladi. Logs bolimida:

```
Bot ishga tushdi (polling mode)
Database initialized — path: /data/edubot.db
```

kabi xabarlarni korsiz.

---

## Mahalliy ishga tushirish

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env faylini ochib BOT_TOKEN va ADMIN_ID ni toldirinig
python main.py
```

---

## Loyiha tuzilmasi

```
├── main.py
├── config.py
├── database.py
├── Dockerfile
├── railway.toml
├── requirements.txt
├── .env.example
├── .gitignore
├── handlers/
│   ├── admin.py
│   ├── user.py
│   └── states.py
├── keyboards/
│   ├── admin.py
│   └── user.py
├── middlewares/
│   └── db.py
└── data/
    └── texts.py
```

---

## ENV ozgaruvchilari

| Ozgaruvchi | Majburiy | Standart | Tavsif |
|-------------|----------|----------|--------|
| BOT_TOKEN | Ha | — | Telegram bot tokeni |
| ADMIN_ID | Ha | — | Admin Telegram ID |
| DB_PATH | Yoq | /data/edubot.db | SQLite fayl yoli |
| LOG_FILE | Yoq | (console) | Log fayli yoli |

---

## Bepul platformalar taqqoslash

| Platforma | Narx | Uxlaydi? | SQLite |
|-----------|------|----------|--------|
| Railway | 5$ kredit/oy | Uxlamaydi | Volume bilan |
| Render | Bepul | 15 daqiqada uxlaydi | Disk bilan |
| Fly.io | Bepul | Uxlamaydi | Volume bilan |
| Vercel | Bepul | — | Mos emas |
