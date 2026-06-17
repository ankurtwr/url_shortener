# ✂ Snip — URL Shortener

A fast, minimal URL shortener built with **Flask** and **MySQL**. Create short links instantly with custom aliases, expiration control, and a clean analytics dashboard.

---

## Features

- **Instant URL shortening** — Paste a long URL, get a clean short link in under a second
- **Custom aliases** — Choose your own short code (e.g., `yoursite.com/my-brand`)
- **Expiration control** — Set links to expire after 1 hour, 24 hours, 7 days, 30 days, 90 days, or a custom date
- **Click analytics** — Dashboard with total clicks, link status, and creation dates
- **In-memory caching** — Redirects are cached in memory for near-zero latency
- **Dark / Light theme** — Toggle between themes, preference saved locally
- **Custom 404 page** — Animated error page for broken or expired links
- **Responsive design** — Works on desktop, tablet, and mobile
- **No authentication required** — Open for anyone to use

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.10+, Flask 3.x |
| **Database** | MySQL 8.0+ with InnoDB |
| **ORM** | Flask-SQLAlchemy |
| **Caching** | cachetools (in-memory TTL cache) |
| **Frontend** | Vanilla HTML, CSS, JavaScript |
| **Fonts** | DM Sans, JetBrains Mono (Google Fonts) |

---

## Project Structure

```
url_shortner/
├── app.py                  # Flask app factory & entry point
├── config.py               # Configuration (loads from .env)
├── models.py               # SQLAlchemy URL model
├── routes.py               # All routes — shorten, redirect, dashboard, API
├── utils.py                # URL validation, Base62 code generation
├── setup_db.py             # Database creation script
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not committed)
├── .gitignore
├── README.md
├── static/
│   ├── css/
│   │   └── style.css       # Full design system — dark/light themes
│   └── js/
│       └── main.js         # AJAX, copy-to-clipboard, theme toggle
└── templates/
    ├── base.html            # Base layout with navbar & footer
    ├── index.html           # Landing page with URL input form
    ├── dashboard.html       # Analytics dashboard
    └── 404.html             # Custom error page with animations
```

---

## Getting Started

### Prerequisites

- **Python 3.10+** installed
- **MySQL 8.0+** installed and running
- **pip** (Python package manager)

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/url_shortner.git
cd url_shortner
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

Create a `.env` file in the project root (or edit the existing one):

```env
FLASK_APP=app.py
FLASK_DEBUG=1
SECRET_KEY=your-secret-key-here

DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=root
DB_NAME=url_shortner_db
```

### 5. Set up the database

Make sure MySQL is running, then:

```bash
python setup_db.py
```

This will:
- Create the `url_shortner_db` database
- Create the `urls` table with proper indexing

### 6. Run the application

```bash
python app.py
```

The app will be available at **http://localhost:5000**

---

## Usage

### Shorten a URL

1. Open `http://localhost:5000`
2. Paste your long URL in the input field
3. (Optional) Enter a custom alias
4. (Optional) Set an expiration time
5. Click **Shorten**
6. Copy the generated short link

### Redirect

Visit your short link (e.g., `http://localhost:5000/abc123`) and you'll be instantly redirected to the original URL.

### Dashboard

Visit `http://localhost:5000/dashboard` to see:
- All shortened URLs
- Click counts for each link
- Link status (Active / Expired)
- Creation and expiration dates
- Delete links you no longer need

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Landing page |
| `POST` | `/shorten` | Shorten a URL (JSON body) |
| `GET` | `/<short_code>` | Redirect to original URL |
| `GET` | `/dashboard` | Analytics dashboard |
| `GET` | `/api/urls` | Get all URLs (JSON, paginated) |
| `DELETE` | `/api/urls/<id>` | Delete a URL |

### POST `/shorten` — Request Body

```json
{
  "url": "https://example.com/very/long/url",
  "custom_code": "my-link",
  "expiry": "7d",
  "custom_expiry": "2025-12-31T23:59"
}
```

**Expiry options:** `never`, `1h`, `24h`, `7d`, `30d`, `90d`, `custom`

### POST `/shorten` — Response

```json
{
  "success": true,
  "short_url": "http://localhost:5000/my-link",
  "short_code": "my-link",
  "original_url": "https://example.com/very/long/url",
  "expires_at": "Jan 07, 2026 00:00 UTC"
}
```

---

## Performance

The redirect path is optimized for minimal latency:

1. **In-memory cache** (TTLCache) is checked first — no DB query needed for popular links
2. **Indexed lookups** — `short_code` has a `UNIQUE` index in MySQL for O(log n) queries
3. **Connection pooling** — SQLAlchemy maintains a pool of 10 connections to avoid connection overhead
4. **302 redirects** — Standard temporary redirects that browsers handle natively

---

## Themes

The app supports both **dark** and **light** themes:

- Click the ☀/☾ icon in the navbar to toggle
- Your preference is saved in `localStorage` and persists across sessions
- All colors use CSS custom properties for seamless switching

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -m 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## License

This project is open source and available under the [MIT License](LICENSE).
