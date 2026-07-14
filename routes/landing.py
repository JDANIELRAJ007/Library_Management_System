from flask import Blueprint, render_template
from models.book import Book

landing_bp = Blueprint('landing', __name__)


@landing_bp.route('/')
def index():
    featured = Book.query.order_by(Book.times_borrowed.desc()).limit(8).all()
    new_arrivals = Book.query.order_by(Book.created_at.desc()).limit(4).all()
    return render_template('landing/index.html',
                           featured=featured,
                           new_arrivals=new_arrivals)
