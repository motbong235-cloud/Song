# 🎵 Song Search Bot

Telegram bot សម្រាប់ស្វែងរក និងទាញយកចម្រៀង MP3 ពី YouTube តាមចំណងជើង។

## របៀបដំណើរការ
1. វាយឈ្មោះចម្រៀង → bot ស្វែងរកលទ្ធផលពី YouTube (រហូតដល់ ៦ លទ្ធផល)
2. ចុចជ្រើសរើសពី inline buttons
3. bot ទាញយក audio ជា MP3 ហើយផ្ញើមកវិញ

## តម្រូវការ
- Python 3.10+
- **ffmpeg** (ត្រូវការសម្រាប់បំប្លែងទៅ MP3) — `apt install ffmpeg` (VPS) ឬតាមរយៈ Termux: `pkg install ffmpeg`

## ដំឡើង
```bash
pip install -r requirements.txt
```

## កំណត់ Token
```bash
export BOT_TOKEN="1234567890:AAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
python bot.py
```

## Deploy លើ Render
1. Push កូដទៅ GitHub repo
2. បង្កើត "Background Worker" service ថ្មីនៅ Render
3. Build command: `pip install -r requirements.txt`
4. Start command: `python bot.py`
5. **សំខាន់៖** បន្ថែម Buildpack ឬ Docker ដើម្បីឲ្យមាន `ffmpeg` — Render's default Python environment មិនមាន ffmpeg ជាមុនទេ។ ដំណោះស្រាយងាយបំផុតគឺប្រើ Docker image ដែលមាន ffmpeg ស្រាប់ (ឧ. `python:3.11-slim` + `apt-get install ffmpeg` ក្នុង Dockerfile)
6. កំណត់ Environment Variable: `BOT_TOKEN`

## Deploy លើ VPS/Termux
```bash
pkg install ffmpeg python  # Termux
pip install -r requirements.txt
export BOT_TOKEN="..."
python bot.py
```
សម្រាប់ដំណើរការជាប់រហូត អាចប្រើ `pm2`, `screen`, ឬ `systemd service`។

## កំណត់ចំណាំ
- ចម្រៀងទាញយកជា MP3 192kbps រួចលុបចោលពី server ភ្លាមៗបន្ទាប់ពីផ្ញើ (មិនរក្សាទុកអចិន្ត្រៃយ៍ទេ)
- លទ្ធផលស្វែងរកនីមួយៗ ចងជាមួយ user ជាបណ្តោះអាសន្ន — ប្រសិនបើផុតកំណត់ត្រូវស្វែងរកម្តងទៀត
- សូមគោរពច្បាប់រក្សាសិទ្ធិ (copyright) នៅពេលប្រើប្រាស់ជាមួយមាតិកា YouTube
