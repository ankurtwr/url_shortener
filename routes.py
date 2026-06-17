from flask import Blueprint, request, redirect, jsonify, render_template, url_for
from datetime import datetime, timedelta, timezone
from cachetools import TTLCache
from models import db, URL
from utils import generate_short_code, normalize_url, is_valid_url, is_valid_custom_code

main = Blueprint('main', __name__)

# In-memory cache: up to 2000 entries, 1-hour TTL
# Key: short_code -> Value: original_url
_url_cache = TTLCache(maxsize=2000, ttl=3600)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

@main.route('/')
def index():
    """Landing page with URL shortener form."""
    return render_template('index.html')


@main.route('/dashboard')
def dashboard():
    """Analytics dashboard showing all shortened URLs."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    urls = URL.query.order_by(URL.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return render_template('dashboard.html', urls=urls)


# ---------------------------------------------------------------------------
# API: Shorten URL
# ---------------------------------------------------------------------------

@main.route('/shorten', methods=['POST'])
def shorten_url():
    """Accept a URL and return a shortened version."""
    data = request.get_json() if request.is_json else request.form

    original_url = data.get('url', '').strip()
    custom_code = data.get('custom_code', '').strip()
    expiry_option = data.get('expiry', 'never')  # never, 1h, 24h, 7d, 30d, custom

    # Validate URL
    original_url = normalize_url(original_url)
    if not original_url or not is_valid_url(original_url):
        return jsonify({'error': 'Please enter a valid URL.'}), 400

    # Determine short code
    if custom_code:
        if not is_valid_custom_code(custom_code):
            return jsonify({
                'error': 'Custom code must be 3-30 characters, '
                         'alphanumeric and hyphens only.'
            }), 400

        # Check if custom code already exists
        existing = URL.query.filter_by(short_code=custom_code).first()
        if existing:
            return jsonify({'error': 'That custom code is already taken. Try another.'}), 409

        short_code = custom_code
        is_custom = True
    else:
        # Generate random code with collision retry
        short_code = None
        for _ in range(5):
            candidate = generate_short_code()
            if not URL.query.filter_by(short_code=candidate).first():
                short_code = candidate
                break

        if not short_code:
            return jsonify({'error': 'Could not generate a unique code. Please try again.'}), 500
        is_custom = False

    # Determine expiration
    expires_at = _calculate_expiry(expiry_option, data.get('custom_expiry'))

    # Save to database
    url_entry = URL(
        short_code=short_code,
        original_url=original_url,
        expires_at=expires_at,
        is_custom=is_custom,
    )
    db.session.add(url_entry)
    db.session.commit()

    # Pre-populate cache
    _url_cache[short_code] = original_url

    short_url = request.host_url + short_code

    return jsonify({
        'success': True,
        'short_url': short_url,
        'short_code': short_code,
        'original_url': original_url,
        'expires_at': expires_at.strftime('%Y-%m-%d %H:%M UTC') if expires_at else 'Never',
    }), 201


# ---------------------------------------------------------------------------
# Redirect: The core feature — must be FAST
# ---------------------------------------------------------------------------

@main.route('/<short_code>')
def redirect_to_url(short_code):
    """Look up short code and redirect. Cache-first for speed."""

    # 1. Check in-memory cache (instant)
    cached_url = _url_cache.get(short_code)
    if cached_url:
        # Increment click count in background (don't block the redirect)
        _increment_click_async(short_code)
        return redirect(cached_url, code=302)

    # 2. Cache miss — query database (indexed lookup)
    url_entry = URL.query.filter_by(short_code=short_code).first()

    if not url_entry:
        return render_template('404.html', message="This short link doesn't exist."), 404

    # 3. Check expiration
    if url_entry.is_expired:
        return render_template('404.html', message="This short link has expired."), 410

    # 4. Populate cache for next time
    _url_cache[short_code] = url_entry.original_url

    # 5. Increment click count
    url_entry.click_count += 1
    db.session.commit()

    return redirect(url_entry.original_url, code=302)


# ---------------------------------------------------------------------------
# API: Dashboard data (for AJAX refresh)
# ---------------------------------------------------------------------------

@main.route('/api/urls')
def api_urls():
    """Return all URLs as JSON for dashboard."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    pagination = URL.query.order_by(URL.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    return jsonify({
        'urls': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page,
    })


# ---------------------------------------------------------------------------
# API: Delete URL
# ---------------------------------------------------------------------------

@main.route('/api/urls/<int:url_id>', methods=['DELETE'])
def delete_url(url_id):
    """Delete a shortened URL."""
    url_entry = URL.query.get(url_id)
    if not url_entry:
        return jsonify({'error': 'URL not found.'}), 404

    # Remove from cache
    _url_cache.pop(url_entry.short_code, None)

    db.session.delete(url_entry)
    db.session.commit()

    return jsonify({'success': True, 'message': 'URL deleted.'})


# ---------------------------------------------------------------------------
# Error Handlers
# ---------------------------------------------------------------------------

@main.app_errorhandler(404)
def not_found(e):
    """Custom 404 page."""
    return render_template('404.html', message="Page not found."), 404


@main.app_errorhandler(500)
def server_error(e):
    """Custom 500 page."""
    return render_template('404.html', message="Something went wrong on our end."), 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _calculate_expiry(option, custom_value=None):
    """Calculate expiration datetime based on user selection."""
    now = datetime.now(timezone.utc)

    expiry_map = {
        'never': None,
        '1h': now + timedelta(hours=1),
        '24h': now + timedelta(hours=24),
        '7d': now + timedelta(days=7),
        '30d': now + timedelta(days=30),
        '90d': now + timedelta(days=90),
    }

    if option in expiry_map:
        return expiry_map[option]

    # Custom date provided
    if option == 'custom' and custom_value:
        try:
            return datetime.strptime(custom_value, '%Y-%m-%dT%H:%M').replace(
                tzinfo=timezone.utc
            )
        except (ValueError, TypeError):
            return None

    return None


def _increment_click_async(short_code):
    """Increment click count for a cached URL (runs during request)."""
    try:
        url_entry = URL.query.filter_by(short_code=short_code).first()
        if url_entry:
            url_entry.click_count += 1
            db.session.commit()
    except Exception:
        db.session.rollback()
