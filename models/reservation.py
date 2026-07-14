from datetime import datetime
from . import db


class Reservation(db.Model):
    __tablename__ = 'reservations'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id     = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    reserved_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at  = db.Column(db.DateTime)
    # Status: 'active' | 'fulfilled' | 'cancelled' | 'expired'
    status      = db.Column(db.String(20), default='active')

    def __repr__(self):
        return f'<Reservation user={self.user_id} book={self.book_id}>'
