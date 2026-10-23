/**
 * Helping Hand of LPU - Frontend Interactive Client
 * Powered by Zero-Dependency Native JS & REST API
 */

// State
let currentUser = null;
let allVideos = [];
let activeVideo = null;
let watchSecondsElapsed = 0;
let watchTimerInterval = null;
let selectedPlan = { name: "Single Project Boost", amount: 49 };
let currentSchoolFilter = "All";
let currentSearchTerm = "";

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
  fetchCurrentUser();
  fetchVideos();
  fetchCampusStats();
});

// ---------------- USER & CRITERIA LOGIC ----------------

async function fetchCurrentUser() {
  try {
    const res = await fetch("/api/user/current");
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      renderUserStatus();
    }
  } catch (err) {
    console.error("Failed to load user session:", err);
  }
}

function renderUserStatus() {
  if (!currentUser) return;

  const elig = currentUser.eligibility;
  const navBadge = document.getElementById("nav-eligibility-badge");
  const navLikes = document.getElementById("nav-likes-count");
  const navComments = document.getElementById("nav-comments-count");
  const navProgBar = document.getElementById("nav-progress-bar");
  const navName = document.getElementById("nav-user-name");
  const navReg = document.getElementById("nav-user-reg");
  const navAvatar = document.getElementById("nav-user-avatar");

  // User details
  navName.textContent = currentUser.name;
  navReg.textContent = currentUser.reg_no;
  navAvatar.textContent = currentUser.name.charAt(0);

  // Counter values
  navLikes.textContent = `${elig.likes_given}/${elig.required_likes}`;
  navComments.textContent = `${elig.comments_given}/${elig.required_comments}`;
  navProgBar.style.width = `${elig.progress_percent}%`;

  // Eligibility badge state
  if (elig.paid_passes > 0) {
    navBadge.className = "criteria-badge vip";
    navBadge.textContent = `⚡ VIP PASS (${elig.paid_passes})`;
  } else if (elig.is_eligible) {
    navBadge.className = "criteria-badge unlocked";
    navBadge.textContent = "✓ Criteria Met (Eligible)";
  } else {
    navBadge.className = "criteria-badge locked";
    navBadge.textContent = `🔒 Needs ${elig.likes_remaining}L / ${elig.comments_remaining}C`;
  }
}

// ---------------- VIDEOS & FEED LOGIC ----------------

async function fetchVideos() {
  try {
    let url = `/api/videos?school=${encodeURIComponent(currentSchoolFilter)}`;
    if (currentSearchTerm) {
      url += `&search=${encodeURIComponent(currentSearchTerm)}`;
    }
    const res = await fetch(url);
    const data = await res.json();
    if (data.success) {
      allVideos = data.videos;
      renderVideosGrid(allVideos);
    }
  } catch (err) {
    console.error("Failed to load videos:", err);
  }
}

function renderVideosGrid(videos) {
  const grid = document.getElementById("videos-grid");
  if (!videos || videos.length === 0) {
    grid.innerHTML = `
      <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px; background: #fff; border-radius: 16px; border: 1px dashed #cbd5e1;">
        <div style="font-size: 2.5rem; margin-bottom: 12px;">📚</div>
        <h3 style="color: #0f172a; margin-bottom: 8px;">No Project Videos Found</h3>
        <p style="color: #64748b; font-size: 0.9rem; margin-bottom: 16px;">Be the first LPU student in this category to submit a project video!</p>
        <button class="btn btn-primary" onclick="openUploadFlow()">+ Upload Project Video</button>
      </div>
    `;
    return;
  }

  grid.innerHTML = videos.map(v => {
    // Determine thumbnail
    const thumbUrl = v.youtube_id 
      ? `https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg`
      : 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?w=600&auto=format&fit=crop&q=80';

    const boostBadge = v.is_paid_boost 
      ? `<span class="boost-badge">⚡ VIP Boost</span>` 
      : '';

    return `
      <div class="video-card">
        <div class="video-thumb-wrap" onclick="openEngageModal(${v.id})">
          <img src="${thumbUrl}" alt="${v.title}" class="video-thumb" loading="lazy">
          <div class="platform-badge">${v.platform}</div>
          ${boostBadge}
          <div class="play-overlay">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><polygon points="5 3 19 12 5 21 5 3"/></svg>
          </div>
        </div>

        <div class="card-body">
          <div class="card-meta-row">
            <span class="badge-tag">${v.course_code || 'PROJ'}</span>
            <span style="font-size: 0.72rem; color: #64748b;">Sec ${v.section || 'N/A'}</span>
          </div>

          <h3 class="card-title" title="${v.title}">${v.title}</h3>
          <div class="card-author">By <strong>${v.student_name}</strong> (${v.student_reg_no})</div>

          <div class="card-criteria-box">
            <div class="criteria-metric-row">
              <span>❤️ Likes: <strong>${v.current_likes}</strong> / ${v.target_likes}</span>
              <div style="display: flex; align-items: center;">
                <span style="font-family: var(--font-mono); font-size: 0.75rem;">${v.likes_pct}%</span>
                <div class="metric-bar-wrap">
                  <div class="metric-bar-fill" style="width: ${v.likes_pct}%;"></div>
                </div>
              </div>
            </div>

            <div class="criteria-metric-row">
              <span>💬 Comments: <strong>${v.current_comments}</strong> / ${v.target_comments}</span>
              <div style="display: flex; align-items: center;">
                <span style="font-family: var(--font-mono); font-size: 0.75rem;">${v.comments_pct}%</span>
                <div class="metric-bar-wrap">
                  <div class="metric-bar-fill comment-fill" style="width: ${v.comments_pct}%;"></div>
                </div>
              </div>
            </div>
          </div>

          <div class="card-actions">
            <button class="btn btn-outline btn-block" onclick="openEngageModal(${v.id})">
              🤝 Support Project & Earn Credit &rarr;
            </button>
          </div>
        </div>
      </div>
    `;
  }).join("");
}

function filterBySchool(school) {
  currentSchoolFilter = school;
  const pills = document.querySelectorAll("#school-filters .filter-pill");
  pills.forEach(p => p.classList.remove("active"));
  event.target.classList.add("active");
  fetchVideos();
}

let searchDebounce = null;
function handleSearch(term) {
  clearTimeout(searchDebounce);
  searchDebounce = setTimeout(() => {
    currentSearchTerm = term.trim();
    fetchVideos();
  }, 300);
}

function refreshVideos() {
  fetchVideos();
  fetchCampusStats();
  showToast("Feed refreshed with latest peer project submissions.");
}

function scrollToFeed() {
  document.getElementById("community-feed").scrollIntoView({ behavior: "smooth" });
}

// ---------------- ENGAGE / SUPPORT MODAL ----------------

async function openEngageModal(videoId) {
  try {
    const res = await fetch(`/api/videos/${videoId}`);
    const data = await res.json();
    if (!data.success) {
      showToast(data.error || "Unable to load video details", "error");
      return;
    }

    activeVideo = data.video;
    
    // Set video details in modal
    document.getElementById("modal-engage-title").textContent = activeVideo.title;
    document.getElementById("modal-engage-course").textContent = activeVideo.course_code;
    document.getElementById("modal-engage-student").textContent = activeVideo.student_name;
    document.getElementById("modal-engage-reg").textContent = activeVideo.student_reg_no;
    document.getElementById("modal-engage-deadline").textContent = activeVideo.deadline || "Nov 2026";
    document.getElementById("modal-engage-desc").textContent = activeVideo.description || "No description provided.";
    
    // Render video embed
    const container = document.getElementById("modal-video-container");
    if (activeVideo.youtube_id) {
      container.innerHTML = `
        <iframe src="https://www.youtube.com/embed/${activeVideo.youtube_id}?autoplay=1&mute=1" 
                title="${activeVideo.title}" 
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                allowfullscreen>
        </iframe>
      `;
    } else {
      container.innerHTML = `
        <div style="width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; background: #0f172a; color: #fff; padding: 20px; text-align: center;">
          <p style="margin-bottom: 12px; font-weight: 600;">Direct Social Video Link</p>
          <a href="${activeVideo.url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary btn-sm">
            Open Video on ${activeVideo.platform} &rarr;
          </a>
        </div>
      `;
    }

    // Reset Watch Verification Timer
    resetWatchTimer();

    // Render comments list
    renderModalComments(activeVideo.comments || []);

    // Open modal
    openModal("modal-engage");

  } catch (err) {
    console.error("Failed to open engage modal:", err);
    showToast("Error loading video details", "error");
  }
}

function resetWatchTimer() {
  clearInterval(watchTimerInterval);
  watchSecondsElapsed = 0;
  const timerDisplay = document.getElementById("watch-timer");
  const progressFill = document.getElementById("watch-progress-fill");
  const statusChip = document.getElementById("like-status-chip");
  const likeBtn = document.getElementById("modal-like-btn");

  timerDisplay.textContent = "Watching: 0s / 5s required";
  progressFill.style.width = "0%";
  statusChip.innerHTML = `<span style="color: #64748b;">🛡️ Bot tracking viewing duration...</span>`;
  likeBtn.disabled = true;

  // Run 5-second verification countdown
  watchTimerInterval = setInterval(() => {
    watchSecondsElapsed++;
    const pct = Math.min(100, (watchSecondsElapsed / 5) * 100);
    progressFill.style.width = `${pct}%`;
    timerDisplay.textContent = `Watching: ${watchSecondsElapsed}s / 5s required`;

    if (watchSecondsElapsed >= 5) {
      clearInterval(watchTimerInterval);
      likeBtn.disabled = false;
      statusChip.innerHTML = `<span style="color: #10b981; font-weight: 700;">✓ Engagement Bot Verified: Ready to Like</span>`;
    }
  }, 1000);
}

async function submitLike() {
  if (!activeVideo) return;
  const likeBtn = document.getElementById("modal-like-btn");
  likeBtn.disabled = true;

  try {
    const res = await fetch(`/api/videos/${activeVideo.id}/like`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ watch_seconds: watchSecondsElapsed })
    });
    const data = await res.json();

    if (!data.success) {
      showToast(data.error, "error");
      likeBtn.disabled = false;
      return;
    }

    showToast("❤️ Like verified by Engagement Bot! +1 Upload Credit awarded.", "success");
    document.getElementById("like-status-chip").innerHTML = `<span style="color: #10b981;">✓ Liked & Verified (${data.verification.verification_signature})</span>`;
    
    // Refresh user criteria & feed
    fetchCurrentUser();
    fetchVideos();

  } catch (err) {
    console.error("Like failed:", err);
    showToast("Failed to record like", "error");
    likeBtn.disabled = false;
  }
}

function updateCommentBotPreview(text) {
  const len = text.trim().length;
  const countEl = document.getElementById("comment-char-count");
  const checkEl = document.getElementById("comment-bot-live-check");
  const postBtn = document.getElementById("post-comment-btn");

  countEl.textContent = `${len} / 12 min`;

  if (len === 0) {
    checkEl.className = "comment-bot-live-check";
    checkEl.textContent = "Bot Pre-Check: Enter at least 12 characters of genuine feedback";
    postBtn.disabled = false;
  } else if (len < 12) {
    checkEl.className = "comment-bot-live-check";
    checkEl.innerHTML = `⚠️ Comment too short (<strong style="color: #ef4444;">${12 - len} more chars needed</strong>)`;
  } else {
    checkEl.className = "comment-bot-live-check valid";
    checkEl.innerHTML = `✓ Bot Pre-Check Passed: Eligible for university peer evaluation mark`;
  }
}

async function submitComment() {
  if (!activeVideo) return;
  const textarea = document.getElementById("comment-textarea");
  const commentText = textarea.value.trim();
  const postBtn = document.getElementById("post-comment-btn");

  if (!commentText) {
    showToast("Please enter a constructive peer comment", "error");
    return;
  }

  postBtn.disabled = true;
  postBtn.textContent = "Auditing Comment...";

  try {
    const res = await fetch(`/api/videos/${activeVideo.id}/comment`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ comment: commentText, watch_seconds: watchSecondsElapsed })
    });
    const data = await res.json();

    if (!data.success) {
      showToast(data.error, "error");
      postBtn.disabled = false;
      postBtn.textContent = "💬 Post Verified Review";
      return;
    }

    showToast("💬 Peer review verified by Engagement Bot! +1 Upload Credit awarded.", "success");
    textarea.value = "";
    updateCommentBotPreview("");
    postBtn.disabled = false;
    postBtn.textContent = "💬 Post Verified Review";

    // Re-fetch video comments
    const cRes = await fetch(`/api/videos/${activeVideo.id}/comments`);
    const cData = await cRes.json();
    if (cData.success) {
      renderModalComments(cData.comments);
    }

    // Refresh user criteria & feed
    fetchCurrentUser();
    fetchVideos();

  } catch (err) {
    console.error("Comment submission failed:", err);
    showToast("Failed to post comment", "error");
    postBtn.disabled = false;
    postBtn.textContent = "💬 Post Verified Review";
  }
}

function renderModalComments(comments) {
  const listEl = document.getElementById("modal-comments-list");
  const countEl = document.getElementById("modal-comment-count");
  countEl.textContent = comments.length;

  if (comments.length === 0) {
    listEl.innerHTML = `<div style="text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 20px;">No peer reviews yet. Be the first to review!</div>`;
    return;
  }

  listEl.innerHTML = comments.map(c => `
    <div class="comment-card">
      <div class="comment-meta">
        <span class="comment-author">${c.author_name} (${c.author_reg_no})</span>
        <span class="comment-sig">🛡️ Bot Verified</span>
      </div>
      <div class="comment-text">${escapeHtml(c.content)}</div>
    </div>
  `).join("");
}

// ---------------- UPLOAD VIDEO & AI MODERATION SCAN ----------------

function openUploadFlow() {
  if (!currentUser) return;

  const elig = currentUser.eligibility;
  const gateBanner = document.getElementById("upload-gate-banner");
  const form = document.getElementById("upload-form");
  const gateMsg = document.getElementById("gate-message-text");
  const alertBox = document.getElementById("moderation-alert");
  const scannerBox = document.getElementById("moderation-scanner");

  alertBox.style.display = "none";
  scannerBox.style.display = "none";

  if (!elig.is_eligible) {
    gateBanner.style.display = "flex";
    gateMsg.innerHTML = `
      Your Criteria Progress: <strong>${elig.likes_given}/10 Likes</strong> and <strong>${elig.comments_given}/5 Comments</strong>.<br>
      You still need <strong style="color: #d97706;">${elig.likes_remaining} more like(s)</strong> and <strong style="color: #d97706;">${elig.comments_remaining} more comment(s)</strong> on peers' project videos to unlock free upload, or you can use an Instant Pass.
    `;
    form.style.opacity = "0.4";
    form.style.pointerEvents = "none";
  } else {
    gateBanner.style.display = "none";
    form.style.opacity = "1";
    form.style.pointerEvents = "auto";
  }

  openModal("modal-upload");
}

function handleUrlInput(url) {
  // Auto-detect YouTube title or alert
  if (url.includes("youtube.com") || url.includes("youtu.be")) {
    const titleInput = document.getElementById("video-title");
    if (!titleInput.value) {
      titleInput.placeholder = "e.g. Computer Graphics 3D Rendering Project in OpenGL";
    }
  }
}

async function submitVideoUpload() {
  const url = document.getElementById("video-url").value.trim();
  const title = document.getElementById("video-title").value.trim();
  const course_code = document.getElementById("video-course").value.trim();
  const section = document.getElementById("video-section").value.trim();
  const description = document.getElementById("video-desc").value.trim();
  const target_likes = document.getElementById("video-target-likes").value;
  const target_comments = document.getElementById("video-target-comments").value;

  const scannerBox = document.getElementById("moderation-scanner");
  const alertBox = document.getElementById("moderation-alert");
  const submitBtn = document.getElementById("btn-submit-upload");

  scannerBox.style.display = "block";
  alertBox.style.display = "none";
  submitBtn.disabled = true;

  const stepUrl = document.getElementById("step-url");
  const stepVulgarity = document.getElementById("step-vulgarity");
  const stepAcademic = document.getElementById("step-academic");

  // Step 1: URL validation
  stepUrl.className = "scan-step passed";
  stepUrl.textContent = "✓ Validating URL format & platform origin";

  // Step 2: Vulgarity
  stepVulgarity.className = "scan-step";
  stepVulgarity.textContent = "⌛ Scanning metadata for vulgarity, adult, and offensive terms...";

  await new Promise(r => setTimeout(r, 600));

  try {
    const res = await fetch("/api/videos/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url, title, course_code, section, description,
        target_likes, target_comments
      })
    });
    const data = await res.json();

    if (!data.success) {
      stepVulgarity.className = "scan-step failed";
      stepVulgarity.textContent = "✗ Content flagged by SafetyBot";
      stepAcademic.className = "scan-step failed";
      stepAcademic.textContent = "✗ Academic review failed";

      alertBox.className = "moderation-feedback error";
      alertBox.style.display = "block";
      alertBox.innerHTML = `
        <strong>🚫 AI Content Moderation Bot Alert:</strong><br>
        ${data.error}<br>
        ${data.details && data.details.flags ? `<small style="font-family: var(--font-mono);">Detected Triggers: [${data.details.flags.join(", ")}]</small>` : ""}
      `;
      submitBtn.disabled = false;
      return;
    }

    // Success animation
    stepVulgarity.className = "scan-step passed";
    stepVulgarity.textContent = "✓ Vulgarity & NSFW check clean (0.00% offensive content)";
    stepAcademic.className = "scan-step passed";
    stepAcademic.textContent = `✓ LPU Academic Alignment verified (${Math.round(data.moderation_audit.academic_score * 100)}% match)`;

    alertBox.className = "moderation-feedback success";
    alertBox.style.display = "block";
    alertBox.innerHTML = `
      <strong>🎉 Approved by AI Moderation Bot!</strong><br>
      Your project video has been published to the Lovely Professional University peer community feed.
    `;

    showToast("Project video published successfully!", "success");

    setTimeout(() => {
      closeModal("modal-upload");
      fetchVideos();
      fetchCurrentUser();
      submitBtn.disabled = false;
      document.getElementById("upload-form").reset();
    }, 1200);

  } catch (err) {
    console.error("Upload error:", err);
    showToast("Failed to submit video", "error");
    submitBtn.disabled = false;
  }
}

// ---------------- PAYMENT & VIP PASS ----------------

function selectPlan(name, amount) {
  selectedPlan = { name, amount };
  document.getElementById("plan-single").classList.toggle("selected", amount === 49);
  document.getElementById("plan-semester").classList.toggle("selected", amount === 99);
  document.getElementById("pay-amount-display").textContent = amount;
}

async function executeMockPayment() {
  try {
    const res = await fetch("/api/payment/purchase-pass", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        plan_name: selectedPlan.name,
        amount: selectedPlan.amount,
        payment_method: "UPI (Simulated GPay)"
      })
    });
    const data = await res.json();

    if (!data.success) {
      showToast(data.error, "error");
      return;
    }

    showToast(`⚡ Payment of ₹${selectedPlan.amount} received! Instant Pass activated.`, "success");
    closeModal("modal-pay");
    fetchCurrentUser();

    // Automatically prompt upload modal with unlocked permission
    setTimeout(() => {
      openUploadFlow();
    }, 400);

  } catch (err) {
    console.error("Payment failed:", err);
    showToast("Payment execution failed", "error");
  }
}

// ---------------- BOT WATCHTOWER & SANDBOX ----------------

async function switchBotTab(tab) {
  document.getElementById("bot-tab-moderation").style.display = (tab === 'moderation') ? 'block' : 'none';
  document.getElementById("bot-tab-verification").style.display = (tab === 'verification') ? 'block' : 'none';
  document.getElementById("bot-tab-tester").style.display = (tab === 'tester') ? 'block' : 'none';

  document.getElementById("tab-btn-mod").classList.toggle("active", tab === 'moderation');
  document.getElementById("tab-btn-ver").classList.toggle("active", tab === 'verification');
  document.getElementById("tab-btn-test").classList.toggle("active", tab === 'tester');

  if (tab === 'moderation') loadModerationLogs();
  if (tab === 'verification') loadVerificationLogs();
}

async function loadModerationLogs() {
  const tbody = document.getElementById("table-mod-logs");
  tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Loading AI audit records...</td></tr>`;

  try {
    const res = await fetch("/api/moderation/logs");
    const data = await res.json();
    if (data.success) {
      tbody.innerHTML = data.logs.map(log => `
        <tr>
          <td style="font-family: var(--font-mono); font-size: 0.72rem;">${log.created_at}</td>
          <td>
            <strong>${escapeHtml(log.title)}</strong><br>
            <small style="color: #64748b;">${escapeHtml(log.url)}</small>
          </td>
          <td>
            <span style="color: ${log.vulgarity_score > 0.2 ? '#ef4444' : '#10b981'}; font-weight: 700; font-family: var(--font-mono);">
              ${Math.round(log.vulgarity_score * 100)}%
            </span>
          </td>
          <td>
            <span style="color: #3b82f6; font-family: var(--font-mono);">${Math.round(log.academic_score * 100)}%</span>
          </td>
          <td>
            <span class="badge-tag" style="background: ${log.verdict === 'APPROVED' ? '#ecfdf5; color: #059669;' : '#fef2f2; color: #dc2626;'}">
              ${log.verdict}
            </span>
          </td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading mod logs:", err);
  }
}

async function loadVerificationLogs() {
  const tbody = document.getElementById("table-ver-logs");
  tbody.innerHTML = `<tr><td colspan="5" style="text-align: center;">Loading activity audit records...</td></tr>`;

  try {
    const res = await fetch("/api/verification/logs");
    const data = await res.json();
    if (data.success) {
      tbody.innerHTML = data.logs.map(log => `
        <tr>
          <td style="font-family: var(--font-mono); font-size: 0.72rem;">${log.created_at}</td>
          <td><strong>${log.student_name}</strong></td>
          <td><span class="badge-tag">${log.type}</span></td>
          <td style="font-family: var(--font-mono); color: #10b981; font-weight: 700;">${Math.round(log.bot_confidence * 100)}%</td>
          <td>
            <span style="font-size: 0.75rem; color: #64748b;">${escapeHtml(log.bot_reason || '')}</span><br>
            <small style="color: #0f172a;">${escapeHtml(log.content || '')}</small>
          </td>
        </tr>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading verification logs:", err);
  }
}

function setTestSample(type) {
  const input = document.getElementById("test-bot-input");
  if (type === 'academic') {
    input.value = "Autonomous Micro-Drone Object Detection Project using YOLOv8 - CSE423 Capstone";
  } else if (type === 'vulgar') {
    input.value = "Hot adult xxx free strip clip leaked dating scam";
  } else if (type === 'spam') {
    input.value = "Get free 10,000 free coins hack 100% working download cracked software now";
  }
}

async function runSandboxBotCheck() {
  const text = document.getElementById("test-bot-input").value.trim();
  const box = document.getElementById("sandbox-result-box");
  if (!text) {
    showToast("Please enter sample text to test", "error");
    return;
  }

  box.style.display = "block";
  box.innerHTML = "🤖 Running neural audit filters...";

  try {
    const res = await fetch("/api/bot/test-moderation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: text, description: text, url: "https://www.youtube.com/watch?v=sample12345" })
    });
    const data = await res.json();
    const a = data.audit;

    box.innerHTML = `
      <div style="margin-bottom: 8px;">
        <span style="color: ${a.is_safe ? '#4ade80' : '#f87171'}; font-weight: 800; font-size: 1rem;">
          ${a.verdict} (${a.is_safe ? 'SAFE & ACADEMIC' : 'PROHIBITED CONTENT'})
        </span>
      </div>
      <div><strong>Reason:</strong> ${a.reason}</div>
      <div style="margin-top: 6px;">
        • Vulgarity Index: <strong>${a.vulgarity_score * 100}%</strong><br>
        • Academic Relevance: <strong>${a.academic_score * 100}%</strong><br>
        • Flags Detected: <strong>${a.flags_detected.length > 0 ? a.flags_detected.join(', ') : 'None'}</strong><br>
        • Bot Signature: <strong>${a.bot_signature}</strong>
      </div>
    `;
  } catch (err) {
    box.innerHTML = "Inspection failed.";
  }
}

// ---------------- USER SWITCHER & REGISTRATION ----------------

async function loadAllPersonas() {
  const listEl = document.getElementById("persona-list");
  try {
    const res = await fetch("/api/users");
    const data = await res.json();
    if (data.success) {
      listEl.innerHTML = data.users.map(u => `
        <div class="persona-item ${u.id === data.active_user_id ? 'active' : ''}" onclick="switchUser(${u.id})">
          <div class="persona-left">
            <div class="avatar">${u.name.charAt(0)}</div>
            <div class="persona-info">
              <strong>${u.name} ${u.id === data.active_user_id ? '✓ (Current)' : ''}</strong>
              <span>${u.reg_no} • ${u.course}</span>
            </div>
          </div>
          <div class="persona-stats">
            ❤️ ${u.likes_given}/10 | 💬 ${u.comments_given}/5
            ${u.paid_passes > 0 ? `<br><span style="color: #b45309; font-weight: 700;">⚡ ${u.paid_passes} Pass</span>` : ''}
          </div>
        </div>
      `).join("");
    }
  } catch (err) {
    console.error("Error loading personas:", err);
  }
}

async function switchUser(userId) {
  try {
    const res = await fetch("/api/user/switch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ user_id: userId })
    });
    const data = await res.json();
    if (data.success) {
      currentUser = data.user;
      renderUserStatus();
      closeModal("modal-switch-user");
      showToast(`Switched active student to ${currentUser.name}`);
      fetchVideos();
    }
  } catch (err) {
    showToast("Failed to switch persona", "error");
  }
}

async function registerNewStudent() {
  const reg_no = document.getElementById("new-reg-no").value.trim();
  const name = document.getElementById("new-name").value.trim();
  const school = document.getElementById("new-school").value;
  const course = document.getElementById("new-course").value.trim() || "B.Tech CSE";

  try {
    const res = await fetch("/api/user/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reg_no, name, school, course })
    });
    const data = await res.json();
    if (!data.success) {
      showToast(data.error, "error");
      return;
    }

    currentUser = data.user;
    renderUserStatus();
    closeModal("modal-switch-user");
    showToast(`Welcome ${name}! Your LPU account is ready.`);
    fetchVideos();
  } catch (err) {
    showToast("Registration failed", "error");
  }
}

// ---------------- CAMPUS STATS ----------------

async function fetchCampusStats() {
  try {
    const res = await fetch("/api/stats");
    const data = await res.json();
    if (data.success) {
      const s = data.stats;
      document.getElementById("stat-projects").textContent = s.total_projects;
      document.getElementById("stat-likes").textContent = s.total_likes_exchanged;
      document.getElementById("stat-vulgarity").textContent = s.vulgarity_blocked;
    }
  } catch (err) {
    console.error("Stats error:", err);
  }
}

// ---------------- MODAL HELPERS ----------------

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add("active");
    if (id === 'modal-bot-watchtower') {
      loadModerationLogs();
    }
    if (id === 'modal-switch-user') {
      loadAllPersonas();
    }
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove("active");
    if (id === 'modal-engage') {
      clearInterval(watchTimerInterval);
      document.getElementById("modal-video-container").innerHTML = "";
    }
  }
}

// Close on backdrop click
window.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal-overlay")) {
    e.target.classList.remove("active");
    if (e.target.id === 'modal-engage') {
      clearInterval(watchTimerInterval);
      document.getElementById("modal-video-container").innerHTML = "";
    }
  }
});

// Toast notification
function showToast(message, type = "info") {
  const container = document.getElementById("toast-container");
  const toast = document.createElement("div");
  toast.className = `toast ${type === 'success' ? 'toast-success' : type === 'error' ? 'toast-error' : ''}`;
  toast.innerHTML = `<span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.remove();
  }, 4000);
}

function escapeHtml(text) {
  if (!text) return "";
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return text.toString().replace(/[&<>"']/g, m => map[m]);
}
