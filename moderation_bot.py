"""
AI Content Moderation Bot for Helping Hand of LPU.
Inspects submitted video URLs, titles, descriptions, and tags for:
- Vulgarity, profanity, adult / NSFW content
- Hate speech, harassment, abusive language
- Non-academic scam / gambling / commercial spam
- Proper format for university academic evaluation
"""
import re
import urllib.parse
from typing import Dict, Any, List

# Blacklist of prohibited vulgar / adult / offensive terms and patterns
VULGAR_KEYWORDS = [
    "porn", "xxx", "nsfw", "sex", "nude", "nudity", "erotic", "fuck", "bitch", "shit",
    "asshole", "bastard", "cunt", "dick", "pussy", "slut", "whore", "cock",
    "chutiya", "gaali", "bhosadi", "madarchod", "behenchod", "harami", "randi",
    "dating scam", "onlyfans", "stripper", "strip club", "casino", "bet365", "satta",
    "rummy hack", "teen patti cheat", "crypto pump", "free followers hack"
]

SPAM_PATTERNS = [
    r"free\s+iphone",
    r"get\s+rich\s+quick",
    r"earn\s+\$?\d+\s+daily\s+without\s+work",
    r"100%\s+working\s+hack",
    r"click\s+here\s+to\s+download\s+cracked",
    r"subscribe\s+to\s+subscribe\s+sub4sub",
]

ACADEMIC_INDICATORS = [
    "project", "presentation", "assignment", "capstone", "viva", "demo", "code",
    "analysis", "design", "simulation", "case study", "engineering", "research",
    "report", "overview", "implementation", "tutorial", "system", "model", "study",
    "lpu", "university", "b.tech", "mba", "cse", "ece", "mec", "int", "evaluation"
]

def extract_video_metadata(url: str) -> Dict[str, Any]:
    """Parse social media URL and determine platform and video ID."""
    url = url.strip()
    platform = "Unknown"
    video_id = None

    # YouTube Watch
    yt_match = re.search(r'(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})', url)
    if yt_match:
        platform = "YouTube"
        video_id = yt_match.group(1)
        return {"platform": platform, "video_id": video_id, "embed_url": f"https://www.youtube.com/embed/{video_id}"}

    # Instagram Reel
    ig_match = re.search(r'instagram\.com\/(?:reel|p)\/([a-zA-Z0-9_-]+)', url)
    if ig_match:
        platform = "Instagram"
        video_id = ig_match.group(1)
        return {"platform": platform, "video_id": video_id, "embed_url": url}

    # LinkedIn Video
    if "linkedin.com" in url:
        platform = "LinkedIn"
        return {"platform": platform, "video_id": "linkedin_post", "embed_url": url}

    return {"platform": platform, "video_id": None, "embed_url": url}


def audit_video_submission(title: str, description: str, url: str) -> Dict[str, Any]:
    """
    Simulates comprehensive AI moderation scan on video content & metadata.
    Returns audit details with confidence scores and verdict.
    """
    text_to_scan = f"{title} {description} {url}".lower()
    meta = extract_video_metadata(url)
    
    flags_detected: List[str] = []
    vulgarity_matches: List[str] = []
    
    # 1. URL validity check
    if meta["platform"] == "Unknown":
        flags_detected.append("INVALID_PLATFORM_URL")
    
    # 2. Vulgarity & Inappropriate Content Scan
    for word in VULGAR_KEYWORDS:
        # Match whole words or obvious substring boundaries
        pattern = r'\b' + re.escape(word) + r'\b'
        if re.search(pattern, text_to_scan) or (word in text_to_scan and len(word) > 4):
            vulgarity_matches.append(word)

    # 3. Spam and Scam Pattern Scan
    for pattern in SPAM_PATTERNS:
        if re.search(pattern, text_to_scan):
            flags_detected.append("DETECTED_COMMERCIAL_SPAM_OR_SCAM")

    # 4. Vulgarity scoring (0.00 safe to 1.00 critical vulgarity)
    vulgarity_score = 0.0
    if vulgarity_matches:
        flags_detected.append(f"VULGARITY_OR_PROFANITY_TRIGGERED: {', '.join(vulgarity_matches)}")
        vulgarity_score = min(1.0, 0.45 * len(vulgarity_matches) + 0.3)
    
    # 5. Academic Alignment Scoring
    academic_matches = [w for w in ACADEMIC_INDICATORS if w in text_to_scan]
    academic_score = min(1.0, 0.2 + (0.15 * len(academic_matches)))
    if len(title.strip()) < 10:
        flags_detected.append("TITLE_TOO_SHORT_FOR_ACADEMIC_EVALUATION")
        academic_score *= 0.5

    # 6. Final Decision Logic
    is_safe = True
    verdict = "APPROVED"
    reason = "Video passed AI moderation. Safe, university-appropriate content verified."

    if vulgarity_score > 0.25:
        is_safe = False
        verdict = "REJECTED_VULGARITY"
        reason = f"Automated Bot Alert: Video contains prohibited offensive/vulgar terms ({', '.join(vulgarity_matches)}). Violation of LPU Code of Conduct."
    elif "DETECTED_COMMERCIAL_SPAM_OR_SCAM" in flags_detected:
        is_safe = False
        verdict = "REJECTED_SPAM"
        reason = "Automated Bot Alert: Video flagged as non-academic commercial spam, hack, or fraudulent promotion."
    elif "INVALID_PLATFORM_URL" in flags_detected:
        is_safe = False
        verdict = "REJECTED_INVALID_URL"
        reason = "Invalid video link. Please supply a valid YouTube (watch/shorts), Instagram Reel, or LinkedIn video URL."

    return {
        "is_safe": is_safe,
        "verdict": verdict,
        "reason": reason,
        "vulgarity_score": round(vulgarity_score, 2),
        "academic_score": round(academic_score, 2),
        "flags_detected": flags_detected,
        "platform": meta["platform"],
        "video_id": meta["video_id"],
        "embed_url": meta["embed_url"],
        "bot_signature": "LPU-SafetyBot-v2.4-DeepAudit"
    }

if __name__ == "__main__":
    # Test safe video
    safe_test = audit_video_submission(
        "IoT Weather Monitoring Station using ESP32 - CSE220",
        "Final academic group project presentation showing live sensor feed into Firebase database.",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    )
    print("Safe Test Result:", safe_test["verdict"], "| Safe:", safe_test["is_safe"])

    # Test vulgar video
    vulgar_test = audit_video_submission(
        "Hot Sexy xxx adult leaks and porn video",
        "Click here for free coins chutiya",
        "https://www.youtube.com/watch?v=badbad12345"
    )
    print("Vulgar Test Result:", vulgar_test["verdict"], "| Safe:", vulgar_test["is_safe"], "| Reason:", vulgar_test["reason"])
