## Tech Stack
- Python 3.11+
- FastAPI + Uvicorn
- SQLAlchemy (Async) + PostgreSQL
- Alembic (миграции)
- Pydantic Settings (конфигурация)
- Docker & Docker Compose
- SQLAdmin (админ-панель)
- Redis (опционально)

## Author
**Alen Omarov**  

# App 
APP_NAME=Note App
APP_VERSION=0.1.0
APP_DEBUG=true        # false на проде

#  Security
SECRET_KEY=KSEUtdh6od27s5hNBWyoMvpyZI7qQ07fq8eyC6HQx1eI5NY1T9v4Jcp5gc1p56Ra2nwwXKjmS85N5LSj-2py1Q
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
ADMIN_SESSION_KEY=admin_user_id

# Database (для приложения) 
# Хост db — это имя контейнера Postgres из docker-compose
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/postgres

#  Database bootstrap (для образа postgres) 
# Эти переменные читает контейнер postgres при старте
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



