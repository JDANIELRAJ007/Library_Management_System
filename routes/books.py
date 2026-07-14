from flask import Blueprint, render_template, request
from models.book import Book, Category

books_bp = Blueprint('books', __name__)


@books_bp.route('/')
def catalog():
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', 0, type=int)

    query = Book.query
    if q:
        query = query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%'))
        )
    if category_id:
        query = query.filter_by(category_id=category_id)

    paginated = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    books = paginated.items
    total = paginated.total
    categories = Category.query.order_by(Category.name).all()

    return render_template('books/catalog.html',
                           books=books, q=q, total=total, page=page,
                           paginated=paginated, categories=categories,
                           category_id=category_id)


@books_bp.route('/<int:bid>')
def book_detail(bid):
    book = Book.query.get_or_404(bid)
    return render_template('books/detail.html', book=book)
