from datetime import datetime
from . import db


class Fine(db.Model):
    __tablename__ = 'fines'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    borrow_id      = db.Column(db.Integer, db.ForeignKey('borrow_records.id'))
    amount         = db.Column(db.Float, nullable=False, default=0.0)
    reason         = db.Column(db.String(200))
    paid           = db.Column(db.Boolean, default=False)
    paid_at        = db.Column(db.DateTime)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    razorpay_order_id = db.Column(db.String(100))
    razorpay_payment_id = db.Column(db.String(100))


    borrow_record  = db.relationship('BorrowRecord', backref='fine', uselist=False)

    def __repr__(self):
        return f'<Fine user={self.user_id} amount={self.amount} paid={self.paid}>'
