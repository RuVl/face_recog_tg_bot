# FaceRecog TG Bot

[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-green.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Docker](https://img.shields.io/badge/Docker-Compose-pink)](https://docs.docker.com/compose/)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17.5-orange)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7%2B-red)](https://redis.io/)

A powerful Telegram bot for face recognition in photos, built for client management in salons or services. Upload a
photo, and it detects faces using AI, matches them against database, and lets you add visits with details like names,
social media, phones, services, and media. Moderators search by ID/phone, admins manage everything—including adding
moderators and locations.
Whether you're running a beauty salon tracking repeat clients or need quick face-based lookups, this bot turns your
Telegram into a simple CRM tool.

## ✨ Features

- AI-Powered Face Recognition: Detects single faces in photos and matches them against stored encodings with high accuracy.
- Client Management: Create clients from new faces, search by ID/phone, view profiles with photo galleries.
- Visit Tracking: Add/edit visits with name, social media, phone, service type, photos, and videos.
- Role-Based Access:
  - Anyone: Check if a face exists (privacy mode: no details if multiple matches).
  - Moderator: Search faces, clients by ID/phone.
  - Admin: All features + manage moderators/locations.

- Media Handling: Supports images (JPG, PNG, HEIC) and videos; auto-converts HEIF, fixes EXIF.
- Secure Storage: Face encodings in PostgreSQL, media on Yandex Disk (or local), Redis for caching.
- Async & Scalable: Handles long-running tasks with cancellation tokens; GPU support for fast AI.
- Utility Scripts: Fill DB with sample data, convert images, process results.
- Notifications: Alerts admins on new clients or unmatched faces.

## 🛠 Tech Stack

| Category          | Technologies & Versions                          | Purpose |
|-------------------|--------------------------------------------------|---------|
| **Bot Framework** | aiogram 3.21.0                                   | Async Telegram API handling, FSM states, routers. |
| **Face Recognition** | DeepFace 0.0.95 (Facenet512 model, RetinaFace backend) | Face detection & embedding; cosine similarity matching. |
| **Database**      | PostgreSQL 15+ with SQLAlchemy 2.0.42, asyncpg 0.30.0, Alembic 1.16.4 | ORM, async queries, migrations for clients/visits/images. |
| **Caching**       | Redis 7.4.5                                      | Session storage, rate limiting. |
| **Image/Video Processing** | Pillow 11.3.0, pillow-heif 1.1.0, numpy 2.1.3 | Image loading, conversion (HEIC→JPG), encoding extraction. |
| **File Storage**  | yadisk 3.4.0 (Yandex Disk)                       | Cloud upload for media; local fallback. |
| **Utils**         | phonenumbers 9.0.11, protobuf/grpcio 4.25.3/1.62.2 | Phone validation, serialization. |
| **Deployment**    | Docker Compose (NVIDIA runtime)                  | GPU-accelerated containers for bot, DB, Redis. |
| **Testing/Dev**   | tf-keras 2.19.0 (for DeepFace)                   | Model inference; scripts for DB filling. |

Dependencies managed via `pip` and `requirements.txt`. No external installs needed beyond setup.

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (with NVIDIA Docker for GPU acceleration - optional but recommended for DeepFace speed).
- Python 3.12+ (for local dev).
- Telegram Bot Token (create via [@BotFather](https://t.me/botfather)).
- PostgreSQL/Redis creds (in `.env`).
- Yandex Disk OAuth token (for video upload; set `CLOUD_STORAGE_TOKEN` in `.env`) - optional.
  - Imgur API token (for photo upload; set `IM_HOST_TOKEN` in `.env`) - optional.
- NVIDIA GPU (if using GPU mode; set in `docker-compose.yaml`).


### Folder Structure

```
face_recog_tg_bot/
├── LICENSE                  # GPL v3 license
├── docker-compose.yaml      # Orchestrates bot, DB, cache services
├── postgres/                # PostgreSQL service
│   ├── .env.dist            # Environment variables template
│   ├── Dockerfile           # Database container build
│   ├── backup.sh            # Backup database script
│   └── cronjob              # Cron job for backup database
├── redis/                   # Redis service
│   └── .env.dist
└── telegram_bot/            # Main application
    ├── .env.dist            # Environment variables template
    ├── Dockerfile           # Bot container build
    ├── alembic.ini          # DB migration config
    ├── requirements.txt     # Dependencies (to be populated)
    ├── run.py               # Entry point (to be implemented)
    ├── scripts.py           # Utility scripts
    ├── scripts/             # Additional scripts dir
    ├── tests/               # Test suite
    └── core/                # Bot logic
        ├── bots.py          # Bot and dispatcher setup
        ├── config.py        # App configuration
        ├── env.py           # Alembic env
        ├── main.py          # Core bot runner
        ├── callback_factory/ # Callback query handlers
        ├── cancel_token/    # Cancellation logic
        ├── cloud_storage/   # Cloud file storage
        ├── database/        # DB models and sessions
        ├── face_recognition/ # Face detection/encoding logic
        │   ├── main.py
        │   └── represent_example.json  # Example data
        ├── filters/         # Custom filters
        ├── handlers/        # Message/command handlers
        │   ├── admin/       # Admin handlers
        │   ├── anyone.py    # Public handlers
        │   ├── main.py
        │   ├── moderator.py # Moderator handlers
        │   ├── shared/      # Shared handlers
        │   └── utils.py
        ├── image_hosting/   # Photo upload logic
        ├── json_classes/    # Data classes
        ├── keyboards/       # Inline keyboards
        ├── middlewares/     # Request middlewares
        ├── misc/            # Utilities
        └── state_machines/  # FSM states
            └── text/        # Text resources
```

### Installation
1. Clone the repo:
   ```
   git clone https://github.com/RuVl/face_recog_tg_bot.git
   cd face_recog_tg_bot
   ```

2. Configure environment (copy templates and edit):
   ```
   cp telegram_bot/.env.dist telegram_bot/.env
   cp postgres/.env.dist postgres/.env
   cp redis/.env.dist redis/.env
   ```
   Key vars in `telegram_bot/.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token
   DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/dbname
   REDIS_URL=redis://redis:6379
   IM_HOST_TOKEN=your_yadisk_oauth_token  # Or 'no-need' for local
   PHONE_NUMBER_REGION=RU  # For phone parsing
   ADMIN_GROUP_ID=-1001234567890  # Your admin chat ID
   BACKEND=retinaface
   MODEL=Facenet512
   DISTANCE_METRIC=cosine
   ```
   Edit `postgres/.env` for DB user/pass, `redis/.env` for Redis config.

3. Build & run with Docker (GPU-enabled):
   ```
   docker-compose up --build
   ```
    - Bot runs on container `facebot`.
    - Volumes: Persistent DB (`facebot-postgres`), Redis (`facebot-redis`), media (`./telegram_bot/media`).
    - Exposes: Postgres (5432), Redis (6379) internally.
    - Healthcheck: Postgres readiness.

## 📖 Usage
Interact via private messages. Bot uses FSM for multi-step flows.

### Commands & Flows
- **/start**: Welcome menu (role-based).
    - **Anyone**: "Проверить в базе" → Upload photo → "Лицо найдено/не найдено" (ID if unique match).
    - **Moderator**: "Проверить в базе" (face search), "Найти по id", "Найти по тел номеру".
    - **Admin**: All + "Меню админа" (add/edit moderators, locations).

### Example: Face Recognition (Moderator Flow)
1. `/start` → "Проверить в базе".
2. Upload photo → Bot: "Обнаружено 1 лицо! Поиск совпадений...".
3. If match: Shows client gallery, ID, visits. Buttons: "Добавить визит" / "Удалить".
4. If no match: "Нет в базе!" → "Добавить нового?" → Да → Creates client, notifies admins.
5. Add visit: Name → Social → Phone → Service → Photos/Videos.

### Example: Add Visit
- After match: "Добавить визит" → Inline menu: Name, Social Media, Phone, Service, Photos, Videos.
- Upload media: Supports docs/videos up to 20MB; auto-processes.

### Privacy Notes
- Public mode: No details if >1 match ("Конфиденциальность 😟").
- Tokens: Cancels long tasks (e.g., upload) via "Отмена".
- Admins get notifications for new clients/unmatched faces.

## 🧠 How It Works
1. **Photo Upload**: aiogram router (`handlers/anyone.py`, `recognizer.py`) downloads to temp dir (`TEMP_DIR`), validates (single face, <20MB).
2. **Detection**: DeepFace extracts embedding (128D vector) via `represent()` with RetinaFace; filters confidence >0.75.
3. **Matching**: Compares vs. all clients' encodings using cosine distance < threshold (from DeepFace).
4. **DB Ops**: SQLAlchemy async session queries `Client` model (face_encoding JSONB, profile_picture Image rel).
5. **Storage**: Media to Yandex Disk (`cloud_storage/`); local fallback in `./media`.
6. **Response**: Edits message with gallery (`InputMediaPhoto`), inline keyboards (`paginate` for lists).
7. **Cleanup**: Deletes temp files, cancels tokens (`clearing.py`).

## 🔧 Customization
- **Thresholds**: Edit `core/config.py` (e.g., `DISTANCE_METRIC='euclidean'`).
- **Models**: Swap in `config.py` (e.g., MODEL='VGG-Face').
- **Storage**: Replace Yandex Disk in `core/cloud_storage/main.py`.
- **Roles**: Add users via admin menu; DB models in `core/database/models/`.
- **Scripts**: Extend `scripts/fill_database.py` for bulk imports.

## 📄 License
GNU General Public License v3.0. See [LICENSE](LICENSE) for details.
