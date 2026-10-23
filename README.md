# Helping Hand of LPU (Lovely Professional University)

> **Student-to-Student University Project Mutual Engagement Platform** with AI Content Moderation & Engagement Verification Bots.

---

## 📌 Problem & Concept

At Lovely Professional University (LPU) and many modern universities, students are frequently assigned projects that require creating and uploading videos on social media platforms (YouTube, Instagram, LinkedIn). Evaluation marks often depend on meeting specific performance criteria — such as reaching a minimum number of **views, likes, and comments**.

Individual students often struggle to meet these thresholds organically. 

**Helping Hand of LPU** solves this with a **fair peer-to-peer mutual exchange ecosystem**:
1. **Upload Gating Criteria**: To submit your project video into the university pool, you must first support fellow students by **liking 10 peer videos** and **posting 5 constructive comments**.
2. **Instant Pass (Pay to Skip)**: If a student is short on time before their project viva/deadline or prefers not to engage manually, they can purchase an **Instant Upload Pass (₹49)** to bypass the criteria and upload immediately.
3. **AI Content Moderation Bot**: Automatically screens submitted video URLs and metadata to detect and reject **vulgarity, adult content, offensive language, scams, or inappropriate material**, ensuring only academic-compliant university projects enter the pool.
4. **Engagement Verification Bot**: Audits all student interactions in real time — enforcing minimum viewing duration (5s watch time check) and analyzing peer comments using NLP heuristics to prevent spam, single-word bot comments, or repetitive character abuse.

---

## 🚀 Key Features

| Feature | Description |
|---|---|
| **Live Criteria Progress Meter** | Sticky header widget showing real-time progress (`❤️ 8/10 Likes`, `💬 3/5 Comments`) and upload eligibility status. |
| **Project Arena Feed** | Filterable by academic schools (CSE/IT, Mittal Business School, Mechanical, MCA, Biotech) with live progress bars towards marks criteria. |
| **Interactive Video Player & Reviewer** | Embedded player modal with watch timer, like authenticator, and anti-spam peer review comment box. |
| **Dual AI Bot System** | • `ModerationBot`: Checks vulgarity, NSFW terms, scams, and academic alignment.<br>• `VerificationBot`: Detects self-boosting, auto-clickers, and grades constructive feedback. |
| **Instant Pass / Payment Simulator** | Mock UPI QR Code system (Google Pay, PhonePe, Paytm, BHIM) allowing instant ₹49 Single Boost or ₹99 Semester Pass unlock. |
| **AI Bot Watchtower** | Real-time public audit logs of all bot moderation decisions and verification signatures, plus an interactive tester sandbox. |
| **Student Persona Switcher** | Switch between pre-seeded LPU student accounts (Aarav, Simran, Gurpreet, Vikram) or register a new student registration number. |

---

## 🛠️ Technology Stack

- **Backend**: Python 3 standard library (`http.server.ThreadingHTTPServer`, `sqlite3`, `urllib`, `json`, `hashlib`, `re`). **Zero external pip dependencies required.**
- **Frontend**: Responsive Single-Page Application (HTML5, Vanilla ES6 JavaScript, CSS3 with LPU university branding and glassmorphic cards).
- **Database**: SQLite persistent database (`lpu_helping_hand.db`).

---

## 🏃 Quick Start Guide

### 1. Start the Server
Run the provided launcher:
```powershell
cd C:\Users\91700\.gemini\antigravity\scratch\helping-hand-lpu
python server.py
```
Or double-click `run.bat` in Windows Explorer.

### 2. Access the Application
Open your web browser and navigate to:
```
http://localhost:8080
```

### 3. Run Automated Tests
To test the moderation bot, verification bot, database gating, and payment bypass:
```powershell
python test_internal.py
```

---

## 🤖 Bot Architecture Details

### 1. AI Content Moderation Bot (`moderation_bot.py`)
- **Vulgarity Screening**: Scans input title, description, and tags against profanity, explicit adult keywords, harassment terms, and local slang.
- **Scam & Commercial Spam Detection**: Regex filters for get-rich-quick hacks, cracked software, and sub4sub schemes.
- **Academic Relevance Score**: Verifies alignment with university evaluation criteria (e.g. references to algorithms, design, simulation, analysis, viva, or course codes).

### 2. Engagement Verification Bot (`verification_bot.py`)
- **Self-Engagement Blocker**: Prevents students from liking or commenting on their own videos to gain credits.
- **Watch Duration Verification**: Enforces minimum watch time before the like button is unlocked.
- **Peer Review Quality Audit**:
  - Rejects single-word spam (e.g. *"nice"*, *"good"*, *"done"*).
  - Flags keyboard mashing (e.g. *"aaaaaaaa"*, *"asdfghjk"*).
  - Rewards comments containing constructive peer feedback on hardware, code, design, or presentation.
  - Issues cryptographic verification signatures (e.g. `BOT-VERIFIED-COMMENT-7a8f3b21`).

---

## 📂 Project Structure

```
helping-hand-lpu/
├── database.py           # SQLite schema and sample university projects
├── moderation_bot.py     # AI Content Moderation Bot engine
├── verification_bot.py   # Engagement Verification Bot engine
├── server.py             # Multi-threaded HTTP server & REST API
├── test_internal.py      # Comprehensive unit & integration test suite
├── run.bat               # Windows quick-launch script
├── public/
│   ├── index.html        # Main web application layout & modals
│   ├── style.css         # LPU Orange/Navy design system & responsive styling
│   └── app.js            # Reactive frontend state & bot interaction logic
└── README.md             # Documentation
```
