from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from models import db
from models.user import User
from models.book import Book, Category
from models.borrow import BorrowRecord
from models.fine import Fine
from models.notification import Notification
from utils.decorators import admin_required

admin_bp = Blueprint('admin', __name__)


# ─── Dashboard ───────────────────────────────────────────────
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    stats = {
        'total_books':       Book.query.count(),
        'total_users':       User.query.count(),
        'total_students':    User.query.filter_by(role='student').count(),
        'total_teachers':    User.query.filter_by(role='teacher').count(),
        'active_borrows':    BorrowRecord.query.filter_by(status='borrowed').count(),
        'pending_requests':  BorrowRecord.query.filter_by(status='requested').count(),
        'overdue_count':     0,
        'total_fines':       db.session.query(db.func.sum(Fine.amount)).scalar() or 0,
        'unpaid_fines':      db.session.query(db.func.sum(Fine.amount)).filter_by(paid=False).scalar() or 0,
    }

    # Count overdue
    all_borrowed = BorrowRecord.query.filter_by(status='borrowed').all()
    stats['overdue_count'] = sum(1 for r in all_borrowed if r.is_overdue)

    recent_requests = (BorrowRecord.query
                       .filter_by(status='requested')
                       .order_by(BorrowRecord.created_at.desc())
                       .limit(10).all())
    recent_users = (User.query
                    .order_by(User.created_at.desc())
                    .limit(8).all())

    # Monthly borrow data for chart (last 6 months)
    monthly_data = _get_monthly_data()

    return render_template('admin/dashboard.html',
                           stats=stats,
                           recent_requests=recent_requests,
                           recent_users=recent_users,
                           monthly_data=monthly_data)


# ─── Users Management ────────────────────────────────────────
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    role_filter = request.args.get('role', '')
    q = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if q:
        query = query.filter(
            (User.username.ilike(f'%{q}%')) |
            (User.email.ilike(f'%{q}%')) |
            (User.full_name.ilike(f'%{q}%'))
        )
    users_page = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/users.html', users=users_page, q=q, role_filter=role_filter)


@admin_bp.route('/users/<int:uid>/toggle')
@login_required
@admin_required
def toggle_user(uid):
    user = User.query.get_or_404(uid)
    if user.id == current_user.id:
        flash('Cannot deactivate yourself.', 'warning')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        status = 'activated' if user.is_active else 'deactivated'
        flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        user = User(
            full_name=request.form['full_name'],
            username=request.form['username'],
            email=request.form['email'],
            role=request.form['role'],
            department=request.form.get('department', ''),
            student_id=request.form.get('student_id', ''),
            employee_id=request.form.get('employee_id', ''),
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash(f'User {user.username} created successfully.', 'success')
        return redirect(url_for('admin.users'))
    return render_template('admin/add_user.html')


# ─── Books Management ────────────────────────────────────────
@admin_bp.route('/books')
@login_required
@admin_required
def books():
    q    = request.args.get('q', '')
    page = request.args.get('page', 1, type=int)
    cat  = request.args.get('category', 0, type=int)

    query = Book.query
    if q:
        query = query.filter(
            (Book.title.ilike(f'%{q}%')) |
            (Book.author.ilike(f'%{q}%')) |
            (Book.isbn.ilike(f'%{q}%'))
        )
    if cat:
        query = query.filter_by(category_id=cat)

    books_page = query.order_by(Book.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    categories = Category.query.all()
    return render_template('admin/books.html', books=books_page, categories=categories, q=q, cat=cat)


@admin_bp.route('/books/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_book():
    if request.method == 'POST':
        category_id = request.form.get('category_id') or None
        
        import os
        import uuid
        from werkzeug.utils import secure_filename
        from flask import current_app
        
        cover_filename = ''
        cover_file = request.files.get('cover_image')
        if cover_file and cover_file.filename:
            ext = cover_file.filename.rsplit('.', 1)[-1].lower() if '.' in cover_file.filename else 'png'
            cover_filename = f"{uuid.uuid4().hex}.{ext}"
            cover_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'covers')
            os.makedirs(cover_path, exist_ok=True)
            cover_file.save(os.path.join(cover_path, cover_filename))
            
        pdf_filename = ''
        pdf_file = request.files.get('pdf_file')
        if pdf_file and pdf_file.filename:
            ext = pdf_file.filename.rsplit('.', 1)[-1].lower() if '.' in pdf_file.filename else 'pdf'
            pdf_filename = f"{uuid.uuid4().hex}.{ext}"
            pdf_path = current_app.config['EBOOK_FOLDER']
            os.makedirs(pdf_path, exist_ok=True)
            pdf_file.save(os.path.join(pdf_path, pdf_filename))

        book = Book(
            title=request.form['title'],
            author=request.form['author'],
            isbn=request.form.get('isbn') or None,
            publisher=request.form.get('publisher', ''),
            published_year=request.form.get('published_year') or None,
            description=request.form.get('description', ''),
            language=request.form.get('language', 'English'),
            pages=request.form.get('pages') or None,
            category_id=category_id,
            copies_total=int(request.form.get('copies_total', 1)),
            copies_available=int(request.form.get('copies_total', 1)),
            location=request.form.get('location', ''),
            cover_image=cover_filename,
            has_ebook=bool(pdf_filename),
            pdf_file=pdf_filename,
            tags=request.form.get('tags', ''),
            added_by=current_user.id,
        )
        db.session.add(book)
        db.session.commit()
        flash(f'Book "{book.title}" added successfully.', 'success')
        return redirect(url_for('admin.books'))
    categories = Category.query.all()
    return render_template('admin/add_book.html', categories=categories)


@admin_bp.route('/books/<int:bid>/delete', methods=['POST'])
@login_required
@admin_required
def delete_book(bid):
    book = Book.query.get_or_404(bid)
    db.session.delete(book)
    db.session.commit()
    flash(f'Book "{book.title}" deleted.', 'success')
    return redirect(url_for('admin.books'))


# ─── Categories ──────────────────────────────────────────────
@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form['name'].strip()
        if not Category.query.filter_by(name=name).first():
            cat = Category(
                name=name,
                description=request.form.get('description', ''),
                icon=request.form.get('icon', 'fa-book'),
                color=request.form.get('color', '#6366f1'),
            )
            db.session.add(cat)
            db.session.commit()
            flash('Category added.', 'success')
        else:
            flash('Category already exists.', 'warning')
    cats = Category.query.order_by(Category.name).all()
    return render_template('admin/categories.html', categories=cats)


# ─── Borrow Requests ─────────────────────────────────────────
@admin_bp.route('/requests')
@login_required
@admin_required
def borrow_requests():
    status = request.args.get('status', 'requested')
    page   = request.args.get('page', 1, type=int)
    records = (BorrowRecord.query
               .filter_by(status=status)
               .order_by(BorrowRecord.created_at.desc())
               .paginate(page=page, per_page=20, error_out=False))
    return render_template('admin/requests.html', records=records, status=status)


@admin_bp.route('/requests/<int:rid>/approve', methods=['POST'])
@login_required
@admin_required
def approve_request(rid):
    record = BorrowRecord.query.get_or_404(rid)
    if record.status != 'requested':
        flash('Request already processed.', 'warning')
        return redirect(url_for('admin.borrow_requests'))

    if record.book.copies_available < 1:
        flash('No copies available.', 'danger')
        return redirect(url_for('admin.borrow_requests'))

    admin_time_str = request.form.get('admin_time')
    record.status = 'borrowed'
    record.approved_by = current_user.id
    record.borrow_date = datetime.utcnow()
    record.set_due_date(admin_time_str)
    record.book.copies_available -= 1

    # Notify user
    _notify(record.user_id, 'Borrow Approved ✅',
            f'Your request for "{record.book.title}" has been approved. Due: {record.due_date.strftime("%d %b %Y")}',
            'success')

    db.session.commit()
    flash('Request approved.', 'success')
    return redirect(url_for('admin.borrow_requests'))


@admin_bp.route('/requests/<int:rid>/reject', methods=['POST'])
@login_required
@admin_required
def reject_request(rid):
    record = BorrowRecord.query.get_or_404(rid)
    record.status = 'rejected'
    _notify(record.user_id, 'Borrow Request Rejected',
            f'Your request for "{record.book.title}" was rejected.', 'danger')
    db.session.commit()
    flash('Request rejected.', 'info')
    return redirect(url_for('admin.borrow_requests'))


@admin_bp.route('/requests/<int:rid>/return', methods=['POST'])
@login_required
@admin_required
def mark_returned(rid):
    record = BorrowRecord.query.get_or_404(rid)
    if record.status != 'borrowed':
        flash('Book not currently borrowed.', 'warning')
        return redirect(url_for('admin.borrow_requests', status='borrowed'))

    record.status = 'returned'
    record.return_date = datetime.utcnow()
    record.book.copies_available += 1

    # Fine if overdue
    if record.is_overdue:
        fine_amount = record.fine_amount
        fine = Fine(user_id=record.user_id, borrow_id=record.id,
                    amount=fine_amount,
                    reason=f'Overdue fine for "{record.book.title}" ({record.overdue_days} days)')
        db.session.add(fine)
        _notify(record.user_id, 'Overdue Fine ⚠️',
                f'A fine of ₹{fine_amount} has been added for late return of "{record.book.title}".',
                'warning')
    else:
        _notify(record.user_id, 'Book Returned ✅',
                f'"{record.book.title}" has been successfully returned. Thank you!', 'success')

    db.session.commit()
    flash('Book marked as returned.', 'success')
    return redirect(url_for('admin.borrow_requests', status='borrowed'))


# ─── Fines ───────────────────────────────────────────────────
@admin_bp.route('/fines')
@login_required
@admin_required
def fines():
    page = request.args.get('page', 1, type=int)
    paid = request.args.get('paid', '')
    query = Fine.query
    if paid == '1':
        query = query.filter_by(paid=True)
    elif paid == '0':
        query = query.filter_by(paid=False)
        
    fines_page = query.order_by(Fine.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    
    from services.settings_service import get_setting
    due_setting = get_setting('due_time', '14d')
    return render_template('admin/fines.html', fines=fines_page, paid=paid, due_setting=due_setting)

@admin_bp.route('/fines/settings', methods=['POST'])
@login_required
@admin_required
def set_fine_settings():
    from services.settings_service import set_setting
    due_time_str = request.form.get('due_time')
    if due_time_str in ['1m', '10h', '1d', '7d']:
        set_setting('due_time', due_time_str)
        flash(f'Due time setting updated to {due_time_str}', 'success')
    else:
        flash('Invalid due time selection.', 'danger')
    return redirect(url_for('admin.fines'))


@admin_bp.route('/fines/<int:fid>/mark-paid', methods=['POST'])
@login_required
@admin_required
def mark_fine_paid(fid):
    fine = Fine.query.get_or_404(fid)
    fine.paid = True
    fine.paid_at = datetime.utcnow()
    db.session.commit()
    flash('Fine marked as paid.', 'success')
    return redirect(url_for('admin.fines'))


@admin_bp.route('/calculate-fines', methods=['POST'])
@login_required
@admin_required
def calculate_fines():
    active_borrows = BorrowRecord.query.filter_by(status='borrowed').all()
    count = 0
    for record in active_borrows:
        if record.is_overdue:
            total_fine = record.fine_amount
            paid_fines = Fine.query.filter_by(borrow_id=record.id, paid=True).all()
            total_paid = sum(f.amount for f in paid_fines)
            remaining = total_fine - total_paid
            
            unpaid_fine = Fine.query.filter_by(borrow_id=record.id, paid=False).first()
            if remaining > 0:
                if not unpaid_fine:
                    fine = Fine(user_id=record.user_id, borrow_id=record.id, amount=remaining, 
                                reason=f'Overdue fine for "{record.book.title}" ({record.overdue_days} days)')
                    db.session.add(fine)
                    _notify(record.user_id, 'Overdue Alert ⚠️', 
                            f'Your book "{record.book.title}" is overdue by {record.overdue_days} days. A fine of ₹{remaining} is due.', 'danger')
                    count += 1
                elif unpaid_fine.amount != remaining:
                    unpaid_fine.amount = remaining
                    unpaid_fine.reason = f'Overdue fine for "{record.book.title}" ({record.overdue_days} days)'
                    count += 1
            elif remaining <= 0 and unpaid_fine:
                db.session.delete(unpaid_fine)
                count += 1
    db.session.commit()
    flash(f'Fines calculated automatically. {count} records updated.', 'success')
    return redirect(url_for('admin.fines'))


# ─── Reports ─────────────────────────────────────────────────
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    top_books = (db.session.query(Book)
                 .order_by(Book.times_borrowed.desc())
                 .limit(10).all())
    top_borrowers = (db.session.query(User, db.func.count(BorrowRecord.id).label('count'))
                     .join(BorrowRecord, User.id == BorrowRecord.user_id)
                     .group_by(User.id)
                     .order_by(db.text('count DESC'))
                     .limit(10).all())
    return render_template('admin/reports.html',
                           top_books=top_books,
                           top_borrowers=top_borrowers)


# ─── Helpers ─────────────────────────────────────────────────
def _notify(user_id, title, message, type_='info', link=None):
    n = Notification(user_id=user_id, title=title, message=message,
                     type=type_, link=link)
    db.session.add(n)


def _get_monthly_data():
    from sqlalchemy import extract
    from datetime import date
    months = []
    counts = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month = (now.month - i - 1) % 12 + 1
        year  = now.year if now.month - i > 0 else now.year - 1
        count = (BorrowRecord.query
                 .filter(db.extract('month', BorrowRecord.borrow_date) == month,
                         db.extract('year',  BorrowRecord.borrow_date) == year)
                 .count())
        months.append(datetime(year, month, 1).strftime('%b %Y'))
        counts.append(count)
    return {'labels': months, 'data': counts}

@admin_bp.route('/scanner')
@login_required
@admin_required
def scanner():
    return render_template('admin/scanner.html')
