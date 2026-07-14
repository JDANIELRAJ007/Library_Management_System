import random
import uuid
import os
from app import create_app
from models import db
from models.book import Book, Category
from models.user import User
from reportlab.pdfgen import canvas

def create_placeholder_pdf(title, filename):
    app = create_app()
    with app.app_context():
        pdf_path = os.path.join(app.config['EBOOK_FOLDER'], filename)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, f"Placeholder E-Book for: {title}")
        c.drawString(100, 730, "This is an auto-generated placeholder file.")
        c.save()

def generate_fake_books():
    app = create_app()
    with app.app_context():
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            print("No admin user found.")
            return

        categories_data = [
            ('Computer Science', '#6366f1', ['Python', 'Java', 'Algorithms', 'AI', 'Machine Learning', 'Databases', 'Web Dev']),
            ('Mathematics', '#10b981', ['Calculus', 'Algebra', 'Geometry', 'Statistics', 'Topology', 'Number Theory']),
            ('Physics', '#3b82f6', ['Quantum Mechanics', 'Thermodynamics', 'Relativity', 'Optics', 'Astrophysics']),
            ('Literature', '#f59e0b', ['Shakespeare', 'Modern Poetry', 'Classic Novels', 'Creative Writing']),
            ('History', '#ec4899', ['World War II', 'Ancient Rome', 'Medieval Europe', 'Cold War', 'Renaissance']),
            ('Biology', '#8b5cf6', ['Genetics', 'Evolution', 'Cell Biology', 'Anatomy', 'Ecology']),
            ('Economics', '#f97316', ['Microeconomics', 'Macroeconomics', 'Finance', 'Game Theory', 'Global Markets'])
        ]

        authors = ['John Doe', 'Jane Smith', 'Alice Johnson', 'Robert Williams', 'Emily Brown', 'Michael Davis', 'Sarah Miller', 'David Wilson']
        adjectives = ['Advanced', 'Introduction to', 'Mastering', 'Fundamentals of', 'Applied', 'Modern', 'Essential', 'The Art of']

        total_added = 0
        for cat_name, color, topics in categories_data:
            category = Category.query.filter_by(name=cat_name).first()
            if not category:
                category = Category(name=cat_name, color=color)
                db.session.add(category)
                db.session.commit()

            for _ in range(15):  # 15 books per category * 7 categories = 105 books
                topic = random.choice(topics)
                adj = random.choice(adjectives)
                title = f"{adj} {topic}"
                author = random.choice(authors)
                isbn = f"978{random.randint(1000000000, 9999999999)}"
                pub_year = random.randint(1990, 2026)

                if Book.query.filter_by(title=title).first(): continue

                pdf_filename = f"{uuid.uuid4().hex}.pdf"
                create_placeholder_pdf(title, pdf_filename)

                book = Book(
                    title=title,
                    author=author,
                    isbn=isbn,
                    published_year=pub_year,
                    category_id=category.id,
                    copies_total=random.randint(3, 10),
                    copies_available=random.randint(1, 10),
                    description=f"A comprehensive guide on {topic} written by {author}.",
                    cover_image='',
                    has_ebook=True,
                    pdf_file=pdf_filename,
                    added_by=admin.id
                )
                db.session.add(book)
                total_added += 1

        db.session.commit()
        print(f"Successfully generated and added {total_added} local books to the catalog!")

if __name__ == '__main__':
    generate_fake_books()
