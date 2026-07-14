import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'database', 'library.db')

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("ALTER TABLE fines ADD COLUMN razorpay_order_id VARCHAR(100)")
    c.execute("ALTER TABLE fines ADD COLUMN razorpay_payment_id VARCHAR(100)")
    conn.commit()
    conn.close()
    print("Successfully added razorpay columns to fines table.")
except Exception as e:
    print("Error:", e)
