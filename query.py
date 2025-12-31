import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

D_URL = os.getenv("D_URL")

# ------------------ اتصال ------------------
def connect():
    return psycopg2.connect(D_URL)


# ------------------ Users ------------------
def insert_user(user_id, user_name):
    """اضافه کردن کاربر (اگر وجود نداشت)"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (user_id, user_name)
            VALUES (%s, %s)
            ON CONFLICT (user_id) DO NOTHING
            """,
            (user_id, user_name)
        )


# ------------------ Slots ------------------
def show_slot_dates():
    """برگرداندن تاریخ‌هایی که اسلات آزاد دارند"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT DISTINCT slot_date
            FROM slot
            WHERE slot_status = 1
            ORDER BY slot_date
            """
        )
        return [row[0] for row in cur.fetchall()]


def show_times_by_date(date):
    """برگرداندن ساعت‌های آزاد یک تاریخ"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT slot_id, slot_time
            FROM slot
            WHERE slot_date = %s
              AND slot_status = 1
            ORDER BY slot_time
            """,
            (date,)
        )
        return cur.fetchall()


# ------------------ Booking ------------------
def book_appointment(user_id, slot_id):
    """
    رزرو نوبت:
    1. ثبت در appt
    2. تغییر وضعیت slot
    """
    with connect() as conn:
        cur = conn.cursor()

        # ثبت رزرو
        cur.execute(
            """
            INSERT INTO appt (user_id, slot_id)
            VALUES (%s, %s)
            """,
            (user_id, slot_id)
        )

        # قفل کردن اسلات
        cur.execute(
            """
            UPDATE slot
            SET slot_status = 0
            WHERE slot_id = %s
            """,
            (slot_id,)
        )


# ------------------ Admin ------------------
def insert_slots(date, times):
    """اضافه کردن چند اسلات برای یک تاریخ"""
    with connect() as conn:
        cur = conn.cursor()
        for t in times:
            cur.execute(
                """
                INSERT INTO slot (slot_date, slot_time, slot_status)
                VALUES (%s, %s, 1)
                """,
                (date, t)
            )


def delete_all_slots():
    """حذف تمام اسلات‌ها و رزروها"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM appt")
        cur.execute("DELETE FROM slot")


# ------------------ Get Appointments ------------------
def get_user_appointments(user_id):
    """گرفتن نوبت‌های یک کاربر"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.slot_date, s.slot_time
            FROM appt a
            JOIN slot s ON a.slot_id = s.slot_id
            WHERE a.user_id = %s
            ORDER BY s.slot_date, s.slot_time
            """,
            (user_id,)
        )
        return cur.fetchall()


def get_admin_appointments():
    """گرفتن همه نوبت‌ها برای ادمین"""
    with connect() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT s.slot_date, s.slot_time, u.user_name
            FROM appt a
            JOIN slot s ON a.slot_id = s.slot_id
            JOIN users u ON a.user_id = u.user_id
            ORDER BY s.slot_date, s.slot_time
            """
        )
        return cur.fetchall()
