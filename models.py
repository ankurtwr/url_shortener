from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone

db = SQLAlchemy()


class URL(db.Model):
    """Stores shortened URL mappings."""
    __tablename__ = 'urls'

    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    short_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    original_url = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = db.Column(db.DateTime, nullable=True)  # None = never expires
    click_count = db.Column(db.Integer, default=0)
    is_custom = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<URL {self.short_code} -> {self.original_url[:50]}>'

    @property
    def is_expired(self):
        """Check if this URL has expired."""
        if self.expires_at is None:
            return False
        # MySQL DATETIME returns timezone-naive values, so compare with naive UTC
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        expires = self.expires_at.replace(tzinfo=None) if self.expires_at.tzinfo else self.expires_at
        return now_utc > expires

    def to_dict(self):
        """Serialize to dictionary for JSON responses."""
        return {
            'id': self.id,
            'short_code': self.short_code,
            'original_url': self.original_url,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else None,
            'expires_at': self.expires_at.strftime('%Y-%m-%d %H:%M') if self.expires_at else None,
            'click_count': self.click_count,
            'is_custom': self.is_custom,
            'is_expired': self.is_expired,
        }
