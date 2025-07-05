// Dynamic PQGen JavaScript - No Static Examples, PDF-Generated Only
console.log("Dynamic PQGen JavaScript loaded successfully");

// Global state for challenge attempts and results
const challengeStates = {};

// Firebase configuration (replace with your actual config)
const firebaseConfig = {
  apiKey: "AIzaSyBM8yL_OhsklMsO5naTvW3zhn9XGaIMFwk",
  authDomain: "pqgen-31a0c.firebaseapp.com",
  projectId: "pqgen-31a0c",
  storageBucket: "pqgen-31a0c.firebasestorage.app",
  messagingSenderId: "481313515335",
  appId: "1:481313515335:web:40964b50afc8c341188e62"
};

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const auth = firebase.auth();
const db = firebase.firestore();
const storage = firebase.storage();

let currentUser = null;

document.addEventListener("DOMContentLoaded", () => {
  // ─── Section refs ────────────────────────────────────────────────────────────
  const sections = {
    upload: document.getElementById("upload-section"),
    loading: document.getElementById("enhanced-loading"),
    topics: document.getElementById("topic-selection"),
    genProgress: document.getElementById("challenge-generation"),
    display: document.getElementById("challenge-display"),
    profile: document.getElementById("profile-section"),
    favorites: document.getElementById("favorites-section"),
    error: document.getElementById("error-section"),
  };

  // ─── Upload UI refs ─────────────────────────────────────────────────────────
  const fileInput = document.getElementById("file-input");
  const uploadArea = document.getElementById("upload-area");
  const fileNameEl = document.getElementById("file-name");
  const fileStateEl = document.getElementById("file-state");
  const uploadBtn = document.getElementById("upload-btn");

  // ─── Extraction progress refs ───────────────────────────────────────────────
  const progressMsg = document.getElementById("progress-message");
  const progressFill = document.getElementById("progress-fill");
  const progressPct = document.getElementById("progress-percentage");

  // ─── Topic selection refs ───────────────────────────────────────────────────
  const topicsList = document.getElementById("topics-list");
  const selectAllBtn = document.getElementById("select-all-topics");
  const clearAllBtn = document.getElementById("clear-topics");
  const generateBtn = document.getElementById("generate-challenges-btn");

  // ─── Generation progress refs ───────────────────────────────────────────────
  const genMsg = document.getElementById("generation-message");
  const genFill = document.getElementById("generation-progress-fill");
  const genPct = document.getElementById("generation-progress-text");

  // ─── Challenges display refs ─────────────────────────────────────────────────
  const challengeContainer = document.getElementById("challenge-container");
  const challengesCount = document.getElementById("challenges-count");
  const challengesSolved = document.getElementById("challenges-solved");

  // ─── Filter buttons ─────────────────────────────────────────────────────────
  const filterBtns = Array.from(document.querySelectorAll(".filter-btn"));

  // ─── Error & retry refs ─────────────────────────────────────────────────────
  const errorMessageEl = document.getElementById("error-message");
  const retryBtn = document.getElementById("retry-button");

  // ─── Modal refs ─────────────────────────────────────────────────────────────
  const challengeModal = document.getElementById("challenge-modal");
  const modalTitle = document.getElementById("modal-title");
  const modalBody = document.getElementById("modal-body");
  const modalClose = document.getElementById("modal-close");
  const modalHint = document.getElementById("modal-hint");
  const modalSubmit = document.getElementById("modal-submit");

  // ─── Auth Modal refs ────────────────────────────────────────────────────────
  const authButton = document.getElementById("auth-button");
  const authModal = document.getElementById("auth-modal");
  const authModalClose = document.getElementById("auth-modal-close");
  const authModalTitle = document.getElementById("auth-modal-title");
  const authForm = document.getElementById("auth-form");
  const authEmail = document.getElementById("auth-email");
  const authUsernameGroup = document.getElementById("auth-username-group");
  const authUsername = document.getElementById("auth-username");
  const authPassword = document.getElementById("auth-password");
  const authAvatarGroup = document.getElementById("auth-avatar-group");
  const avatarOptions = document.querySelectorAll(".avatar-option");
  const authSubmitButton = document.getElementById("auth-submit-button");
  const switchToSignup = document.getElementById("switch-to-signup");
  const switchToLogin = document.getElementById("switch-to-login");
  let isLoginMode = true;
  let selectedAvatar = "avatar1";

  // ─── Profile refs ───────────────────────────────────────────────────────────
  const profileDisplayName = document.getElementById("profile-display-name");
  const profileEmail = document.getElementById("profile-email");
  const profileAvatar = document.getElementById("profile-avatar");
  const profileSolvedCount = document.getElementById("profile-solved-count");
  const profileFavoritesCount = document.getElementById("profile-favorites-count");
  const profileUploadsCount = document.getElementById("profile-uploads-count");
  const logoutButton = document.getElementById("logout-button");

  // ─── Favorites refs ─────────────────────────────────────────────────────────
  const favoritesList = document.getElementById("favorites-list");
  const noFavorites = document.getElementById("no-favorites");

  // ─── Navigation refs ────────────────────────────────────────────────────────
  const navUpload = document.getElementById("nav-upload");
  const navChallenges = document.getElementById("nav-challenges");
  const navFavorites = document.getElementById("nav-favorites");
  const navProfile = document.getElementById("nav-profile");

  // ─── State ───────────────────────────────────────────────────────────────────
  let currentDocId = null;
  let allTopics = [];
  let allChallenges = [];
  let currentChallengeIndex = null;

  // ─── Helpers ─────────────────────────────────────────────────────────────────
  function showSection(key) {
    Object.values(sections).forEach((sec) => {
      if (sec) sec.classList.add("hidden");
    });
    if (sections[key]) sections[key].classList.remove("hidden");
    
    // Update navigation button states
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeNavBtn = document.querySelector(`[data-section="${key}"]`);
    if (activeNavBtn) activeNavBtn.classList.add('active');
  }

  function showError(msg) {
    if (errorMessageEl) errorMessageEl.textContent = msg;
    showSection("error");
    console.error(msg);
  }

  function updateProgress(msg = "", pct = 0) {
    if (progressMsg) progressMsg.textContent = msg;
    if (progressFill) progressFill.style.width = `${pct}%`;
    if (progressPct) progressPct.textContent = `${pct}%`;
  }

  function updateGenProgress(msg = "", pct = 0) {
    if (genMsg) genMsg.textContent = msg;
    if (genFill) genFill.style.width = `${pct}%`;
    if (genPct) genPct.textContent = `${pct}%`;
  }

  function getSelectedTopics() {
    if (!topicsList) return [];
    return Array.from(topicsList.querySelectorAll(".topic-item")).reduce(
      (arr, div) => {
        const cb = div.querySelector(".topic-checkbox");
        const sel = div.querySelector(".difficulty-select");
        if (cb && cb.checked && sel)
          arr.push({ topic: cb.value, difficulty: sel.value });
        return arr;
      },
      []
    );
  }

  // ─── Enhanced Challenge State Management ────────────────────────────────────
  function initializeChallengeState(index) {
    if (!challengeStates[index]) {
      challengeStates[index] = {
        attempts: 0,
        solved: false,
        hintShown: false,
        userAnswers: {},
        feedback: null,
      };
    }
    return challengeStates[index];
  }

  async function updateChallengeCard(index) {
    if (!challengeContainer || !challengeContainer.children[index]) return;

    const card = challengeContainer.children[index];
    const state = challengeStates[index];
    const feedbackEl = card.querySelector(".challenge-feedback");
    const favoriteIcon = card.querySelector(".favorite-icon");

    if (feedbackEl) {
      feedbackEl.remove();
    }

    // Add feedback indicator with animations
    const feedback = document.createElement("div");
    feedback.className = "challenge-feedback";

    if (state.solved) {
      feedback.innerHTML = 
        '<div class="victory-animation">✓</div>';
      feedback.classList.add("success");
    } else if (state.attempts >= 3) {
      feedback.innerHTML = 
        '<div class="defeat-animation">✗</div>';
      feedback.classList.add("failure");

      // Show correct answer and hint
      const challenge = allChallenges[index];
      const answerDiv = document.createElement("div");
      answerDiv.className = "correct-answer-display";
      answerDiv.innerHTML = `
        <div class="answer-section">
          <strong>Correct Answer:</strong> ${getCorrectAnswerText(challenge)}
        </div>
        <div class="hint-section">
          <strong>Hint:</strong> ${challenge.hint}
        </div>
      `;
      feedback.appendChild(answerDiv);
    }

    card.appendChild(feedback);

    // Update solved count
    const solvedCount = Object.values(challengeStates).filter((s) => s.solved).length;
    if (challengesSolved) challengesSolved.textContent = `${solvedCount} solved`;

    // Update favorite icon state
    if (favoriteIcon && currentUser) {
      const challengeId = allChallenges[index].id;
      const isFavorited = await checkIfFavorited(challengeId);
      if (isFavorited) {
        favoriteIcon.classList.add("favorited");
      } else {
        favoriteIcon.classList.remove("favorited");
      }
    }
  }

  function getCorrectAnswerText(challenge) {
    if (challenge.type.includes("multiple")) {
      return challenge.options[challenge.correct_answer];
    } else if (challenge.type === "debugging") {
      // Show the code snippet and the correct answer for debugging challenges
      let debugAnswer = "";
      if (challenge.code_stub) {
        debugAnswer += `<div class="debug-code-display"><strong>Code:</strong><pre><code>${challenge.code_stub}</code></pre></div>`;
      }
      if (challenge.correct_answer) {
        debugAnswer += `<div class="debug-solution"><strong>Solution:</strong> ${challenge.correct_answer}</div>`;
      } else {
        debugAnswer += `<div class="debug-solution"><strong>Solution:</strong> See hint for debugging guidance</div>`;
      }
      return debugAnswer;
    } else if (challenge.type.includes("fill")) {
      return challenge.blanks
        .map((b) => `Blank ${b.blank_number}: ${b.correct_answer}`)
        .join(", ");
    }
    return "See hint for guidance";
  }

  // ─── Drag & Drop + Click-to-Upload ──────────────────────────────────────────
  if (uploadArea && fileInput) {
    uploadArea.addEventListener("click", () => fileInput.click());
    uploadArea.addEventListener("dragover", (e) => {
      e.preventDefault();
      uploadArea.classList.add("drag-over");
    });
    uploadArea.addEventListener("dragleave", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("drag-over");
    });
    uploadArea.addEventListener("drop", (e) => {
      e.preventDefault();
      uploadArea.classList.remove("drag-over");
      if (e.dataTransfer.files[0]) processFile(e.dataTransfer.files[0]);
    });
    fileInput.addEventListener("change", (e) => {
      if (e.target.files[0]) processFile(e.target.files[0]);
    });
  }

  // ─── Upload & Poll for Extraction ────────────────────────────────────────────
  async function processFile(file) {
    if (!currentUser) {
      alert("Please login to upload documents.");
      return;
    }

    try {
      if (fileNameEl) {
        fileNameEl.textContent = file.name;
        fileNameEl.classList.remove("hidden");
      }
      if (fileStateEl) fileStateEl.textContent = "Uploading and processing…";
      if (uploadBtn) uploadBtn.classList.remove("hidden");

      showSection("loading");
      updateProgress("Uploading file…", 0);

      // Upload to Firebase Storage first
      const storageRef = storage.ref();
      const fileRef = storageRef.child(
        `users/${currentUser.uid}/uploads/${file.name}`
      );
      const uploadTask = fileRef.put(file);

      uploadTask.on(
        "state_changed",
        (snapshot) => {
          const progress =
            (snapshot.bytesTransferred / snapshot.totalBytes) * 50; // Only 50% for Firebase upload
          updateProgress(`Uploading file: ${file.name}`, progress);
        },
        (error) => {
          showError(`Upload failed: ${error.message}`);
        },
        async () => {
          const downloadURL = await fileRef.getDownloadURL();
          // Save metadata to Firestore
          await db
            .collection("users")
            .doc(currentUser.uid)
            .collection("uploads")
            .add({
              filename: file.name,
              downloadURL: downloadURL,
              uploadedAt: firebase.firestore.FieldValue.serverTimestamp(),
            });

          updateProgress("File uploaded to Firebase, processing with backend...", 50);

          // Now upload to backend for processing
          const form = new FormData();
          form.append('file', file);
          const res = await fetch('/api/upload', { method: 'POST', body: form });
          if (!res.ok) throw new Error(`Upload failed (${res.status})`);
          const { document_id } = await res.json();
          currentDocId = document_id;

          // Poll for extraction progress
          while (true) {
            await new Promise(r => setTimeout(r, 1000));
            const pr = await fetch(`/api/documents/${currentDocId}/progress`);
            if (!pr.ok) { showError(`Progress check failed (${pr.status})`); return; }
            const data = await pr.json();
            updateProgress(data.message || '', 50 + (data.progress || 0) * 0.5); // Scale to 50-100%

            if (data.status === 'completed') {
              allTopics = data.topics || [];
              renderTopicSelection();
              showSection('topics');
              break;
            }
            if (data.status === 'error') throw new Error(data.message || 'Extraction failed');
          }
        }
      );
    } catch (err) {
      showError(err.message);
    }
  }

  // ─── Render Topic Selection UI ───────────────────────────────────────────────
  function renderTopicSelection() {
    if (!topicsList) return;

    topicsList.innerHTML = "";
    allTopics.forEach((topic) => {
      const div = document.createElement("div");
      div.className = "topic-item";
      div.innerHTML = `
        <label>
          <input type="checkbox" class="topic-checkbox" value="${topic}" checked>
          ${topic}
        </label>
        <select class="difficulty-select">
          <option value="easy">Easy</option>
          <option value="medium" selected>Medium</option>
          <option value="hard">Hard</option>
        </select>
      `;
      div.querySelector(".topic-checkbox").addEventListener("change", () => {
        if (generateBtn) generateBtn.disabled = getSelectedTopics().length === 0;
      });
      topicsList.append(div);
    });

    if (selectAllBtn) {
      selectAllBtn.onclick = () => {
        topicsList
          .querySelectorAll(".topic-checkbox")
          .forEach((cb) => (cb.checked = true));
        if (generateBtn) generateBtn.disabled = false;
      };
    }

    if (clearAllBtn) {
      clearAllBtn.onclick = () => {
        topicsList
          .querySelectorAll(".topic-checkbox")
          .forEach((cb) => (cb.checked = false));
        if (generateBtn) generateBtn.disabled = true;
      };
    }

    if (generateBtn) {
      generateBtn.onclick = handleGenerateChallenges;
      generateBtn.disabled = getSelectedTopics().length === 0;
    }
  }

  // ─── Generate & Poll for Challenges ─────────────────────────────────────────
  async function handleGenerateChallenges() {
    try {
      const chosen = getSelectedTopics();
      if (!chosen.length) {
        showError("Please select at least one topic");
        return;
      }

      showSection("genProgress");
      updateGenProgress("Starting generation…", 0);

      // Send request to backend to start challenge generation
      await fetch(`/api/documents/${currentDocId}/generate`, {
        method: 'POST',
        headers: { 'Content-Type':'application/json' },
        body: JSON.stringify({ topics: chosen })
      });

      // Poll until ready
      while (true) {
        await new Promise(r => setTimeout(r, 2000));
        const pr = await fetch(`/api/documents/${currentDocId}/progress`);
        if (!pr.ok) { showError(`Gen progress failed (${pr.status})`); return; }
        const d = await pr.json();
        updateGenProgress(d.message||'', d.progress||0);

        if (d.status === 'challenges_ready' || d.status === 'completed') {
          const finalRes = await fetch(`/api/documents/${currentDocId}/challenges`);
          const { challenges } = await finalRes.json();
          allChallenges = challenges;
          renderChallenges(challenges);
          break;
        }
        if (d.status === 'error') throw new Error(d.message || 'Generation error');
      }
    } catch (err) {
      showError(err.message);
    }
  }

  // ─── Enhanced Challenge Rendering with Interactive Elements ─────────────────
  function renderChallenges(chals) {
    if (!challengeContainer) return;

    // Clear existing challenges and states
    challengeContainer.innerHTML = "";
    Object.keys(challengeStates).forEach((key) => delete challengeStates[key]);

    const typeColors = {
      "multiple-choice": "#007bff",
      multiple_choice: "#007bff",
      debugging: "#ff8c00",
      "fill-in-the-blank": "#8a2be2",
      fill_in_blank: "#8a2be2",
    };

    chals.forEach((c, i) => {
      // Initialize challenge state
      initializeChallengeState(i);

      const card = document.createElement("div");
      card.className = "challenge-item";
      card.dataset.type = c.type;
      card.dataset.index = i;

      const borderColor = typeColors[c.type] || "#00ff41";
      card.style.setProperty("--border-color", borderColor);

      const typeLabel = c.type.includes("multiple")
        ? "Multiple Choice"
        : c.type === "debugging"
        ? "Debugging"
        : "Fill in the Blank";

      const aiIcon = c.ai_generated
        ? `<span class="ai-icon" title="AI-generated">🤖</span>`
        : "";

      card.innerHTML = `
        <div class="challenge-header">
          <span class="challenge-type">${typeLabel}</span>
          <h3>${c.topic}</h3>
          <span class="challenge-difficulty ${c.difficulty}">
            ${c.difficulty.charAt(0).toUpperCase() + c.difficulty.slice(1)}
          </span>
          ${aiIcon}
        </div>
        <div class="challenge-actions">
          <button class="btn btn-secondary hint-btn" data-index="${i}">
            <i class="fas fa-lightbulb"></i> Show Hint
          </button>
          <button class="btn btn-primary solve-btn" data-index="${i}">
            <i class="fas fa-play"></i> Solve Challenge
          </button>
          <button class="btn btn-secondary favorite-icon" data-challenge-id="${c.id}">
            <i class="fas fa-star"></i>
          </button>
        </div>
      `;

      challengeContainer.append(card);
    });

    // Add event listeners for buttons
    challengeContainer.addEventListener("click", handleChallengeButtonClick);

    // Update stats
    if (challengesCount) challengesCount.textContent = `${chals.length} challenges`;
    if (challengesSolved) challengesSolved.textContent = `0 solved`;

    // Reset filters
    document.querySelector(".filter-btn.active")?.classList.remove("active");
    document.querySelector(".filter-btn[data-filter=\"all\"]")?.classList.add("active");
    filterChallenges("all");

    showSection("display");
  }

  // ─── Enhanced Button Click Handler ──────────────────────────────────────────
  async function handleChallengeButtonClick(e) {
    e.preventDefault();
    e.stopPropagation();

    const button = e.target.closest("button");
    if (!button) return;

    const index = parseInt(button.dataset.index);
    const challengeId = button.dataset.challengeId;
    if (isNaN(index) && !challengeId) return;

    if (button.classList.contains("hint-btn")) {
      if (isNaN(index)) return;
      const challenge = allChallenges[index];
      const state = challengeStates[index];
      showHint(index, challenge, state);
    } else if (button.classList.contains("solve-btn")) {
      if (isNaN(index)) return;
      const challenge = allChallenges[index];
      const state = challengeStates[index];
      openChallengeModal(index, challenge, state);
    } else if (button.classList.contains("favorite-icon")) {
      if (!currentUser) {
        alert("Please login to favorite challenges.");
        return;
      }
      await toggleFavorite(challengeId, button);
    }
  }

  // ─── Favorite Challenges ────────────────────────────────────────────────────
  async function toggleFavorite(challengeId, button) {
    const favoritesRef = db
      .collection("users")
      .doc(currentUser.uid)
      .collection("favorites");
    const favoriteDocRef = favoritesRef.doc(challengeId);

    try {
      const doc = await favoriteDocRef.get();
      if (doc.exists) {
        await favoriteDocRef.delete();
        button.classList.remove("favorited");
        console.log("Challenge unfavorited");
      } else {
        await favoriteDocRef.set({
          challengeId: challengeId,
          favoritedAt: firebase.firestore.FieldValue.serverTimestamp(),
        });
        button.classList.add("favorited");
        console.log("Challenge favorited");
      }
      updateProfileUI(); // Update favorite count on profile
    } catch (error) {
      console.error("Error toggling favorite:", error);
      alert("Failed to update favorite status.");
    }
  }

  async function checkIfFavorited(challengeId) {
    if (!currentUser) return false;
    const doc = await db
      .collection("users")
      .doc(currentUser.uid)
      .collection("favorites")
      .doc(challengeId)
      .get();
    return doc.exists;
  }

  // ─── Enhanced Hint System ───────────────────────────────────────────────────
  async function showHint(index, challenge, state) {
    state.hintShown = true;

    try {
      // Get hint from backend
      const response = await fetch(`/api/challenges/${challenge.id}/hint`);
      let hint = challenge.hint || "Think about the key concepts in this topic.";
      
      if (response.ok) {
        const result = await response.json();
        hint = result.hint || hint;
      }

      // Create hint modal
      const hintModal = document.createElement("div");
      hintModal.className = "hint-modal";
      hintModal.innerHTML = `
        <div class="hint-content">
          <div class="hint-header">
            <h4>💡 Hint</h4>
            <button class="hint-close">&times;</button>
          </div>
          <div class="hint-body">
            <p>${hint}</p>
          </div>
        </div>
      `;

      document.body.appendChild(hintModal);
      hintModal.classList.add("show");

      // Close hint modal
      hintModal.querySelector(".hint-close").onclick = () => {
        hintModal.remove();
      };
      hintModal.onclick = (e) => {
        if (e.target === hintModal) hintModal.remove();
      };
    } catch (error) {
      console.error("Error getting hint:", error);
      // Fallback to default hint
      const hintModal = document.createElement("div");
      hintModal.className = "hint-modal";
      hintModal.innerHTML = `
        <div class="hint-content">
          <div class="hint-header">
            <h4>💡 Hint</h4>
            <button class="hint-close">&times;</button>
          </div>
          <div class="hint-body">
            <p>${challenge.hint || "Think about the key concepts in this topic."}</p>
          </div>
        </div>
      `;

      document.body.appendChild(hintModal);
      hintModal.classList.add("show");

      // Close hint modal
      hintModal.querySelector(".hint-close").onclick = () => {
        hintModal.remove();
      };
      hintModal.onclick = (e) => {
        if (e.target === hintModal) hintModal.remove();
      };
    }
  }

  // ─── Enhanced Challenge Modal with Interactive Elements ─────────────────────
  function openChallengeModal(index, challenge, state) {
    if (!challengeModal || !modalTitle || !modalBody) return;

    currentChallengeIndex = index;

    modalTitle.textContent = `${challenge.topic} — ${challenge.difficulty}`;

    let html = `
      <div class="challenge-question">
        <p>${challenge.question}</p>
      </div>
    `;

    // Check if challenge is solved - show review mode
    if (state.solved) {
      html += `
        <div class="review-mode-indicator">
          <div class="victory-animation">✓</div>
          <h4>Challenge Completed - Review Mode</h4>
        </div>
      `;

      // Always show code snippet for fill-in-the-blank challenges
      if (challenge.type.includes("fill")) {
        html += `
          <div class="code-section">
            <h5>Complete the code:</h5>
            <pre><code class="fill-code">${challenge.code_with_blanks}</code></pre>
          </div>
        `;
      } else if (challenge.type === "debugging") {
        html += `
          <div class="code-section">
            <h5>Code to Debug:</h5>
            <pre><code class="debug-code">${challenge.code_stub}</code></pre>
          </div>
        `;
      }

      html += `
        <div class="review-content">
          <div class="correct-answer-section">
            <h5><strong>Correct Answer:</strong></h5>
            <div>${getCorrectAnswerText(challenge)}</div>
          </div>
          <div class="hint-section">
            <h5><strong>Hint:</strong></h5>
            <p>${challenge.hint}</p>
          </div>
        </div>
      `;

      // Hide submit button and show close button only
      if (modalSubmit) modalSubmit.style.display = "none";
      if (modalHint) modalHint.style.display = "none";
    }
    // Check if challenge failed - show review mode with failure
    else if (state.attempts >= 3) {
      html += `
        <div class="review-mode-indicator">
          <div class="defeat-animation">✗</div>
          <h4>Challenge Failed - Review Mode</h4>
        </div>
      `;

      // Always show code snippet for failed challenges
      if (challenge.type.includes("fill")) {
        html += `
          <div class="code-section">
            <h5>Complete the code:</h5>
            <pre><code class="fill-code">${challenge.code_with_blanks}</code></pre>
          </div>
        `;
      } else if (challenge.type === "debugging") {
        html += `
          <div class="code-section">
            <h5>Code to Debug:</h5>
            <pre><code class="debug-code">${challenge.code_stub}</code></pre>
          </div>
        `;
      }

      html += `
        <div class="review-content">
          <div class="attempts-used">
            <p>You used all 3 attempts on this challenge.</p>
          </div>
          <div class="correct-answer-section">
            <h5><strong>Correct Answer:</strong></h5>
            <div>${getCorrectAnswerText(challenge)}</div>
          </div>
          <div class="hint-section">
            <h5><strong>Hint:</strong></h5>
            <p>${challenge.hint}</p>
          </div>
        </div>
      `;

      // Hide submit button and show close button only
      if (modalSubmit) modalSubmit.style.display = "none";
      if (modalHint) modalHint.style.display = "none";
    }
    // Active challenge mode
    else {
      html += `
        <div class="attempts-indicator">
          <span>Attempts: ${state.attempts}/3</span>
        </div>
      `;

      if (challenge.type.includes("multiple")) {
        html += '<div class="challenge-options">';
        challenge.options.forEach((option, i) => {
          html += `
            <label class="option-label">
              <input type="radio" name="modal-mcq" value="${i}">
              <span class="option-text">${option}</span>
            </label>
          `;
        });
        html += "</div>";
      } else if (challenge.type === "debugging") {
        html += `
          <div class="code-section">
            <h5>Code to Debug:</h5>
            <pre><code class="debug-code">${challenge.code_stub}</code></pre>
          </div>
          <div class="debug-input-section">
            <label for="debug-answer">Describe the bug and how to fix it:</label>
            <div class="debug-instructions">
              <p><strong>What to include in your answer:</strong></p>
              <ul>
                <li>Identify the specific line or part of code that has the bug</li>
                <li>Explain what type of error it is (syntax, logic, runtime, etc.)</li>
                <li>Describe exactly how to fix it (what to change)</li>
                <li>Mention key concepts like operators (=, ==), initialization, indexing, etc.</li>
              </ul>
            </div>
            <textarea id="debug-answer" class="debug-textarea" 
                      placeholder="Example: 'The bug is on line X where we use = instead of == for comparison. This should be changed to == to properly compare values instead of assigning them.'"></textarea>
          </div>
        `;
      } else if (challenge.type.includes("fill")) {
        html += `
          <div class="code-section">
            <h5>Complete the code:</h5>
            <pre><code class="fill-code">${challenge.code_with_blanks}</code></pre>
          </div>
          <div class="fill-inputs-section">
        `;
        challenge.blanks.forEach((blank) => {
          html += `
            <div class="fill-input-group">
              <label>Blank ${blank.blank_number}:</label>
              <select class="fill-select" data-blank="${blank.blank_number}">
                <option value="">Choose an option...</option>
                ${blank.options
                  .map((option) => `<option value="${option}">${option}</option>`)
                  .join("")}
              </select>
            </div>
          `;
        });
        html += "</div>";
      }

      // Show submit and hint buttons for active challenges
      if (modalSubmit) modalSubmit.style.display = "inline-flex";
      if (modalHint) modalHint.style.display = "inline-flex";
    }

    modalBody.innerHTML = html;
    challengeModal.classList.remove("hidden");
    challengeModal.classList.add("show");
  }

  // ─── Enhanced Modal Submit Handler ──────────────────────────────────────────
  if (modalSubmit) {
    modalSubmit.addEventListener("click", async () => {
      if (currentChallengeIndex === null || !modalBody) return;

      const challenge = allChallenges[currentChallengeIndex];
      const state = challengeStates[currentChallengeIndex];

      if (state.attempts >= 3 || state.solved) return;

      let userAnswer = null;

      // Get user answer based on challenge type
      if (challenge.type.includes("multiple")) {
        const selected = modalBody.querySelector(
          "input[name=\"modal-mcq\"]:checked"
        );
        if (!selected) {
          alert("Please select an answer");
          return;
        }
        userAnswer = parseInt(selected.value);
      } else if (challenge.type === "debugging") {
        userAnswer = modalBody.querySelector("#debug-answer").value.trim();
        if (!userAnswer) {
          alert("Please describe the bug and how to fix it");
          return;
        }
      } else if (challenge.type.includes("fill")) {
        const selects = modalBody.querySelectorAll(".fill-select");
        userAnswer = {};
        let allFilled = true;

        selects.forEach((select) => {
          const blankNum = select.dataset.blank;
          const value = select.value;
          if (!value) allFilled = false;
          userAnswer[blankNum] = value;
        });

        if (!allFilled) {
          alert("Please fill in all blanks");
          return;
        }
      }

      try {
        // Submit answer to backend
        const response = await fetch(`/api/challenges/${challenge.id}/attempt`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ answer: userAnswer })
        });

        if (!response.ok) {
          throw new Error(`Failed to submit answer: ${response.status}`);
        }

        const result = await response.json();

        // Update local state based on backend response
        state.attempts = result.attempts;
        state.solved = result.correct;

        if (result.correct) {
          showFeedback("Correct! Well done! 🎉", "success");
          // Update solved count in Firestore
          if (currentUser) {
            const userRef = db.collection("users").doc(currentUser.uid);
            userRef.update({
              solvedChallenges: firebase.firestore.FieldValue.increment(1),
            });
          }
        } else {
          if (result.attempts >= 3) {
            showFeedback("Incorrect. You've used all attempts. 😞", "failure");
          } else {
            showFeedback(
              `Incorrect. ${3 - result.attempts} attempts remaining.`,
              "warning"
            );
          }
        }

        // Update challenge card
        updateChallengeCard(currentChallengeIndex);

        // Close modal if solved or no attempts left
        if (result.correct || result.attempts >= 3) {
          setTimeout(() => {
            challengeModal.classList.add("hidden");
            challengeModal.classList.remove("show");
            currentChallengeIndex = null;
          }, 2000);
        } else {
          // Update attempts indicator
          const attemptsEl = modalBody.querySelector(".attempts-indicator span");
          if (attemptsEl) {
            attemptsEl.textContent = `Attempts: ${result.attempts}/3`;
          }
        }
      } catch (error) {
        console.error("Error submitting answer:", error);
        showFeedback("Failed to submit answer. Please try again.", "warning");
      }
    });
  }

  // ─── Enhanced Feedback System with Animations ──────────────────────────────
  function showFeedback(message, type) {
    if (!modalBody) return;

    const feedback = document.createElement("div");
    feedback.className = `modal-feedback ${type}`;

    // Create animation element based on type
    let animationElement = "";
    if (type === "success") {
      animationElement = '<div class="victory-animation">✓</div>';
    } else if (type === "failure") {
      animationElement = '<div class="defeat-animation">✗</div>';
    }

    feedback.innerHTML = `
      <div class="feedback-content">
        ${animationElement}
        <span class="feedback-message">${message}</span>
      </div>
    `;

    const existingFeedback = modalBody.querySelector(".modal-feedback");
    if (existingFeedback) existingFeedback.remove();

    modalBody.appendChild(feedback);

    // Auto-remove after 3 seconds for non-final states
    if (type === "warning") {
      setTimeout(() => {
        if (feedback.parentNode) feedback.remove();
      }, 3000);
    }
  }

  // ─── Filters ────────────────────────────────────────────────────────────────
  function filterChallenges(filter) {
    if (!challengeContainer) return;
    challengeContainer.querySelectorAll(".challenge-item").forEach((card) => {
      card.style.display =
        filter === "all" || card.dataset.type === filter ? "block" : "none";
    });
  }

  filterBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelector(".filter-btn.active")?.classList.remove("active");
      btn.classList.add("active");
      filterChallenges(btn.dataset.filter);
    });
  });

  // ─── Modal close handlers ───────────────────────────────────────────────────
  if (modalClose) {
    modalClose.addEventListener("click", () => {
      challengeModal.classList.add("hidden");
      challengeModal.classList.remove("show");
      currentChallengeIndex = null;
    });
  }

  if (challengeModal) {
    challengeModal.addEventListener("click", (e) => {
      if (e.target === challengeModal) {
        challengeModal.classList.add("hidden");
        challengeModal.classList.remove("show");
        currentChallengeIndex = null;
      }
    });
  }

  // ─── Modal Hint Button ──────────────────────────────────────────────────────
  if (modalHint) {
    modalHint.addEventListener("click", () => {
      if (currentChallengeIndex !== null) {
        const challenge = allChallenges[currentChallengeIndex];
        const state = challengeStates[currentChallengeIndex];
        showHint(currentChallengeIndex, challenge, state);
      }
    });
  }

  // ─── Auth Modal Logic ───────────────────────────────────────────────────────
  if (authButton) {
    authButton.addEventListener("click", () => {
      authModal.classList.remove("hidden");
      authModal.classList.add("show");
      setAuthMode(true); // Always start in login mode
    });
  }

  if (authModalClose) {
    authModalClose.addEventListener("click", () => {
      authModal.classList.add("hidden");
      authModal.classList.remove("show");
    });
  }

  if (authModal) {
    authModal.addEventListener("click", (e) => {
      if (e.target === authModal) {
        authModal.classList.add("hidden");
        authModal.classList.remove("show");
      }
    });
  }

  if (switchToSignup) {
    switchToSignup.addEventListener("click", (e) => {
      e.preventDefault();
      setAuthMode(false);
    });
  }

  if (switchToLogin) {
    switchToLogin.addEventListener("click", (e) => {
      e.preventDefault();
      setAuthMode(true);
    });
  }

  avatarOptions.forEach((img) => {
    img.addEventListener("click", () => {
      avatarOptions.forEach((opt) => opt.classList.remove("active"));
      img.classList.add("active");
      selectedAvatar = img.dataset.avatar;
    });
  });

  function setAuthMode(isLogin) {
    isLoginMode = isLogin;
    if (isLoginMode) {
      authModalTitle.textContent = "Login";
      authSubmitButton.textContent = "Login";
      authUsernameGroup.classList.add("hidden");
      authAvatarGroup.classList.add("hidden");
      switchToSignup.style.display = "inline";
      switchToLogin.style.display = "none";
    } else {
      authModalTitle.textContent = "Sign Up";
      authSubmitButton.textContent = "Sign Up";
      authUsernameGroup.classList.remove("hidden");
      authAvatarGroup.classList.remove("hidden");
      switchToSignup.style.display = "none";
      switchToLogin.style.display = "inline";
    }
  }

  if (authForm) {
    authForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = authEmail.value;
      const password = authPassword.value;

      if (isLoginMode) {
        // Login
        try {
          await auth.signInWithEmailAndPassword(email, password);
          authModal.classList.add("hidden");
          alert("Logged in successfully!");
        } catch (error) {
          alert(`Login failed: ${error.message}`);
        }
      } else {
        // Signup
        const displayName = authUsername.value;
        try {
          const userCredential = await auth.createUserWithEmailAndPassword(
            email,
            password
          );
          await userCredential.user.updateProfile({
            displayName: displayName,
            photoURL: `https://api.dicebear.com/7.x/pixel-art/svg?seed=${selectedAvatar}`,
          });
          // Save user data to Firestore
          await db.collection("users").doc(userCredential.user.uid).set({
            email: email,
            displayName: displayName,
            avatar: selectedAvatar,
            solvedChallenges: 0,
            createdAt: firebase.firestore.FieldValue.serverTimestamp(),
          });
          authModal.classList.add("hidden");
          alert("Signed up successfully!");
        } catch (error) {
          alert(`Signup failed: ${error.message}`);
        }
      }
    });
  }

  // ─── Auth State Observer ────────────────────────────────────────────────────
  auth.onAuthStateChanged(async (user) => {
    currentUser = user;
    if (user) {
      // User is signed in.
      authButton.textContent = "Profile";
      authButton.removeEventListener("click", () => {
        authModal.classList.remove("hidden");
        authModal.classList.add("show");
        setAuthMode(true);
      });
      authButton.addEventListener("click", () => {
        showSection("profile");
        updateProfileUI();
      });
      // Fetch user data from Firestore
      const userDoc = await db.collection("users").doc(user.uid).get();
      if (userDoc.exists) {
        const userData = userDoc.data();
        currentUser = { ...user, ...userData }; // Merge Firestore data
      }
      updateProfileUI();
      
      // Show upload section by default when logged in
      showSection("upload");
    } else {
      // User is signed out - require login
      authButton.textContent = "Login / Signup";
      authButton.removeEventListener("click", () => {
        showSection("profile");
        updateProfileUI();
      });
      authButton.addEventListener("click", () => {
        authModal.classList.remove("hidden");
        authModal.classList.add("show");
        setAuthMode(true);
      });
      
      // Force login modal to show if not authenticated
      authModal.classList.remove("hidden");
      authModal.classList.add("show");
      setAuthMode(true);
    }
  });

  // ─── Navigation Event Listeners ─────────────────────────────────────────────
  if (navUpload) {
    navUpload.addEventListener("click", () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      showSection("upload");
    });
  }

  if (navChallenges) {
    navChallenges.addEventListener("click", () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      if (allChallenges.length === 0) {
        alert("No challenges available. Please upload a document first.");
        return;
      }
      showSection("display");
    });
  }

  if (navFavorites) {
    navFavorites.addEventListener("click", () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      showSection("favorites");
      loadFavorites();
    });
  }

  if (navProfile) {
    navProfile.addEventListener("click", () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      showSection("profile");
      updateProfileUI();
    });
  }

  // ─── Profile Page Logic ─────────────────────────────────────────────────────
  async function updateProfileUI() {
    if (!currentUser) return;

    profileDisplayName.textContent = currentUser.displayName || "N/A";
    profileEmail.textContent = currentUser.email || "N/A";
    profileAvatar.src = currentUser.photoURL || `https://api.dicebear.com/7.x/pixel-art/svg?seed=${currentUser.avatar || 'avatar1'}`;

    // Fetch solved challenges count
    const userDoc = await db.collection("users").doc(currentUser.uid).get();
    if (userDoc.exists) {
      const userData = userDoc.data();
      profileSolvedCount.textContent = userData.solvedChallenges || 0;
    }

    // Fetch favorite challenges count
    const favoritesSnapshot = await db
      .collection("users")
      .doc(currentUser.uid)
      .collection("favorites")
      .get();
    profileFavoritesCount.textContent = favoritesSnapshot.size;

    // Fetch uploaded documents count
    const uploadsSnapshot = await db
      .collection("users")
      .doc(currentUser.uid)
      .collection("uploads")
      .get();
    profileUploadsCount.textContent = uploadsSnapshot.size;
  }

  // ─── Favorites Page Logic ───────────────────────────────────────────────────
  async function loadFavorites() {
    if (!currentUser || !favoritesList) return;

    try {
      // Clear existing favorites
      favoritesList.innerHTML = "";
      
      // Fetch user's favorites from Firestore
      const favoritesSnapshot = await db
        .collection("users")
        .doc(currentUser.uid)
        .collection("favorites")
        .get();

      if (favoritesSnapshot.empty) {
        // Show empty state
        if (noFavorites) {
          noFavorites.classList.remove("hidden");
        }
        return;
      }

      // Hide empty state
      if (noFavorites) {
        noFavorites.classList.add("hidden");
      }

      // Create favorite challenge cards
      const favoritePromises = favoritesSnapshot.docs.map(async (doc) => {
        const favoriteData = doc.data();
        const challengeId = favoriteData.challengeId;
        
        // Find the challenge in allChallenges
        const challenge = allChallenges.find(c => c.id === challengeId);
        
        if (challenge) {
          return createFavoriteCard(challenge, favoriteData);
        }
        return null;
      });

      const favoriteCards = await Promise.all(favoritePromises);
      
      favoriteCards.forEach(card => {
        if (card) {
          favoritesList.appendChild(card);
        }
      });

    } catch (error) {
      console.error("Error loading favorites:", error);
      alert("Failed to load favorites. Please try again.");
    }
  }

  function createFavoriteCard(challenge, favoriteData) {
    const card = document.createElement("div");
    card.className = "challenge-item favorite-item";
    card.dataset.challengeId = challenge.id;

    const typeColors = {
      "multiple-choice": "#007bff",
      multiple_choice: "#007bff",
      debugging: "#ff8c00",
      "fill-in-the-blank": "#8a2be2",
      fill_in_blank: "#8a2be2",
    };

    const borderColor = typeColors[challenge.type] || "#00ff41";
    card.style.setProperty("--border-color", borderColor);

    const typeLabel = challenge.type.includes("multiple")
      ? "Multiple Choice"
      : challenge.type === "debugging"
      ? "Debugging"
      : "Fill in the Blank";

    const favoritedDate = favoriteData.favoritedAt 
      ? new Date(favoriteData.favoritedAt.toDate()).toLocaleDateString()
      : "Unknown";

    card.innerHTML = `
      <div class="challenge-header">
        <span class="challenge-type">${typeLabel}</span>
        <h3>${challenge.topic}</h3>
        <span class="challenge-difficulty ${challenge.difficulty}">
          ${challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
        </span>
        <span class="favorite-date">⭐ ${favoritedDate}</span>
      </div>
      <div class="challenge-preview">
        <p>${challenge.question.substring(0, 100)}${challenge.question.length > 100 ? '...' : ''}</p>
      </div>
      <div class="challenge-actions">
        <button class="btn btn-secondary hint-btn" data-challenge-id="${challenge.id}">
          <i class="fas fa-lightbulb"></i> Show Hint
        </button>
        <button class="btn btn-primary solve-btn" data-challenge-id="${challenge.id}">
          <i class="fas fa-play"></i> Solve Challenge
        </button>
        <button class="btn btn-danger unfavorite-btn" data-challenge-id="${challenge.id}">
          <i class="fas fa-star"></i> Remove
        </button>
      </div>
    `;

    // Add event listeners for favorite card buttons
    card.querySelector('.hint-btn').addEventListener('click', async () => {
      const challengeIndex = allChallenges.findIndex(c => c.id === challenge.id);
      if (challengeIndex !== -1) {
        const state = challengeStates[challengeIndex] || { hintShown: false };
        await showHint(challengeIndex, challenge, state);
      }
    });

    card.querySelector('.solve-btn').addEventListener('click', () => {
      const challengeIndex = allChallenges.findIndex(c => c.id === challenge.id);
      if (challengeIndex !== -1) {
        const state = challengeStates[challengeIndex] || { attempts: 0, solved: false };
        openChallengeModal(challengeIndex, challenge, state);
      }
    });

    card.querySelector('.unfavorite-btn').addEventListener('click', async () => {
      await toggleFavorite(challenge.id, card.querySelector('.unfavorite-btn'));
      // Reload favorites after unfavoriting
      setTimeout(() => loadFavorites(), 500);
    });

    return card;
  }

  if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
      try {
        await auth.signOut();
        alert("Logged out successfully!");
        showSection("upload");
      } catch (error) {
        alert(`Logout failed: ${error.message}`);
      }
    });
  }

  // ─── Retry & Theme ─────────────────────────────────────────────────────────
  if (retryBtn) retryBtn.onclick = () => showSection("upload");

  document.getElementById("theme-toggle")?.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const next = current === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("pqgen-theme", next);

    // Update icon
    const icon = document.querySelector("#theme-toggle i");
    if (icon) {
      icon.className = next === "dark" ? "fas fa-sun" : "fas fa-moon";
    }
  });

  const saved = localStorage.getItem("pqgen-theme");
  if (saved) {
    document.documentElement.setAttribute("data-theme", saved);
    const icon = document.querySelector("#theme-toggle i");
    if (icon) {
      icon.className = saved === "dark" ? "fas fa-sun" : "fas fa-moon";
    }
  }

  // Auth state observer will handle initial section display
});




