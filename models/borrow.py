from datetime import datetime, timedelta
from flask import current_app
from . import db


class BorrowRecord(db.Model):
    __tablename__ = 'borrow_records'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id       = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)

    # Dates
    borrow_date   = db.Column(db.DateTime, default=datetime.utcnow)
    due_date      = db.Column(db.DateTime)
    return_date   = db.Column(db.DateTime)

    # Status: 'requested' | 'approved' | 'borrowed' | 'returned' | 'rejected' | 'overdue'
    status        = db.Column(db.String(20), default='requested')

    # Teacher/Admin who approved
    approved_by   = db.Column(db.Integer, db.ForeignKey('users.id'))
    notes         = db.Column(db.Text)

    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_due_date(self, admin_time_str=None):
        from services.settings_service import get_setting
        due_setting = get_setting('due_time', '14d')
        if due_setting == '1m':
            delta = timedelta(minutes=1)
        elif due_setting == '10h':
            delta = timedelta(hours=10)
        elif due_setting == '1d':
            delta = timedelta(days=1)
        elif due_setting == '7d':
            delta = timedelta(days=7)
        else:
            delta = timedelta(days=14)

        base_time = datetime.utcnow()
        if admin_time_str:
            try:
                # ISO format timestamp from admin computer
                parsed_time = datetime.fromisoformat(admin_time_str.replace('Z', '+00:00'))
                base_time = parsed_time.replace(tzinfo=None)
            except Exception:
                pass

        self.due_date = base_time + delta

    @property
    def is_overdue(self):
        if self.status == 'borrowed' and self.due_date:
            return datetime.utcnow() > self.due_date
        return False

    @property
    def overdue_days(self):
        if self.is_overdue:
            return (datetime.utcnow() - self.due_date).days
        return 0

    @property
    def fine_amount(self):
        if not self.is_overdue:
            return 0
        rate = current_app.config.get('FINE_PER_DAY', 5)
        
        diff = datetime.utcnow() - self.due_date
        # Every 24 hours (86400 seconds) the fine doubles
        periods_24h = int(diff.total_seconds() // 86400)
        
        # base fine is applied immediately when overdue.
        # multiplier starts at 1, doubles every 24h
        multiplier = 2 ** periods_24h
        return rate * multiplier

    def __repr__(self):
        return f'<BorrowRecord user={self.user_id} book={self.book_id} status={self.status}>'
