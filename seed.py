"""
seed.py — Run once to create demo accounts and seed categories.
Usage: python seed.py
"""
from app import create_app
from models import db
from models.user import User
from models.book import Book, Category
from datetime import datetime


def seed():
    app = create_app()
    with app.app_context():
        db.create_all()

        # ── Categories ────────────────────────────────────────
        cats = [
            ('Computer Science', 'fa-laptop-code', '#6366f1'),
            ('Mathematics',      'fa-calculator',  '#10b981'),
            ('Physics',          'fa-atom',        '#3b82f6'),
            ('Literature',       'fa-feather-alt', '#f59e0b'),
            ('History',          'fa-landmark',    '#ec4899'),
            ('Biology',          'fa-dna',         '#8b5cf6'),
            ('Engineering',      'fa-cogs',        '#ef4444'),
            ('Economics',        'fa-chart-line',  '#f97316'),
        ]
        for name, icon, color in cats:
            if not Category.query.filter_by(name=name).first():
                db.session.add(Category(name=name, icon=icon, color=color))
        db.session.commit()
        print("[OK] Categories seeded")

        # -- Demo Users ---
        users = [
            dict(username='admin',   email='admin@edulib.com',   full_name='System Admin',      role='admin',   password='admin123',   employee_id='EMP001'),
            dict(username='teacher1',email='teacher@edulib.com',  full_name='Dr. Priya Sharma',  role='teacher', password='teacher123', department='Computer Science', employee_id='FAC001'),
            dict(username='student1',email='student@edulib.com',  full_name='Arjun Kumar',       role='student', password='student123', student_id='STU2024001'),
            dict(username='student2',email='student2@edulib.com', full_name='Sneha Reddy',       role='student', password='student123', student_id='STU2024002'),
        ]
        for u in users:
            if not User.query.filter_by(email=u['email']).first():
                user = User(
                    username=u['username'], email=u['email'],
                    full_name=u['full_name'], role=u['role'],
                    department=u.get('department'),
                    student_id=u.get('student_id'),
                    employee_id=u.get('employee_id'),
                    is_active=True,
                )
                user.set_password(u['password'])
                db.session.add(user)
        db.session.commit()
        print("[OK] Demo users seeded")

        # -- Sample Books --
        cs_cat = Category.query.filter_by(name='Computer Science').first()
        math_cat = Category.query.filter_by(name='Mathematics').first()
        admin_user = User.query.filter_by(role='admin').first()

        sample_books = [
            dict(title='Python Crash Course', author='Eric Matthes', isbn='9781593279288',
                 publisher='No Starch Press', published_year=2019, category_id=cs_cat.id if cs_cat else None,
                 copies_total=5, copies_available=3, description='A hands-on, project-based introduction to programming.',
                 has_ebook=False, location='A-1-Row 1',
                 tags='python, programming, beginner'),
            dict(title='Introduction to Algorithms', author='Thomas H. Cormen', isbn='9780262033848',
                 publisher='MIT Press', published_year=2009, category_id=cs_cat.id if cs_cat else None,
                 copies_total=3, copies_available=2, description='The most comprehensive textbook on algorithms.',
                 location='A-2-Row 3', tags='algorithms, data structures, computer science'),
            dict(title='Calculus: Early Transcendentals', author='James Stewart', isbn='9781285741550',
                 publisher='Cengage Learning', published_year=2015, category_id=math_cat.id if math_cat else None,
                 copies_total=8, copies_available=6, description='Comprehensive calculus textbook.',
                 location='B-1-Row 1', tags='calculus, mathematics, engineering'),
        ]

        for bd in sample_books:
            if not Book.query.filter_by(isbn=bd['isbn']).first():
                book = Book(**bd, added_by=admin_user.id if admin_user else None)
                db.session.add(book)
        db.session.commit()
        print("[OK] Sample books seeded")

        print("\nSeeding complete!")
        print("\nDemo Login Credentials:")
        print("  Admin:   admin@edulib.com / admin123")
        print("  Teacher: teacher@edulib.com / teacher123")
        print("  Student: student@edulib.com / student123")
        print("\nRun: flask run")


if __name__ == '__main__':
    seed()
