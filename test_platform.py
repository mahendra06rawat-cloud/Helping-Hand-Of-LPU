"""
Automated End-to-End Test Suite for Helping Hand of LPU.
Tests:
1. Student eligibility gate check (10 likes, 5 comments rule)
2. AI Content Moderation Bot (blocking vulgarity and spam)
3. Engagement Verification Bot (auditing authentic vs spam comments)
4. Instant Pass Payment bypass
5. Video upload lifecycle
"""
import sys
import os
import json
import urllib.request
import urllib.error
import threading
import time

# Ensure import from current dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from server import ThreadingHTTPServer, LPURequestHandler, PORT
from database import init_db, seed_sample_data, get_connection

def run_tests():
    print("--- 1. Initializing DB & Starting Background Server ---")
    init_db()
    seed_sample_data()

    # Start test server on port 8085 to avoid conflicts
    test_port = 8085
    server = ThreadingHTTPServer(("127.0.0.1", test_port), LPURequestHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(1)

    base_url = f"http://127.0.0.1:{test_port}"

    def get(path):
        req = urllib.request.Request(f"{base_url}{path}")
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def post(path, data):
        req = urllib.request.Request(
            f"{base_url}{path}",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return json.loads(resp.read().decode("utf-8")), resp.status
        except urllib.error.HTTPError as e:
            return json.loads(e.read().decode("utf-8")), e.code

    print("\n--- 2. Testing Current User & Criteria Meter ---")
    res = get("/api/user/current")
    assert res["success"] is True, "Failed to get current user"
    user = res["user"]
    print(f"Current User: {user['name']} ({user['reg_no']})")
    print(f"Likes: {user['eligibility']['likes_given']}/10, Comments: {user['eligibility']['comments_given']}/5, Eligible: {user['eligibility']['is_eligible']}")

    print("\n--- 3. Testing Engagement Verification Bot (Spam Comment Filtering) ---")
    # Test submitting a spam single-word comment
    spam_data, code = post("/api/videos/1/comment", {"comment": "nice", "watch_seconds": 10})
    print("Spam comment test response:", spam_data["error"], "(Status:", code, ")")
    assert code == 422, "Expected 422 for spam comment"
    assert "too short" in spam_data["error"].lower() or "spam" in spam_data["error"].lower()

    # Test submitting authentic constructive peer review
    good_comment = "The circuit explanation and PCB layout for the Arduino balancing robot was very thorough."
    good_data, code = post("/api/videos/1/comment", {"comment": good_comment, "watch_seconds": 10})
    print("Authentic comment response:", good_data["message"], "(Status:", code, ")")
    assert code == 200, "Expected 200 for authentic comment"
    assert good_data["verification"]["verified"] is True

    print("\n--- 4. Testing AI Content Moderation Bot (Vulgarity Detection) ---")
    # Switch to student with eligible credits: Aarav (ID 1 has 11 likes and 6 comments)
    post("/api/user/switch", {"user_id": 1})
    
    # Try uploading a video containing prohibited vulgar/adult keywords
    vulgar_video = {
        "title": "Watch hot adult xxx strip leaks chutiya",
        "description": "Click here for free coins porn hack",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "course_code": "CSE423",
        "section": "K21AB"
    }
    vulgar_res, v_code = post("/api/videos/submit", vulgar_video)
    print("Vulgar Video Moderation Output:", vulgar_res["error"], "(Status:", v_code, ")")
    assert v_code == 422, "Vulgar video should be rejected by AI Moderation Bot!"
    assert "prohibited offensive/vulgar terms" in vulgar_res["error"]

    print("\n--- 5. Testing Legitimate Academic Video Submission ---")
    safe_video = {
        "title": "Smart Campus Waste Management System using YOLOv8 - CSE423",
        "description": "Automated recyclable object segregation demo and hardware servo test for final evaluation marks.",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "course_code": "CSE423",
        "section": "K21AB",
        "target_likes": 50,
        "target_comments": 20
    }
    safe_res, s_code = post("/api/videos/submit", safe_video)
    print("Academic Video Submission Output:", safe_res["message"], "(Status:", s_code, ")")
    assert s_code == 200, "Legitimate academic video must pass moderation"
    assert safe_res["moderation_audit"]["is_safe"] is True

    print("\n--- 6. Testing Gatekeeper on Ineligible Student (Vikram - 0 likes, 0 comments) ---")
    # Switch to Vikram (ID 5 has 0 likes, 0 comments, 0 paid passes)
    post("/api/user/switch", {"user_id": 5})
    locked_res, l_code = post("/api/videos/submit", safe_video)
    print("Gatekeeper check on Vikram:", locked_res["error"], "(Status:", l_code, ")")
    assert l_code == 403, "Ineligible student must be blocked from uploading!"
    assert "Submission Locked" in locked_res["error"]

    print("\n--- 7. Testing Instant Pass Payment Bypass ---")
    # Vikram purchases Instant Pass for ₹49
    pay_res, p_code = post("/api/payment/purchase-pass", {
        "plan_name": "Instant Project Boost",
        "amount": 49,
        "payment_method": "UPI (GPay)"
    })
    print("Payment execution:", pay_res["message"], "(Status:", p_code, ")")
    assert p_code == 200
    assert pay_res["eligibility_unlocked"] is True

    # Now Vikram tries uploading with his paid pass:
    bypass_res, b_code = post("/api/videos/submit", safe_video)
    print("Upload with Instant Pass:", bypass_res["message"], "(Status:", b_code, ")")
    assert b_code == 200, "Instant pass should successfully bypass like/comment criteria!"

    print("\n--- ALL TESTS PASSED SUCCESSFULLY! 100% VERIFIED ---")
    server.shutdown()

if __name__ == "__main__":
    run_tests()
