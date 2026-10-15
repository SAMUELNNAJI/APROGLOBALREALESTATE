# Apro Global Real Estate

Django project for the Apro Global Real Estate website. The original HTML
pages are served through Django without changing their design, the files in
`staticfiles/` are configured as static assets, and sign in / sign up,
listings, bookings, payments, chat and support tickets are backed by the
`core` app.

## Requirements

- Python 3.10 or newer
- pip

## Local setup

From the project root, create and activate a virtual environment, then install
the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Create the local database, load the demo data and start the development
server:

```powershell
python manage.py migrate
python manage.py seed_if_empty
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. The existing pages are available at
`/services.html`, `/listings.html`, `/about.html`, `/contact.html`,
`/privacy.html`, and `/terms.html`.

The custom admin dashboard is available at `/dashboard/admin/` for superuser
accounts (the stock Django admin at `/admin/` is not enabled). Create an admin
with `python manage.py createsuperuser`, or set `DJANGO_SUPERUSER_USERNAME`,
`DJANGO_SUPERUSER_PASSWORD` and `DJANGO_SUPERUSER_EMAIL` and run
`python manage.py seed_if_empty`.

## Configuration

Settings can be supplied through environment variables:

- `DJANGO_SECRET_KEY`: Django signing key. A development-only fallback is used
  when this is unset; set a private, randomly generated value in production.
- `DJANGO_DEBUG`: boolean (`1`/`0`, `true`/`false`, `yes`/`no`, or `on`/`off`),
  defaults to `1`. Set to `0` in production.
- `DJANGO_ALLOWED_HOSTS`: comma-separated host names; defaults to
  `localhost,127.0.0.1`. On Render, `.onrender.com` comes from `render.yaml`
  and the service's own hostname is added automatically from
  `RENDER_EXTERNAL_HOSTNAME`.
- `DJANGO_CSRF_TRUSTED_ORIGINS`: comma-separated full origins (e.g.
  `https://aproglobal.com`) allowed to POST forms. Derived from
  `DJANGO_ALLOWED_HOSTS` when unset.
- `DATABASE_URL`: full database URL (e.g. `postgres://user:pass@host/db`).
  When set, Postgres is used instead of the local `db.sqlite3` file.
- `DJANGO_EMAIL_BACKEND`: Django email backend; defaults to the console backend.
- `DJANGO_SUPERUSER_USERNAME` / `DJANGO_SUPERUSER_PASSWORD` /
  `DJANGO_SUPERUSER_EMAIL`: optional admin account created by
  `python manage.py seed_if_empty` on a fresh database.
- `DJANGO_SECURE_HSTS_SECONDS`: HTTP Strict Transport Security max-age;
  defaults to `0` (off) - enable once HTTPS is confirmed.

## Deploying to Render

The repository ships a `render.yaml` blueprint. In the Render dashboard choose
**New -> Blueprint**, select this repository, and Render will build a web
service with:

- **Build**: `pip install -r requirements.txt` +
  `python manage.py collectstatic --noinput`
- **Start**: `python manage.py migrate --noinput` +
  `python manage.py seed_if_empty` + `gunicorn config.wsgi:application`
- **Health check**: `/healthz`

Static files are served by WhiteNoise and uploaded media by Django itself, so
no extra web server is needed. The demo fixture is loaded only when the
database is empty (the seed command is idempotent).

> **Data durability:** on Render's free plan the instance disk is recreated on
> every deploy, so accounts/bookings/uploads reset unless you attach a
> persistent disk (commented example in `render.yaml`) or a Render Postgres
> database - attach one to the service and `DATABASE_URL` is picked up
> automatically.

## Tests

```powershell
python manage.py test
```

## Templates & authentication

- `templates/base.html` holds the shared header/footer; every page extends it.
- `templates/auth/` - sign in / sign up pages (`/signin/`, `/signup/`).
- `templates/dashboard/Purchase Dashboard/` - regular users land here after sign in.
- `templates/dashboard/Apro Global Dashboard/` - superusers land here after sign in.
- `templates/chat/` - WhatsApp-style support chat (users and admins).
