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

## ដោះស្រាយបញ្ហា "រកអត់ឃើញលទ្ធផលទាំងអស់"
YouTube ផ្លាស់ប្តូរប្រព័ន្ធជាញឹកញាប់ ដែលធ្វើឲ្យកំណែ `yt-dlp` ចាស់លែងដំណើរការ។ ប្រសិនបើ search មិនដែលរកឃើញអ្វីសោះ សូមព្យាយាមតាមលំដាប់នេះ៖
1. **Upgrade yt-dlp ជាមុនសិន** (មូលហេតុទូទៅបំផុត)៖
   ```bash
   pip install -U yt-dlp
   ```
2. ពិនិត្យ log terminal នៅពេល error កើតឡើង — bot.py បាន log ចំនួន entries ដែលរកឃើញឲ្យឃើញរាល់ពេល ដើម្បីជួយ debug
3. ប្រសិនបើដំណើរការលើ VPS/Render ហើយនៅតែអត់ឃើញ អាចជាដោយ IP របស់ server ត្រូវ YouTube blocked — ព្យាយាមផ្លាស់ប្តូរ `player_client` ក្នុង `bot.py` (បច្ចុប្បន្នកំណត់ `["android", "web"]`) ឬបន្ថែម cookies ពី browser ដោយប្រើ `cookiefile` option
4. ប្រសិនបើ error ជាក់លាក់លេចឡើងក្នុង Telegram message ខ្លួនឯង (ដូចជា `❌ ស្វែងរកមិនបានទេ៖ ...`) នោះជាសារ error ពិតប្រាកដពី yt-dlp — ចម្លងវាមកសួរបន្ថែមបាន

## ដោះស្រាយ "Sign in to confirm you're not a bot"
YouTube ចាប់ផ្តើម block ការស្នើសុំពី server (VPS/Render) ដែលមិនមាន cookies ចូល account។ មានវិធីពីរ៖

### វិធីទី១ (ណែនាំ): PO Token Provider — មិនចាំបាច់ login account
ប្រើ [bgutil-ytdlp-pot-provider](https://github.com/Brainicism/bgutil-ytdlp-pot-provider) ជា server ដាច់ដោយឡែក ដែលបង្កើត token ស្វ័យប្រវត្តិ។

**ជាមួយ Docker Compose (ងាយបំផុត)** — Dockerfile និង docker-compose.yml បានរៀបចំរួចហើយ:
```bash
export BOT_TOKEN="your_telegram_bot_token"
docker compose up -d
```
នេះនឹង start ទាំង `pot-provider` service និង `song-search-bot` service ព្រមគ្នា ភ្ជាប់គ្នាដោយស្វ័យប្រវត្តិ។

**ដោយមិនប្រើ Docker** (ដំណើរការដោយដៃលើ VPS/Termux):
```bash
# 1. Run pot provider server (ត្រូវការ Node.js)
npx bgutil-ytdlp-pot-provider

# 2. កំណត់ URL ឲ្យ bot ដឹង (default port 4416)
export POT_PROVIDER_URL="http://127.0.0.1:4416"

# 3. Run bot
export BOT_TOKEN="..."
python bot.py
```

**Deploy លើ Render**: បង្កើត service ពីរដាច់ពីគ្នា — មួយសម្រាប់ `pot-provider` (Docker image `brainicism/bgutil-ytdlp-pot-provider`), មួយសម្រាប់ bot ខ្លួនឯង ដោយកំណត់ `POT_PROVIDER_URL` ចង្អុលទៅ internal URL របស់ pot-provider service (Render's private networking)។

### វិធីទី២: Cookies ពី browser (ជម្រើសបម្រុង)
1. ដំឡើង extension "Get cookies.txt LOCALLY" (Chrome/Firefox)
2. ចូល youtube.com ខណៈ login ស្រាប់ → export ជា `cookies.txt`
3. Upload ទៅ server ក្បែរ `bot.py` → `export COOKIES_FILE="/path/to/cookies.txt"`

⚠️ cookies.txt មានសិទ្ធិចូល account YouTube — កុំចែករំលែក ឬដាក់ក្នុង public repo។ គួរប្រើ account បន្ទាប់បន្សំ។

*អាចប្រើទាំងពីរវិធីព្រមគ្នាបាន (PO token + cookies) សម្រាប់ភាពស្ថិរភាពខ្ពស់បំផុត។*

## កំណត់ចំណាំ
- ចម្រៀងទាញយកជា MP3 192kbps រួចលុបចោលពី server ភ្លាមៗបន្ទាប់ពីផ្ញើ (មិនរក្សាទុកអចិន្ត្រៃយ៍ទេ)
- លទ្ធផលស្វែងរកនីមួយៗ ចងជាមួយ user ជាបណ្តោះអាសន្ន — ប្រសិនបើផុតកំណត់ត្រូវស្វែងរកម្តងទៀត
- សូមគោរពច្បាប់រក្សាសិទ្ធិ (copyright) នៅពេលប្រើប្រាស់ជាមួយមាតិកា YouTube
