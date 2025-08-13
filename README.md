# Секретный ключ для сессий и подписи данных 
SECRET_KEY="KSEUtdh6od27s5hNBWyoMvpyZI7qQ07fq8eyC6HQx1eI5NY1T9v4Jcp5gc1p56Ra2nwwXKjmS85N5LSj-2py1Q"

# DSN для подключения backend к Postgres внутри docker-сети
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres

# Данные для контейнера Postgres (docker-compose)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=postgres

````` 
.
├─ app/
│  ├─ main.py                    # FastAPI + middleware + маршруты + setup_admin
│  ├─ admin.py                   # SQLAdmin, доступ только для is_admin
│  ├─ api/                       # ваши API-роуты
│  ├─ core/
│  │  ├─ config.py               # Pydantic Settings (SECRET_KEY, DATABASE_URL и т.д.)
│  │  └─ security.py             # hash/verify password, JWT (если используется)
│  ├─ db/
│  │  ├─ models.py               # модели User, Note, Category
│  │  └─ session.py              # async engine/session, init_db() c ретраями
│  └─ ...
├─ entrypoint.sh                 # ожидание готовности БД и запуск uvicorn
├─ docker-compose.yml
├─ Dockerfile
├─ requirements.txt
└─ README.md
````` 

2) Запусти проект 
docker compose down -v
docker compose build --no-cache
docker compose up -d
docker compose logs -f backend

Полезные URL

API ping: http://localhost:8000/ping

Swagger UI: http://localhost:8000/docs

Админ-панель SQLAdmin: http://localhost:8000/admin

Если в docker-compose.yml меняешь порт backend на хосте — подставь свой.


Админ-панель и доступ только для is_admin
В app/admin.py используется кастомный AdminAuth (sqladmin), который:

показывает форму логина /admin/login;

пускает внутрь только пользователя с is_admin=True;

кладёт admin_user_id в сессию после успешного входа;

на каждом запросе к /admin проверяет, что пользователь всё ещё админ.

В app/main.py подключён SessionMiddleware с твоим SECRET_KEY.

Чтобы зайти в админку, в БД должен существовать пользователь с is_admin = TRUE и корректным hashed_password.

При старте, если APP_DEBUG=True (или у тебя вызван init_db()), выполняется:

ожидание готовности БД (ретраи);

создание таблиц Base.metadata.create_all() (идемпотентно);

(опционально) сидер админа из .env (если включён у тебя в startup).



