from datetime import datetime
from . import db


class Wishlist(db.Model):
    __tablename__ = 'wishlist'

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id    = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    added_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_wishlist'),)

    def __repr__(self):
        return f'<Wishlist user={self.user_id} book={self.book_id}>'
