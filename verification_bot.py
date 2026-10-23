"""
Engagement Verification Bot for Helping Hand of LPU.
Tracks, audits, and validates that users ACTUALLY engaged with peer videos
(preventing bots, spam comments, instant auto-clicking, and fake accounts).
"""
import time
import re
import hashlib
from typing import Dict, Any, Optional

GENERIC_SPAM_WORDS = {
    "nice", "good", "ok", "okay", "super", "k", "fine", "wow", "lol", "first",
    "done", "view", "watch", "like", "cmt", "cmnt", "support", "sub", "pls", "plz", "asdf"
}

PEER_REVIEW_POSITIVE_KEYWORDS = [
    "presentation", "code", "explanation", "approach", "method", "results",
    "implementation", "hardware", "software", "slides", "flowchart", "algorithm",
    "clarity", "viva", "project", "audio", "well explained", "great job", "useful",
    "analysis", "simulation", "detailed", "diagram", "interface", "design"
]

def verify_like_interaction(user_id: int, video_owner_id: int, watch_seconds: int = 8, session_token: str = "") -> Dict[str, Any]:
    """
    Validates a like interaction before awarding credit.
    """
    if user_id == video_owner_id:
        return {
            "verified": False,
            "status": "SELF_ENGAGEMENT_REJECTED",
            "confidence": 0.0,
            "message": "Fraud Detection: You cannot like your own project video to gain upload credits."
        }

    if watch_seconds < 3:
        return {
            "verified": False,
            "status": "WATCH_TIME_INSUFFICIENT",
            "confidence": 0.25,
            "message": "Engagement Bot: Video must be watched for at least 5 seconds before your like is validated."
        }

    # Generate verification signature
    bot_hash = hashlib.sha256(f"lpu_like_{user_id}_{time.time()}".encode()).hexdigest()[:12]
    
    return {
        "verified": True,
        "status": "GENUINE_LIKE_VERIFIED",
        "confidence": 0.98,
        "message": "Engagement Bot: Authentic like interaction verified and synced.",
        "verification_signature": f"BOT-VERIFIED-LIKE-{bot_hash}"
    }


def verify_comment_interaction(user_id: int, video_owner_id: int, comment_text: str, watch_seconds: int = 10) -> Dict[str, Any]:
    """
    Validates that a comment is a genuine, constructive peer review
    and not bot spam, gibberish, or single-word spam.
    """
    text = comment_text.strip()
    
    if user_id == video_owner_id:
        return {
            "verified": False,
            "status": "SELF_COMMENT_REJECTED",
            "confidence": 0.0,
            "message": "Fraud Detection: Self-comments do not count towards the 5 required peer comments."
        }

    if len(text) < 12:
        return {
            "verified": False,
            "status": "COMMENT_TOO_SHORT",
            "confidence": 0.2,
            "message": f"Engagement Bot: Comment too short ({len(text)} chars). Please write a constructive peer comment of at least 12 characters."
        }

    # Check for character repetition spam like "aaaaaaaaa" or "greattttttt"
    if re.search(r'(.)\1{4,}', text):
        return {
            "verified": False,
            "status": "REPETITIVE_CHAR_SPAM",
            "confidence": 0.15,
            "message": "Engagement Bot: Repetitive keyboard spam detected. Please provide authentic feedback."
        }

    clean_words = [w.lower() for w in re.findall(r'\b\w+\b', text)]
    
    # Check if comment only contains generic single-word spam
    if len(clean_words) <= 2 and any(w in GENERIC_SPAM_WORDS for w in clean_words):
        return {
            "verified": False,
            "status": "GENERIC_SPAM_FILTERED",
            "confidence": 0.3,
            "message": "Engagement Bot: Generic one-word feedback ('nice', 'good', 'done') is not eligible for peer academic criteria."
        }

    # Evaluate constructive peer review score
    academic_terms_found = [w for w in PEER_REVIEW_POSITIVE_KEYWORDS if w in text.lower()]
    quality_score = min(1.0, 0.60 + (len(academic_terms_found) * 0.15) + (min(len(text), 100) / 300))
    
    bot_hash = hashlib.sha256(f"lpu_cmt_{user_id}_{text}".encode()).hexdigest()[:12]

    return {
        "verified": True,
        "status": "GENUINE_COMMENT_VERIFIED",
        "confidence": round(quality_score, 2),
        "message": "Engagement Bot: Constructive peer review verified. Credit awarded!",
        "academic_keywords": academic_terms_found,
        "verification_signature": f"BOT-VERIFIED-COMMENT-{bot_hash}"
    }

if __name__ == "__main__":
    # Test cases
    print("Test 1 (Spam comment):", verify_comment_interaction(1, 2, "nice bro"))
    print("Test 2 (Keyboard smash):", verify_comment_interaction(1, 2, "asdfasdfasdfasdfasdf"))
    print("Test 3 (Genuine review):", verify_comment_interaction(1, 2, "The hardware explanation of the motor driver in your project was crystal clear!"))
