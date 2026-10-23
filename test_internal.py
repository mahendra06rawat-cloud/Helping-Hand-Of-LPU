"""
Direct Unit & Integration Test Suite for Helping Hand of LPU.
Tests core platform logic directly:
1. AI Content Moderation Bot logic (vulgarity, spam, URL parsing, scoring)
2. Engagement Verification Bot (spam comments, minimum length, authentic review)
3. Database queries and integrity
4. Eligibility gatekeeping calculations (10 likes, 5 comments rule vs Instant Pass)
"""
import sys
import os
import sqlite3

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
from database import init_db, seed_sample_data, get_connection
from moderation_bot import audit_video_submission, extract_video_metadata
from verification_bot import verify_like_interaction, verify_comment_interaction

def test_moderation_bot():
    print("-> Testing AI Content Moderation Bot...")
    
    # 1. Safe Academic Video
    safe = audit_video_submission(
        "Autonomous Micro-Drone Object Detection Project - CSE423 Capstone",
        "Demonstration of real-time obstacle avoidance and aerial stability for evaluation.",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    assert safe["is_safe"] is True, "Safe video should be approved"
    assert safe["verdict"] == "APPROVED"
    assert safe["vulgarity_score"] < 0.2
    assert safe["platform"] == "YouTube"
    print("   ✓ Safe academic submission verified and approved.")

    # 2. Vulgar / Prohibited Content
    vulgar = audit_video_submission(
        "Free hot porn and xxx adult leak video chutiya",
        "Download dating scam here",
        "https://www.youtube.com/watch?v=bad12345678"
    )
    assert vulgar["is_safe"] is False, "Vulgar video should be blocked"
    assert vulgar["verdict"] == "REJECTED_VULGARITY"
    assert vulgar["vulgarity_score"] > 0.3
    print("   ✓ Vulgarity detector successfully blocked prohibited submission.")

    # 3. Spam / Scam Pattern
    spam = audit_video_submission(
        "Get rich quick earn $500 daily without work",
        "Click here to download cracked software 100% working hack",
        "https://www.youtube.com/watch?v=spam1234567"
    )
    assert spam["is_safe"] is False, "Scam should be blocked"
    assert spam["verdict"] == "REJECTED_SPAM"
    print("   ✓ Commercial spam pattern successfully blocked.")


def test_engagement_verification_bot():
    print("-> Testing Engagement Verification Bot...")

    # 1. Self-like rejection (fraud prevention)
    self_like = verify_like_interaction(user_id=1, video_owner_id=1, watch_seconds=10)
    assert self_like["verified"] is False
    assert self_like["status"] == "SELF_ENGAGEMENT_REJECTED"
    print("   ✓ Self-like fraud prevention verified.")

    # 2. Insufficient watch time (<3s)
    quick_click = verify_like_interaction(user_id=1, video_owner_id=2, watch_seconds=1)
    assert quick_click["verified"] is False
    assert quick_click["status"] == "WATCH_TIME_INSUFFICIENT"
    print("   ✓ Fast click / bot watch-time requirement enforced.")

    # 3. Genuine like
    valid_like = verify_like_interaction(user_id=1, video_owner_id=2, watch_seconds=6)
    assert valid_like["verified"] is True
    assert "BOT-VERIFIED-LIKE" in valid_like["verification_signature"]
    print("   ✓ Authentic peer like verified and signed.")

    # 4. Short / Generic Spam comment ("nice", "cool")
    short_cmt = verify_comment_interaction(user_id=1, video_owner_id=2, comment_text="nice")
    assert short_cmt["verified"] is False
    assert short_cmt["status"] == "COMMENT_TOO_SHORT"
    print("   ✓ Short spam comment rejected.")

    # 5. Keystroke spam ("aaaaaaaaaa")
    repeat_cmt = verify_comment_interaction(user_id=1, video_owner_id=2, comment_text="great project aaaaaaaaaaaaaa")
    assert repeat_cmt["verified"] is False
    assert repeat_cmt["status"] == "REPETITIVE_CHAR_SPAM"
    print("   ✓ Repetitive keyboard spam rejected.")

    # 6. High-quality peer review
    genuine_cmt = verify_comment_interaction(
        user_id=1,
        video_owner_id=2,
        comment_text="Great explanation of the PID tuning process! Did you use Ziegler-Nichols method for calculating Kp and Kd?"
    )
    assert genuine_cmt["verified"] is True
    assert genuine_cmt["confidence"] >= 0.8
    assert "BOT-VERIFIED-COMMENT" in genuine_cmt["verification_signature"]
    print("   ✓ Constructive peer review authenticated.")


def test_database_and_gatekeeper():
    print("-> Testing Database & Criteria Gatekeeping...")
    init_db()
    seed_sample_data()

    conn = get_connection()
    cur = conn.cursor()

    # Verify seed users
    cur.execute("SELECT id, name, likes_given, comments_given, paid_passes FROM users")
    users = {row["name"]: dict(row) for row in cur.fetchall()}

    # Aarav: 11 likes, 6 comments -> ELIGIBLE
    aarav = users["Aarav Sharma"]
    aarav_eligible = (aarav["likes_given"] >= 10 and aarav["comments_given"] >= 5) or (aarav["paid_passes"] > 0)
    assert aarav_eligible is True
    print("   ✓ Aarav Sharma (11 likes, 6 comments): ELIGIBLE")

    # Simran: 8 likes, 3 comments -> INELIGIBLE (Needs 2 likes, 2 comments)
    simran = users["Simran Kaur"]
    simran_eligible = (simran["likes_given"] >= 10 and simran["comments_given"] >= 5) or (simran["paid_passes"] > 0)
    assert simran_eligible is False
    print("   ✓ Simran Kaur (8 likes, 3 comments): LOCKED (Correctly gated)")

    # Vikram: 0 likes, 0 comments, 0 passes -> INELIGIBLE
    vikram = users["Vikramaditya Rao"]
    vikram_eligible = (vikram["likes_given"] >= 10 and vikram["comments_given"] >= 5) or (vikram["paid_passes"] > 0)
    assert vikram_eligible is False
    print("   ✓ Vikramaditya Rao (0 likes, 0 comments): LOCKED (Correctly gated)")

    # Simulate Vikram buying an Instant Pass for ₹49
    cur.execute("UPDATE users SET paid_passes = paid_passes + 1 WHERE id = ?", (vikram["id"],))
    cur.execute("SELECT paid_passes FROM users WHERE id = ?", (vikram["id"],))
    updated_passes = cur.fetchone()[0]
    vikram_now_eligible = (vikram["likes_given"] >= 10 and vikram["comments_given"] >= 5) or (updated_passes > 0)
    assert vikram_now_eligible is True
    print("   ✓ Vikramaditya Rao after ₹49 Instant Pass: UNLOCKED & ELIGIBLE")

    conn.close()

if __name__ == "__main__":
    test_moderation_bot()
    test_engagement_verification_bot()
    test_database_and_gatekeeper()
    print("\n🎉 ALL INTERNAL TESTS PASSED WITH 100% SUCCESS!")
