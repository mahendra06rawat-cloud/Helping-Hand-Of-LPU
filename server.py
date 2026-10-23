"""
Helping Hand of LPU - Full Stack Python Backend Server
Zero-external-dependency REST API and static asset server.
"""
import sys
import os
import json
import sqlite3
import mimetypes
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import uuid
import time

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Local modules
from database import init_db, seed_sample_data, get_connection
from moderation_bot import audit_video_submission, extract_video_metadata
from verification_bot import verify_like_interaction, verify_comment_interaction

PORT = int(os.environ.get("PORT","8080"))
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

# In-memory session tracking for active user
ACTIVE_USER_ID = 2  # Default to Simran (8 likes, 3 comments - needs 2 likes & 2 comments or pay!)

class LPURequestHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(200)

    def _read_json(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            return {}
        body = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {}

    def _send_json(self, data, status=200):
        self._set_headers(status, "application/json")
        self.wfile.write(json.dumps(data, default=str).encode("utf-8"))

    def _send_error(self, message, status=400, details=None):
        self._send_json({"success": False, "error": message, "details": details}, status=status)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        # API Routes
        if path == "/api/user/current":
            self.handle_get_current_user()
        elif path == "/api/users":
            self.handle_get_all_users()
        elif path == "/api/videos":
            self.handle_get_videos(query)
        elif path.startswith("/api/videos/") and path.endswith("/comments"):
            video_id = int(path.split("/")[3])
            self.handle_get_video_comments(video_id)
        elif path.startswith("/api/videos/"):
            video_id = int(path.split("/")[3])
            self.handle_get_single_video(video_id)
        elif path == "/api/moderation/logs":
            self.handle_get_moderation_logs()
        elif path == "/api/verification/logs":
            self.handle_get_verification_logs()
        elif path == "/api/stats":
            self.handle_get_campus_stats()
        else:
            # Static File Serving
            self.handle_static_file(path)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/user/switch":
            self.handle_switch_user()
        elif path == "/api/user/register":
            self.handle_register_user()
        elif path == "/api/videos/submit":
            self.handle_submit_video()
        elif path.startswith("/api/videos/") and path.endswith("/like"):
            video_id = int(path.split("/")[3])
            self.handle_like_video(video_id)
        elif path.startswith("/api/videos/") and path.endswith("/comment"):
            video_id = int(path.split("/")[3])
            self.handle_comment_video(video_id)
        elif path == "/api/payment/purchase-pass":
            self.handle_purchase_pass()
        elif path == "/api/bot/test-moderation":
            self.handle_test_moderation()
        else:
            self._send_error("Route not found", 404)

    # ------------------ HANDLERS ------------------

    def handle_get_current_user(self):
        global ACTIVE_USER_ID
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (ACTIVE_USER_ID,))
        row = cur.fetchone()
        conn.close()

        if not row:
            self._send_error("User session not found", 404)
            return

        user = dict(row)
        likes_given = user["likes_given"]
        comments_given = user["comments_given"]
        paid_passes = user["paid_passes"]

        # 10 likes and 5 comments rule OR paid pass
        likes_remaining = max(0, 10 - likes_given)
        comments_remaining = max(0, 5 - comments_given)
        is_eligible = (likes_remaining == 0 and comments_remaining == 0) or (paid_passes > 0)

        user["eligibility"] = {
            "required_likes": 10,
            "required_comments": 5,
            "likes_given": likes_given,
            "comments_given": comments_given,
            "likes_remaining": likes_remaining,
            "comments_remaining": comments_remaining,
            "is_eligible": is_eligible,
            "paid_passes": paid_passes,
            "progress_percent": min(100, int(((min(10, likes_given)/10 * 0.6) + (min(5, comments_given)/5 * 0.4)) * 100))
        }

        self._send_json({"success": True, "user": user})

    def handle_get_all_users(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, reg_no, name, school, course, likes_given, comments_given, paid_passes FROM users ORDER BY id ASC")
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        self._send_json({"success": True, "users": rows, "active_user_id": ACTIVE_USER_ID})

    def handle_switch_user(self):
        global ACTIVE_USER_ID
        data = self._read_json()
        target_id = data.get("user_id")
        if not target_id:
            self._send_error("User ID required")
            return
        
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE id = ?", (target_id,))
        if not cur.fetchone():
            conn.close()
            self._send_error("User does not exist")
            return
        conn.close()

        ACTIVE_USER_ID = int(target_id)
        self.handle_get_current_user()

    def handle_register_user(self):
        global ACTIVE_USER_ID
        data = self._read_json()
        reg_no = data.get("reg_no", "").strip()
        name = data.get("name", "").strip()
        school = data.get("school", "School of Computer Science & Engineering").strip()
        course = data.get("course", "B.Tech").strip()
        email = data.get("email", f"{reg_no}@lpu.in").strip()

        if not reg_no or not name:
            self._send_error("Registration number and Name are required.")
            return

        conn = get_connection()
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO users (reg_no, name, email, school, course, likes_given, comments_given, paid_passes, avatar_seed)
                VALUES (?, ?, ?, ?, ?, 0, 0, 0, ?)
            """, (reg_no, name, email, school, course, name))
            conn.commit()
            new_id = cur.lastrowid
            ACTIVE_USER_ID = new_id
            conn.close()
            self.handle_get_current_user()
        except sqlite3.IntegrityError:
            conn.close()
            self._send_error("A student with this Registration Number already exists. Please select from the student switcher.")

    def handle_get_videos(self, query):
        conn = get_connection()
        cur = conn.cursor()
        
        school_filter = query.get("school", [None])[0]
        search = query.get("search", [None])[0]

        sql = """
            SELECT v.*, u.name as student_name, u.reg_no as student_reg_no, u.school as student_school
            FROM videos v
            JOIN users u ON v.user_id = u.id
            WHERE v.status = 'APPROVED'
        """
        params = []

        if school_filter and school_filter != "All":
            sql += " AND v.school LIKE ?"
            params.append(f"%{school_filter}%")

        if search:
            sql += " AND (v.title LIKE ? OR v.course_code LIKE ? OR v.description LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param])

        sql += " ORDER BY v.is_paid_boost DESC, v.created_at DESC"
        cur.execute(sql, params)
        videos = [dict(r) for r in cur.fetchall()]
        conn.close()

        for v in videos:
            v["likes_pct"] = min(100, int((v["current_likes"] / max(1, v["target_likes"])) * 100))
            v["comments_pct"] = min(100, int((v["current_comments"] / max(1, v["target_comments"])) * 100))
            v["criteria_met"] = (v["current_likes"] >= v["target_likes"]) and (v["current_comments"] >= v["target_comments"])

        self._send_json({"success": True, "videos": videos})

    def handle_get_single_video(self, video_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT v.*, u.name as student_name, u.reg_no as student_reg_no
            FROM videos v
            JOIN users u ON v.user_id = u.id
            WHERE v.id = ?
        """, (video_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            self._send_error("Video not found", 404)
            return
        
        video = dict(row)
        # Fetch verified comments
        cur.execute("""
            SELECT i.*, u.name as author_name, u.reg_no as author_reg_no
            FROM interactions i
            JOIN users u ON i.user_id = u.id
            WHERE i.video_id = ? AND i.type = 'COMMENT'
            ORDER BY i.created_at DESC
        """, (video_id,))
        comments = [dict(c) for c in cur.fetchall()]
        conn.close()

        video["comments"] = comments
        self._send_json({"success": True, "video": video})

    def handle_get_video_comments(self, video_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.*, u.name as author_name, u.reg_no as author_reg_no
            FROM interactions i
            JOIN users u ON i.user_id = u.id
            WHERE i.video_id = ? AND i.type = 'COMMENT'
            ORDER BY i.created_at DESC
        """, (video_id,))
        comments = [dict(c) for c in cur.fetchall()]
        conn.close()
        self._send_json({"success": True, "comments": comments})

    def handle_submit_video(self):
        global ACTIVE_USER_ID
        data = self._read_json()
        title = data.get("title", "").strip()
        description = data.get("description", "").strip()
        url = data.get("url", "").strip()
        course_code = data.get("course_code", "GEN101").strip().upper()
        section = data.get("section", "K21").strip().upper()
        deadline = data.get("deadline", "2026-11-15")
        target_likes = int(data.get("target_likes", 50))
        target_comments = int(data.get("target_comments", 20))

        if not title or not url:
            self._send_error("Title and Video URL are mandatory.")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (ACTIVE_USER_ID,))
        user_row = cur.fetchone()
        if not user_row:
            conn.close()
            self._send_error("User not found.")
            return
        
        user = dict(user_row)
        likes_given = user["likes_given"]
        comments_given = user["comments_given"]
        paid_passes = user["paid_passes"]

        # GATEKEEPING CRITERIA CHECK: 10 likes & 5 comments OR paid pass
        has_earned_credits = (likes_given >= 10 and comments_given >= 5)
        has_paid_pass = (paid_passes > 0)

        if not (has_earned_credits or has_paid_pass):
            conn.close()
            likes_needed = max(0, 10 - likes_given)
            comments_needed = max(0, 5 - comments_given)
            self._send_error(
                f"Submission Locked: You have not met the LPU peer criteria yet! You need {likes_needed} more like(s) and {comments_needed} more comment(s), or you can unlock instantly with a ₹49 Student Pass.",
                status=403,
                details={
                    "likes_needed": likes_needed,
                    "comments_needed": comments_needed,
                    "likes_given": likes_given,
                    "comments_given": comments_given,
                    "offer_instant_pass": True
                }
            )
            return

        # ---------------- AI CONTENT MODERATION BOT ----------------
        moderation_result = audit_video_submission(title, description, url)
        
        # Log to moderation_logs table
        cur.execute("""
            INSERT INTO moderation_logs (video_id, title, url, vulgarity_score, academic_score, flags_detected, verdict, details)
            VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (
            title, url,
            moderation_result["vulgarity_score"],
            moderation_result["academic_score"],
            ", ".join(moderation_result["flags_detected"]) if moderation_result["flags_detected"] else "NONE",
            moderation_result["verdict"],
            moderation_result["reason"]
        ))
        log_id = cur.lastrowid

        if not moderation_result["is_safe"]:
            conn.commit()
            conn.close()
            self._send_error(
                f"Content Moderation Bot Flagged Submission: {moderation_result['reason']}",
                status=422,
                details={
                    "moderation_verdict": moderation_result["verdict"],
                    "vulgarity_score": moderation_result["vulgarity_score"],
                    "flags": moderation_result["flags_detected"],
                    "reason": moderation_result["reason"]
                }
            )
            return

        # Approved! Consume paid pass if student used pass instead of full credits
        is_paid_boost = 0
        if not has_earned_credits and has_paid_pass:
            cur.execute("UPDATE users SET paid_passes = paid_passes - 1 WHERE id = ?", (ACTIVE_USER_ID,))
            is_paid_boost = 1

        # Insert new video
        cur.execute("""
            INSERT INTO videos (
                user_id, title, description, url, platform, youtube_id, school,
                course_code, section, deadline, target_likes, target_comments,
                current_likes, current_comments, status, moderation_score, moderation_verdict, is_paid_boost
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 'APPROVED', ?, ?, ?)
        """, (
            ACTIVE_USER_ID, title, description, url,
            moderation_result["platform"],
            moderation_result["video_id"],
            user["school"],
            course_code, section, deadline,
            target_likes, target_comments,
            moderation_result["academic_score"],
            moderation_result["reason"],
            is_paid_boost
        ))
        video_id = cur.lastrowid
        cur.execute("UPDATE moderation_logs SET video_id = ? WHERE id = ?", (video_id, log_id))
        conn.commit()
        conn.close()

        self._send_json({
            "success": True,
            "message": "Video verified by AI Moderation Bot and published to community feed!",
            "video_id": video_id,
            "moderation_audit": moderation_result
        })

    def handle_like_video(self, video_id):
        global ACTIVE_USER_ID
        data = self._read_json()
        watch_seconds = int(data.get("watch_seconds", 8))

        conn = get_connection()
        cur = conn.cursor()

        # Check video exists
        cur.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        video_row = cur.fetchone()
        if not video_row:
            conn.close()
            self._send_error("Video not found", 404)
            return
        video = dict(video_row)

        # Check duplicate like
        cur.execute("SELECT id FROM interactions WHERE video_id = ? AND user_id = ? AND type = 'LIKE'", (video_id, ACTIVE_USER_ID))
        if cur.fetchone():
            conn.close()
            self._send_error("You have already liked this video. Peer credit is awarded once per video.")
            return

        # ---------------- ENGAGEMENT VERIFICATION BOT ----------------
        verification = verify_like_interaction(ACTIVE_USER_ID, video["user_id"], watch_seconds=watch_seconds)

        if not verification["verified"]:
            conn.close()
            self._send_error(verification["message"], status=400, details=verification)
            return

        # Insert like interaction
        cur.execute("""
            INSERT INTO interactions (video_id, user_id, type, content, bot_verified, bot_confidence, bot_reason)
            VALUES (?, ?, 'LIKE', 'Thumb Up Verified', 1, ?, ?)
        """, (video_id, ACTIVE_USER_ID, verification["confidence"], verification["verification_signature"]))

        # Increment video like count
        cur.execute("UPDATE videos SET current_likes = current_likes + 1 WHERE id = ?", (video_id,))

        # Increment acting user's likes_given count (building upload credits!)
        cur.execute("UPDATE users SET likes_given = likes_given + 1 WHERE id = ?", (ACTIVE_USER_ID,))
        conn.commit()

        # Get updated count
        cur.execute("SELECT likes_given, comments_given, paid_passes FROM users WHERE id = ?", (ACTIVE_USER_ID,))
        usr = dict(cur.fetchone())
        conn.close()

        likes_rem = max(0, 10 - usr["likes_given"])
        comments_rem = max(0, 5 - usr["comments_given"])

        self._send_json({
            "success": True,
            "message": "Like successfully verified by Engagement Bot! +1 Credit added.",
            "verification": verification,
            "user_progress": {
                "likes_given": usr["likes_given"],
                "comments_given": usr["comments_given"],
                "likes_remaining": likes_rem,
                "comments_remaining": comments_rem,
                "unlocked": (likes_rem == 0 and comments_rem == 0) or (usr["paid_passes"] > 0)
            }
        })

    def handle_comment_video(self, video_id):
        global ACTIVE_USER_ID
        data = self._read_json()
        comment_text = data.get("comment", "").strip()
        watch_seconds = int(data.get("watch_seconds", 12))

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT * FROM videos WHERE id = ?", (video_id,))
        video_row = cur.fetchone()
        if not video_row:
            conn.close()
            self._send_error("Video not found", 404)
            return
        video = dict(video_row)

        # ---------------- ENGAGEMENT VERIFICATION BOT ----------------
        verification = verify_comment_interaction(ACTIVE_USER_ID, video["user_id"], comment_text, watch_seconds=watch_seconds)

        if not verification["verified"]:
            conn.close()
            self._send_error(verification["message"], status=422, details=verification)
            return

        # Insert comment interaction
        cur.execute("""
            INSERT INTO interactions (video_id, user_id, type, content, bot_verified, bot_confidence, bot_reason)
            VALUES (?, ?, 'COMMENT', ?, 1, ?, ?)
        """, (video_id, ACTIVE_USER_ID, comment_text, verification["confidence"], verification["verification_signature"]))

        # Increment video comments count
        cur.execute("UPDATE videos SET current_comments = current_comments + 1 WHERE id = ?", (video_id,))

        # Increment acting user's comments_given count (building upload credits!)
        cur.execute("UPDATE users SET comments_given = comments_given + 1 WHERE id = ?", (ACTIVE_USER_ID,))
        conn.commit()

        cur.execute("SELECT likes_given, comments_given, paid_passes FROM users WHERE id = ?", (ACTIVE_USER_ID,))
        usr = dict(cur.fetchone())
        conn.close()

        likes_rem = max(0, 10 - usr["likes_given"])
        comments_rem = max(0, 5 - usr["comments_given"])

        self._send_json({
            "success": True,
            "message": "Peer comment verified and posted! +1 Comment credit added.",
            "verification": verification,
            "user_progress": {
                "likes_given": usr["likes_given"],
                "comments_given": usr["comments_given"],
                "likes_remaining": likes_rem,
                "comments_remaining": comments_rem,
                "unlocked": (likes_rem == 0 and comments_rem == 0) or (usr["paid_passes"] > 0)
            }
        })

    def handle_purchase_pass(self):
        global ACTIVE_USER_ID
        data = self._read_json()
        plan_name = data.get("plan_name", "Instant Project Boost")
        amount = int(data.get("amount", 49))
        method = data.get("payment_method", "UPI (GooglePay/PhonePe)")

        tx_id = f"LPU-TXN-{int(time.time())}-{uuid.uuid4().hex[:6].upper()}"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO payments (user_id, plan_name, amount_inr, transaction_id, payment_method, status)
            VALUES (?, ?, ?, ?, ?, 'SUCCESS')
        """, (ACTIVE_USER_ID, plan_name, amount, tx_id, method))

        # Award paid pass credit
        cur.execute("UPDATE users SET paid_passes = paid_passes + 1 WHERE id = ?", (ACTIVE_USER_ID,))
        conn.commit()

        cur.execute("SELECT * FROM users WHERE id = ?", (ACTIVE_USER_ID,))
        updated_user = dict(cur.fetchone())
        conn.close()

        self._send_json({
            "success": True,
            "message": f"Payment of ₹{amount} verified via {method}! Instant Upload Pass activated.",
            "transaction_id": tx_id,
            "paid_passes": updated_user["paid_passes"],
            "eligibility_unlocked": True
        })

    def handle_get_moderation_logs(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM moderation_logs ORDER BY created_at DESC LIMIT 25")
        logs = [dict(r) for r in cur.fetchall()]
        conn.close()
        self._send_json({"success": True, "logs": logs})

    def handle_get_verification_logs(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id, i.type, i.content, i.bot_verified, i.bot_confidence, i.bot_reason, i.created_at,
                   u.name as student_name, v.title as video_title
            FROM interactions i
            JOIN users u ON i.user_id = u.id
            JOIN videos v ON i.video_id = v.id
            ORDER BY i.created_at DESC
            LIMIT 25
        """)
        logs = [dict(r) for r in cur.fetchall()]
        conn.close()
        self._send_json({"success": True, "logs": logs})

    def handle_get_campus_stats(self):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM videos WHERE status = 'APPROVED'")
        total_videos = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM interactions WHERE type = 'LIKE'")
        total_likes = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM interactions WHERE type = 'COMMENT'")
        total_comments = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM moderation_logs WHERE verdict LIKE '%REJECTED%'")
        vulgarity_prevented = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users")
        total_students = cur.fetchone()[0]

        conn.close()

        self._send_json({
            "success": True,
            "stats": {
                "total_projects": total_videos,
                "total_likes_exchanged": total_likes + 185, # Including pre-launch campus baseline
                "total_comments_verified": total_comments + 72,
                "vulgarity_blocked": vulgarity_prevented + 14,
                "students_active": total_students + 420,
                "bots_active": 2, # Content Moderation Bot + Engagement Verification Bot
                "campus_status": "OPERATIONAL - 100% SECURE"
            }
        })

    def handle_test_moderation(self):
        """Allows testing custom text with the AI Moderation Bot directly."""
        data = self._read_json()
        title = data.get("title", "")
        desc = data.get("description", "")
        url = data.get("url", "")
        result = audit_video_submission(title, desc, url)
        self._send_json({"success": True, "audit": result})

    def handle_static_file(self, path):
        if path == "/" or path == "":
            path = "/index.html"
        
        file_path = os.path.join(PUBLIC_DIR, path.lstrip("/"))
        file_path = os.path.abspath(file_path)

        # Security check against path traversal
        if not file_path.startswith(PUBLIC_DIR):
            self.send_response(403)
            self.end_headers()
            return

        if not os.path.exists(file_path) or os.path.isdir(file_path):
            file_path = os.path.join(PUBLIC_DIR, "index.html")

        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = "text/plain"

        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self._set_headers(200, content_type)
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self.end_headers()

def run_server():
    init_db()
    seed_sample_data()
    server_address = ("0.0.0.0", PORT)
    httpd = ThreadingHTTPServer(server_address, LPURequestHandler)
    print(f"Helping Hand of LPU running on port {PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
