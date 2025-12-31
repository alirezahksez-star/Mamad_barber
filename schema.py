import psycopg2
import os 
from dotenv import load_dotenv

load_dotenv()

D_URL = os.getenv('D_URL') 



def connect_t ():
    
    conn = psycopg2.connect(D_URL)
    cur = conn.cursor()

    # جدول کاربران
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        user_name TEXT
    )
    """)

    # جدول نوبت‌ها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS slot (
        slot_id SERIAL PRIMARY KEY,
        slot_date TEXT NOT NULL,
        slot_time TEXT NOT NULL,
        slot_status INTEGER DEFAULT 1
    )
    """)
    # slot_status: 1 = آزاد, 0 = رزرو شده

    # جدول رزروها
    cur.execute("""
    CREATE TABLE IF NOT EXISTS appt (
        app_id SERIAL PRIMARY KEY,
        user_id TEXT NOT NULL,
        slot_id INTEGER NOT NULL UNIQUE,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (slot_id) REFERENCES slot(slot_id) ON DELETE CASCADE
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    connect_t()
    print("✅ دیتابیس و جداول با موفقیت ساخته شدند.")
    
