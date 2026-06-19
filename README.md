# Glory Days Past

An online antiques shop built with Django. This is an early skeleton: a
placeholder home page and a contact page. No payments or deployment config yet.

## Tech

- Python 3.12+
- Django 6.0
- [django-environ](https://django-environ.readthedocs.io/) for environment-based settings

## Project layout

```
antiques-website/
├── config/          # project package (settings, urls, wsgi, asgi)
├── shop/            # the shop app (views, urls)
├── templates/       # base.html + shop/ page templates
├── static/css/      # styles
├── .env             # local secrets (gitignored)
├── .env.example     # template to copy into .env
└── requirements.txt
```

## Setup

> On this Windows machine the bare `python` command resolves to the Microsoft
> Store stub. Use the real interpreter to create the venv, then use the venv's
> Python for everything else.

```powershell
# 1. Create a virtual environment
& "C:\Users\jason\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv

# 2. Install dependencies
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Configure environment
Copy-Item .env.example .env
# Edit .env and set a real SECRET_KEY (and DEBUG=True for local dev).
# Generate a key:
.\.venv\Scripts\python.exe -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# 4. Apply migrations
.\.venv\Scripts\python.exe manage.py migrate

# 5. Run the development server
.\.venv\Scripts\python.exe manage.py runserver
```

Then visit:

- http://127.0.0.1:8000/ — home page
- http://127.0.0.1:8000/contact/ — contact page

## Environment variables

| Variable        | Required | Default                  | Notes                                |
|-----------------|----------|--------------------------|--------------------------------------|
| `SECRET_KEY`    | yes      | —                        | Django secret key.                   |
| `DEBUG`         | no       | `False`                  | Set `True` for local development.    |
| `ALLOWED_HOSTS` | no       | `127.0.0.1,localhost`    | Comma-separated hostnames.           |
| `DATABASE_URL`  | no       | local SQLite file        | e.g. `postgres://user:pass@host/db`. |
