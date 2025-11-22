# Outfit Avenue (Django)

A full-stack fashion e-commerce site built with Django. It includes product browsing, cart, checkout, order tracking, user accounts with OTP verification, and a themed UI.

## Features
- Product catalog with detailed views
- Cart with localStorage persistence and navbar sync
- Checkout with multiple payment methods (Card / UPI / COD)
- Order tracking timeline and status updates
- Account registration/login with email verification and MFA OTP for login
- My Orders and Profile pages
- Admin improvements for order updates and status badges

## Tech Stack
- Backend: Django 4.2
- API: Django REST Framework, Simple JWT (token endpoints)
- Frontend: Bootstrap 5, jQuery, AOS
- Storage: SQLite (default), `ImageField` with `Pillow`

## Getting Started

### Prerequisites
- Python 3.10+
- Pip
- Virtualenv (recommended)

### Setup (Windows PowerShell)
1. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Apply migrations:
   ```powershell
   python manage.py migrate
   ```
4. Create a superuser:
   ```powershell
   python manage.py createsuperuser
   ```
5. Run the dev server:
   ```powershell
   python manage.py runserver 127.0.0.1:8000
   ```

### Environment Variables
Create a `.env` file at the project root for sensitive settings (do not commit this file):
- `SECRET_KEY`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `DEFAULT_USE_TLS=True`
- `DEFAULT_USE_SSL=False`

Refer to your `settings.py` for how these values are loaded.

### Project Structure (selected)
- `Ecommerceweb/` – main Django project
- `account/` – custom user model, auth views, OTP, profile, orders
- `shop/` – products, cart, checkout, tracker, admin tweaks
- `blog/` – themed blog module
- `media/` – uploaded images (avatars, product/blog images)
- `static/` – static assets (CSS/JS/images)

### Common Commands
- Run tests: (add tests in `*/tests.py`) `python manage.py test`
- Collect static (for prod): `python manage.py collectstatic`

## Notes
- Orders are associated to users via email (`Order.email`). Ensure checkout uses the same email as the account to see orders under My Orders/Profile.
- Do not commit `db.sqlite3`, `.env`, or generated `staticfiles/` in Git.

## License
MIT