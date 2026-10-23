"""
Database manager and seed data for Helping Hand of LPU.
Zero-dependency SQLite persistent database.
"""
import sqlite3
import os
import json
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lpu_helping_hand.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reg_no TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        school TEXT NOT NULL,
        course TEXT NOT NULL,
        likes_given INTEGER DEFAULT 0,
        comments_given INTEGER DEFAULT 0,
        paid_passes INTEGER DEFAULT 0,
        reputation INTEGER DEFAULT 100,
        avatar_seed TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Videos table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        url TEXT NOT NULL,
        platform TEXT NOT NULL,
        youtube_id TEXT,
        school TEXT NOT NULL,
        course_code TEXT NOT NULL,
        section TEXT,
        deadline TEXT,
        target_likes INTEGER DEFAULT 50,
        target_comments INTEGER DEFAULT 20,
        current_likes INTEGER DEFAULT 0,
        current_comments INTEGER DEFAULT 0,
        status TEXT DEFAULT 'APPROVED', -- PENDING, APPROVED, REJECTED
        moderation_score REAL DEFAULT 0.98,
        moderation_verdict TEXT DEFAULT 'Passed content moderation successfully.',
        is_paid_boost INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Interactions table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        type TEXT NOT NULL, -- 'LIKE' or 'COMMENT'
        content TEXT,
        bot_verified INTEGER DEFAULT 1,
        bot_confidence REAL DEFAULT 0.95,
        bot_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (video_id) REFERENCES videos(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    # Moderation Logs
    cur.execute("""
    CREATE TABLE IF NOT EXISTS moderation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        video_id INTEGER,
        title TEXT NOT NULL,
        url TEXT NOT NULL,
        vulgarity_score REAL NOT NULL,
        academic_score REAL NOT NULL,
        flags_detected TEXT,
        verdict TEXT NOT NULL,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Payments table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        plan_name TEXT NOT NULL,
        amount_inr INTEGER NOT NULL,
        transaction_id TEXT UNIQUE NOT NULL,
        payment_method TEXT NOT NULL,
        status TEXT DEFAULT 'SUCCESS',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """)

    conn.commit()
    conn.close()

def seed_sample_data():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        # Prepopulate demo students
        users = [
            ("12108492", "Aarav Sharma", "aarav.12108492@lpu.in", "School of Computer Science & Engineering", "B.Tech CSE", 11, 6, 0, "Aarav"),
            ("12214309", "Simran Kaur", "simran.12214309@lpu.in", "Mittal School of Business", "MBA Digital Marketing", 8, 3, 0, "Simran"),
            ("12019844", "Gurpreet Singh", "gurpreet.12019844@lpu.in", "School of Mechanical Engineering", "B.Tech Robotics", 4, 1, 1, "Gurpreet"),
            ("12301122", "Ananya Reddy", "ananya.12301122@lpu.in", "School of Computer Applications", "MCA Cloud Computing", 15, 8, 0, "Ananya"),
            ("12209931", "Vikramaditya Rao", "vikram.12209931@lpu.in", "School of Bioengineering & Biosciences", "B.Tech Biotech", 0, 0, 0, "Vikram"),
        ]
        cur.executemany("""
            INSERT INTO users (reg_no, name, email, school, course, likes_given, comments_given, paid_passes, avatar_seed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, users)

        # Seed sample project videos
        sample_videos = [
            (
                1, # Aarav
                "Autonomous Self-Balancing Bot using Arduino & PID - Capstone Project",
                "Demonstration of 2-wheel self-balancing robot with MPU6050 gyroscope and Arduino Uno. Submitted for CSE423 Capstone evaluation.",
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "YouTube",
                "dQw4w9WgXcQ",
                "School of Computer Science & Engineering",
                "CSE423",
                "K21AB",
                "2026-11-05",
                50,
                20,
                38,
                14,
                "APPROVED",
                0.99,
                "Content safe, technical academic demo verified.",
                0
            ),
            (
                2, # Simran
                "Social Media Viral Marketing Strategy for EV Scooters in Punjab",
                "Comprehensive digital marketing campaign breakdown, consumer sentiment analysis, and reel engagement testing for MGT518.",
                "https://www.youtube.com/watch?v=L_LUpnjgPso",
                "YouTube",
                "L_LUpnjgPso",
                "Mittal School of Business",
                "MGT518",
                "B2201",
                "2026-11-02",
                60,
                25,
                49,
                19,
                "APPROVED",
                0.97,
                "Business presentation compliant with LPU assignment rubric.",
                0
            ),
            (
                3, # Gurpreet
                "CAD Modelling & Stress Analysis of Quadcopter Chassis in ANSYS",
                "Finite Element Analysis (FEA) results and structural deformation simulation under 4G aerodynamic loading for MEC342.",
                "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
                "YouTube",
                "fJ9rUzIMcZQ",
                "School of Mechanical Engineering",
                "MEC342",
                "M2004",
                "2026-10-30",
                40,
                15,
                34,
                12,
                "APPROVED",
                0.99,
                "Engineering video verified. No inappropriate elements.",
                1
            ),
            (
                4, # Ananya
                "Full Stack AI Tutor Web App using Next.js & Gemini API",
                "Live demonstration of automated doubt-clearing portal built for college students. Final term project for INT219 Web Dev.",
                "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",
                "YouTube",
                "3JZ_D3ELwOQ",
                "School of Computer Applications",
                "INT219",
                "C2311",
                "2026-11-10",
                50,
                20,
                42,
                18,
                "APPROVED",
                0.98,
                "Code demo and UI walkthrough verified as high-standard academic submission.",
                0
            )
        ]

        cur.executemany("""
            INSERT INTO videos (user_id, title, description, url, platform, youtube_id, school, course_code, section, deadline,
                               target_likes, target_comments, current_likes, current_comments, status, moderation_score, moderation_verdict, is_paid_boost)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_videos)

        # Seed realistic peer comments
        sample_comments = [
            (1, 2, "COMMENT", "Great explanation of the PID tuning process! Did you use Ziegler-Nichols method for calculating Kp and Kd?"),
            (1, 4, "COMMENT", "Very clean hardware cable management. Good luck with the final capstone viva!"),
            (2, 1, "COMMENT", "The segmentation strategy for tier-2 Punjab cities is spot on. Loved the ROI calculations!"),
            (3, 4, "COMMENT", "Stress concentration factor near the motor arms looks well reinforced in the ANSYS mesh."),
            (4, 1, "COMMENT", "UI responsiveness looks buttery smooth. Are you using Tailwind CSS for the frontend?"),
        ]
        cur.executemany("""
            INSERT INTO interactions (video_id, user_id, type, content, bot_verified, bot_confidence, bot_reason)
            VALUES (?, ?, ?, ?, 1, 0.98, 'Genuine peer academic review detected by Verification Bot')
        """, sample_comments)

        # Moderation log seed
        cur.execute("""
            INSERT INTO moderation_logs (video_id, title, url, vulgarity_score, academic_score, flags_detected, verdict, details)
            VALUES 
            (1, 'Autonomous Self-Balancing Bot using Arduino', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ', 0.01, 0.99, 'None', 'APPROVED', 'Robotics project demonstration with clear academic title & valid university format.'),
            (NULL, 'Get Free Game Currency Hack 100% Working Click Here', 'https://youtu.be/fake_spam_video', 0.88, 0.05, 'SPAM, SCAM, MISLEADING', 'REJECTED', 'Automated Bot detected clickbait scam keywords violating LPU project policies.')
        """)

        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    seed_sample_data()
    print("Database initialized and sample data seeded successfully.")
