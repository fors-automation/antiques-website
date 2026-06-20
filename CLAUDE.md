# Project: Glory Days Past — Online Antiques Shop (Django on Lightsail)

## What this is
An online shop for a small antiques business. The owner is non-technical
and must manage listings herself through the Django admin — never by editing code.

## Project layout
- Settings package: `config/` (settings.py, urls.py, wsgi.py, asgi.py).
- App: `shop/` (views, urls, models, admin).
- Project-level `templates/` and `static/` dirs (configured in settings, not per-app).

## Core principles
- Every item is one-of-a-kind: quantity is always 1. "Sold" is permanent.
- The owner manages listings via the Django admin, not custom pages.
- Keep it simple and conventional. Prefer boring, well-supported Django patterns.

## Stack & hosting
- Python 3.12+ (Django 6.0 requires it; dev box runs 3.12.10).
- Django (latest stable), server-rendered templates. Django is pinned in
  `requirements.txt` (currently 6.0.6) — that pin *is* "latest stable"; bump it deliberately.
- PostgreSQL running ON the Lightsail instance (not a managed service)
- Gunicorn (systemd service) behind Nginx; HTTPS via Let's Encrypt/Certbot
- Item photos stored on the instance's local disk under MEDIA_ROOT, served by Nginx
- Django's built-in admin = the owner's management interface
- Stripe Checkout via the Python SDK (NEVER collect or store card data ourselves)
- Resend for transactional email
- Shared Lightsail box will also run my other projects — keep this project isolated
  (its own system user, virtualenv, database, and Nginx server block)

## Conventions
- All secrets (SECRET_KEY, DB creds, Stripe, email) come from environment variables.
  Local: a .env via django-environ (never committed). Production: a server-side .env
  (chmod 600), never committed.
- DEBUG=False in production; ALLOWED_HOSTS read from env.
- Static files via collectstatic + WhiteNoise (keeps Nginx config thin); media served by Nginx.
- Storefront pages are server-rendered Django templates.
- Use Stripe Test mode until I explicitly say to go live.
- Prices use DecimalField (never floats); store the currency. Convert to integer
  minor units (cents) only at the Stripe API boundary.
- Enforce "one-of-a-kind / Sold is permanent" at checkout: mark an item Sold via the
  Stripe webhook (checkout.session.completed), NOT the browser redirect, and do the
  sold-transition atomically (select_for_update / guarded update) so the single unit
  can't be double-sold.
- Harden the admin (it is the owner's production UI): non-default admin URL, HTTPS-only,
  strong owner password. In production set SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE,
  CSRF_COOKIE_SECURE, and HSTS.
- Pillow is required for ImageField; validate uploaded image size/dimensions (the owner
  uploads phone photos) and consider generating thumbnails.

## Always do
- Before any large change, explain the plan and wait for my approval.
- After model changes: makemigrations + migrate, and register the model in admin.
- When writing server commands, give a clear SSH runbook; assume I run them, not you.
- Make small, reviewable changes. Commit only when I ask — do not auto-commit.
- After changes, tell me exactly what to test (URLs, admin steps).
- Keep a lightweight Django test suite for critical paths (sold-transition, checkout)
  in addition to the manual test steps.

## Build order (do not skip ahead)
1. Models + storefront + Django admin for the owner (no payments)
2. Deploy to the Lightsail box (Gunicorn/Nginx/HTTPS) + backups
3. Stripe Checkout buy flow
4. (Later) Auctions with bidding and an end date
