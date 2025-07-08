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
let initialAuthResolved = false;
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
const fileInput         = document.getElementById("file-input");
const uploadArea        = document.getElementById("upload-area");
const fileNameEl        = document.getElementById("file-name");
const fileStateEl       = document.getElementById("file-state");
const uploadBtn         = document.getElementById("upload-btn");

// ─── Extraction progress refs ───────────────────────────────────────────────
const progressMsg       = document.getElementById("progress-message");
const progressFill      = document.getElementById("progress-fill");
const progressPct       = document.getElementById("progress-percentage");

// ─── Topic selection refs ───────────────────────────────────────────────────
const topicsList        = document.getElementById("topics-list");
const selectAllBtn      = document.getElementById("select-all-topics");
const clearAllBtn       = document.getElementById("clear-topics");
const generateBtn       = document.getElementById("generate-challenges-btn");

// ─── Generation progress refs ───────────────────────────────────────────────
const genMsg            = document.getElementById("generation-message");
const genFill           = document.getElementById("generation-progress-fill");
const genPct            = document.getElementById("generation-progress-text");

// ─── Challenges display refs ─────────────────────────────────────────────────
const challengeContainer = document.getElementById("challenge-container");
const challengesCount   = document.getElementById("challenges-count");
const challengesSolved  = document.getElementById("challenges-solved");

// ─── Filter buttons ─────────────────────────────────────────────────────────
const filterBtns        = Array.from(document.querySelectorAll(".filter-btn"));

// ─── Error & retry refs ─────────────────────────────────────────────────────
const errorMessageEl    = document.getElementById("error-message");
const retryBtn          = document.getElementById("retry-button");

// ─── Modal refs ─────────────────────────────────────────────────────────────
const challengeModal    = document.getElementById("challenge-modal");
const modalTitle        = document.getElementById("modal-title");
const modalBody         = document.getElementById("modal-body");
const modalClose        = document.getElementById("modal-close");
const modalHint         = document.getElementById("modal-hint");
const modalSubmit       = document.getElementById("modal-submit");

// ─── Auth Modal refs ────────────────────────────────────────────────────────
const authButton        = document.getElementById("auth-button");
const authModal         = document.getElementById("auth-modal");
const authModalClose    = document.getElementById("auth-modal-close");
const authModalTitle    = document.getElementById("auth-modal-title");
const authForm          = document.getElementById("auth-form");
const authEmail         = document.getElementById("auth-email");
const authUsernameGroup = document.getElementById("auth-username-group");
const authUsername      = document.getElementById("auth-username");
const authPassword      = document.getElementById("auth-password");
const authAvatarGroup   = document.getElementById("auth-avatar-group");
const avatarOptions     = document.querySelectorAll(".avatar-option");
const authSubmitButton  = document.getElementById("auth-submit-button");
const switchToSignup    = document.getElementById("switch-to-signup");
const switchToLogin     = document.getElementById("switch-to-login");
let isLoginMode         = true;
let selectedAvatar      = "avatar1";

// ─── Profile refs ───────────────────────────────────────────────────────────
const profileDisplayName  = document.getElementById("profile-display-name");
const profileEmail        = document.getElementById("profile-email");
const profileAvatar       = document.getElementById("profile-avatar");
const profileSolvedCount  = document.getElementById("profile-solved-count");
const profileFavoritesCount = document.getElementById("profile-favorites-count");
const profileUploadsCount = document.getElementById("profile-uploads-count");
const logoutButton        = document.getElementById("logout-button");

// ─── Favorites refs ─────────────────────────────────────────────────────────
const favoritesList      = document.getElementById("favorites-list");
const noFavorites        = document.getElementById("no-favorites");
const uploadHistoryEl    = document.getElementById("upload-history");

// ─── Navigation refs ────────────────────────────────────────────────────────
const navUpload          = document.getElementById("nav-upload");
const navChallenges      = document.getElementById("nav-challenges");
const navFavorites       = document.getElementById("nav-favorites");
const navProfile         = document.getElementById("nav-profile");

  // ─── State ───────────────────────────────────────────────────────────────────
  let currentDocId = null;
  let allTopics = [];
  let allChallenges = [];
  // Make allChallenges globally accessible for favorites
  window.allChallenges = allChallenges;
  let currentChallengeIndex = null;

  // ─── Restore Challenges from localStorage ───────────────────────────────────
  function restoreChallengesFromStorage() {
    try {
      const storedChallenges = localStorage.getItem('pqgen-challenges');
      if (storedChallenges) {
        const challenges = JSON.parse(storedChallenges);
        allChallenges = challenges;
        window.allChallenges = challenges;
        console.log('Challenges restored from localStorage:', challenges.length);
        return challenges;
      }
    } catch (e) {
      console.warn('Failed to restore challenges from localStorage:', e);
    }
    return [];
  }

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

          // Add to upload history
          onUploadSuccess(file.name);

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
          window.allChallenges = challenges; // Update global reference
          
          // Store challenges in localStorage for persistence
          try {
            localStorage.setItem('pqgen-challenges', JSON.stringify(challenges));
            console.log('Challenges saved to localStorage:', challenges.length);
          } catch (e) {
            console.warn('Failed to save challenges to localStorage:', e);
          }
          
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
        ? `<span class="ai-icon" title="AI-generated"><i class="fas fa-star"></i></span>`
        : "";

      card.innerHTML = `
        <div class="challenge-header">
          <span class="challenge-type">${typeLabel}</span>
          <h3>${c.topic}</h3>
          <span class="challenge-difficulty ${c.difficulty}">
            ${c.difficulty.charAt(0).toUpperCase() + c.difficulty.slice(1)}
          </span>
          ${aiIcon}
          <button class="favorite-star-btn" data-challenge-id="${c.id}" title="Add to favorites">
            ⭐
          </button>
        </div>
        <div class="challenge-actions">
          <button class="btn btn-secondary hint-btn" data-index="${i}">
            <i class="fas fa-lightbulb"></i> Show Hint
          </button>
          <button class="btn btn-primary solve-btn" data-index="${i}">
            <i class="fas fa-play"></i> Solve Challenge
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

    // Update profile generated count
    updateProfileGeneratedCount();

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
    } else if (button.classList.contains("favorite-star-btn")) {
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
      // Add loading animation
      button.style.transform = "scale(1.2)";
      button.style.transition = "all 0.3s ease";
      
      const doc = await favoriteDocRef.get();
      if (doc.exists) {
        await favoriteDocRef.delete();
        button.classList.remove("favorited");
        button.textContent = "⭐"; // Empty star
        button.title = "Add to favorites";
        
        // Unfavorite animation
        button.style.transform = "scale(0.8)";
        setTimeout(() => {
          button.style.transform = "scale(1)";
        }, 200);
        
        console.log("Challenge unfavorited");
      } else {
        // Find the full challenge data
        let challengeData = null;
        console.log("Looking for challenge data for ID:", challengeId);
        console.log("window.allChallenges:", window.allChallenges);
        
        if (window.allChallenges && Array.isArray(window.allChallenges)) {
          challengeData = window.allChallenges.find(c => c.id === challengeId);
          console.log("Found in allChallenges:", challengeData);
        }
        
        if (!challengeData) {
          // Try to restore from localStorage
          console.log("Challenge not found in allChallenges, trying localStorage");
          const restoredChallenges = restoreChallengesFromStorage();
          console.log("Restored challenges:", restoredChallenges);
          if (restoredChallenges.length > 0) {
            challengeData = restoredChallenges.find(c => c.id === challengeId);
            console.log("Found in localStorage:", challengeData);
          }
        }
        
        // Store the complete challenge data in Firestore
        const favoriteData = {
          challengeId: challengeId,
          favoritedAt: firebase.firestore.FieldValue.serverTimestamp(),
        };
        
        // Include full challenge data if available
        if (challengeData) {
          favoriteData.challengeData = {
            id: challengeData.id,
            question: challengeData.question,
            type: challengeData.type,
            topic: challengeData.topic,
            difficulty: challengeData.difficulty,
            options: challengeData.options || null,
            hint: challengeData.hint || null,
            ai_generated: challengeData.ai_generated || false,
            answer: challengeData.answer || null
          };
          console.log("✅ Storing full challenge data:", favoriteData.challengeData);
        } else {
          console.error("❌ Challenge data not found for ID:", challengeId);
          console.log("Available challenge IDs:", window.allChallenges ? window.allChallenges.map(c => c.id) : "No challenges");
          // Still save the favorite but without full data
        }
        
        console.log("Final favoriteData to save:", favoriteData);
        
        await favoriteDocRef.set(favoriteData);
        button.classList.add("favorited");
        button.textContent = "🌟"; // Filled star
        button.title = "Remove from favorites";
        
        // Favorite animation with sparkle effect
        button.style.transform = "scale(1.5)";
        button.style.filter = "drop-shadow(0 0 10px gold)";
        setTimeout(() => {
          button.style.transform = "scale(1)";
          button.style.filter = "none";
        }, 300);
        
        console.log("Challenge favorited with full data");
      }
      updateProfileUI(); // Update favorite count on profile
    } catch (error) {
      console.error("Error toggling favorite:", error);
      alert("Failed to update favorite status.");
      // Reset button state on error
      button.style.transform = "scale(1)";
      button.style.filter = "none";
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
            userRef.set({
              solvedChallenges: firebase.firestore.FieldValue.increment(1),
            }, { merge: true });
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

  // ─── Avatar Selection Logic ────────────────────────────────────────────────
  function setupAvatarSelection() {
    // Setup avatar selection for auth modal
    const authAvatarOptions = document.querySelectorAll("#auth-avatar-group .avatar-option");
    authAvatarOptions.forEach((img) => {
      img.addEventListener("click", () => {
        authAvatarOptions.forEach((opt) => opt.classList.remove("active"));
        img.classList.add("active");
        selectedAvatar = img.dataset.avatar;
      });
    });

    // Setup avatar selection for profile page
    const profileAvatarOptions = document.querySelectorAll("#profile-avatar-options .avatar-option");
    profileAvatarOptions.forEach((img) => {
      img.addEventListener("click", async () => {
        const firebaseUser = auth.currentUser;
        if (!firebaseUser || !currentUser) {
          showProfileMessage("Please log in to update your profile.", "error");
          return;
        }
        
        const newAvatar = img.dataset.avatar;
        
        if (newAvatar === currentUser.avatar) {
          showProfileMessage("This avatar is already selected.", "error");
          return;
        }
        
        try {
          // Update user profile in Firebase Auth
          await firebaseUser.updateProfile({
            photoURL: `${newAvatar}.png`
          });
          
          // Update user data in Firestore
          await db.collection("users").doc(firebaseUser.uid).set({
            avatar: newAvatar
          }, { merge: true });
          
          // Update local user data
          currentUser.avatar = newAvatar;
          
          // Update UI
          profileAvatarOptions.forEach((opt) => opt.classList.remove("active"));
          img.classList.add("active");
          
          // Update profile avatar display
          updateProfileUI();
          
          showProfileMessage("Avatar updated successfully!", "success");
          console.log("Avatar updated successfully");
        } catch (error) {
          console.error("Error updating avatar:", error);
          showProfileMessage("Failed to update avatar. Please try again.", "error");
        }
      });
    });
  }

  // ─── Profile Editing Functionality ──────────────────────────────────────────
  
  // Profile editing refs
  const profileEditName = document.getElementById("profile-edit-name");
  const saveDisplayNameBtn = document.getElementById("save-display-name");

  // Display name editing functionality
  if (saveDisplayNameBtn && profileEditName) {
    saveDisplayNameBtn.addEventListener("click", async () => {
      const firebaseUser = auth.currentUser;
      if (!firebaseUser || !currentUser) {
        showProfileMessage("Please log in to update your profile.", "error");
        return;
      }

      const newDisplayName = profileEditName.value.trim();
      if (!newDisplayName) {
        showProfileMessage("Please enter a display name.", "error");
        return;
      }

      if (newDisplayName === currentUser.displayName) {
        showProfileMessage("Display name is already set to this value.", "error");
        return;
      }

      try {
        // Show loading state
        saveDisplayNameBtn.classList.add("loading");
        saveDisplayNameBtn.disabled = true;

        // Update Firebase Auth profile
        await firebaseUser.updateProfile({
          displayName: newDisplayName
        });

        // Update Firestore user document
        await db.collection("users").doc(firebaseUser.uid).set({
          displayName: newDisplayName,
        }, { merge: true });

        // Update local currentUser object
        currentUser.displayName = newDisplayName;

        // Update profile display
        if (profileDisplayName) {
          profileDisplayName.textContent = newDisplayName;
        }

        // Clear input and show success message
        profileEditName.value = "";
        showProfileMessage("Display name updated successfully!", "success");

        console.log("Display name updated successfully to:", newDisplayName);
      } catch (error) {
        console.error("Error updating display name:", error);
        showProfileMessage("Failed to update display name. Please try again.", "error");
      } finally {
        // Remove loading state
        saveDisplayNameBtn.classList.remove("loading");
        saveDisplayNameBtn.disabled = false;
      }
    });

    // Allow Enter key to save display name
    profileEditName.addEventListener("keypress", (e) => {
      if (e.key === "Enter") {
        saveDisplayNameBtn.click();
      }
    });
  }

  // Function to show profile update messages
  function showProfileMessage(message, type) {
    // Remove any existing messages
    const existingMessages = document.querySelectorAll(".profile-update-message");
    existingMessages.forEach(msg => msg.remove());

    // Create new message element
    const messageEl = document.createElement("div");
    messageEl.className = `profile-update-message ${type}`;
    messageEl.textContent = message;

    // Find the best place to insert the message
    const profileEditingSection = document.querySelector(".profile-editing-section");
    if (profileEditingSection) {
      profileEditingSection.appendChild(messageEl);
    }

    // Auto-remove message after 4 seconds
    setTimeout(() => {
      if (messageEl.parentNode) {
        messageEl.classList.add("fade-out");
        setTimeout(() => {
          messageEl.remove();
        }, 300);
      }
    }, 4000);
  }

  // Call setup function after DOM is loaded
  setupAvatarSelection();

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
            photoURL: `${selectedAvatar}.png`,
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
auth.onAuthStateChanged(async (user) => {
  console.log("Auth state changed:", user ? "User signed in" : "User signed out");
  
  if (user) {
    // User is authenticated - fetch and merge Firestore data
    try {
      console.log("Fetching user data from Firestore for UID:", user.uid);
      
      const userRef = db.collection("users").doc(user.uid);
      const userDoc = await userRef.get();

      // If no Firestore doc yet, create one
      if (!userDoc.exists) {
        await userRef.set({
          displayName:       user.displayName,
          email:             user.email,
          avatar:            "avatar1",
          solvedChallenges:  0,
          createdAt:         firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });
        console.log("Created missing user document in Firestore");
      }

      // Merge Auth + Firestore data into currentUser
      const freshData = (await userRef.get()).data();
      currentUser = {
        uid:               user.uid,
        email:             user.email,
        emailVerified:     user.emailVerified,
        displayName:       freshData.displayName,
        avatar:            freshData.avatar,
        solvedChallenges:  freshData.solvedChallenges,
        createdAt:         freshData.createdAt
      };
      console.log("Merged currentUser object:", currentUser);

      // Update UI for authenticated user
      authModal.classList.add("hidden");
      authModal.classList.remove("show");
      
      authButton.textContent = "Logout";
      authButton.setAttribute("data-state", "logout");
      authButton.onclick = async () => {
        authButton.classList.add("loading");
        try {
          await auth.signOut();
          console.log("User signed out successfully");
        } catch (error) {
          console.error("Error signing out:", error);
          alert("Failed to sign out. Please try again.");
        } finally {
          authButton.classList.remove("loading");
        }
      };
      
      // Refresh UI and data
      await updateProfileUI();
      await loadFavoritesList();
      await loadUploadHistory();
      showSection("upload");
      console.log("User authentication and UI update completed");
      
    } catch (error) {
      console.error("Error fetching user data from Firestore:", error);
      
      // Fallback to Auth data only
      currentUser = {
        uid:               user.uid,
        email:             user.email,
        emailVerified:     user.emailVerified,
        displayName:       user.displayName || "User",
        avatar:            "avatar1",
        solvedChallenges:  0
      };
      
      authModal.classList.add("hidden");
      authButton.textContent = "Logout";
      authButton.setAttribute("data-state", "logout");
      authButton.onclick = async () => {
        authButton.classList.add("loading");
        try {
          await auth.signOut();
          console.log("User signed out successfully");
        } catch (err) {
          console.error("Error signing out:", err);
          alert("Failed to sign out. Please try again.");
        } finally {
          authButton.classList.remove("loading");
        }
      };
      
      showSection("upload");
      alert("Warning: Could not load profile data. Some features may not work correctly.");
    }
    
  } else {
    // User is not authenticated - show login modal
    console.log("User not authenticated, showing login modal");
    
    currentUser = null;
    authButton.textContent = "Login / Signup";
    authButton.setAttribute("data-state", "login");
    authButton.onclick = () => {
      authModal.classList.remove("hidden");
      authModal.classList.add("show");
      setAuthMode(true);
    };
    
    authModal.classList.remove("hidden");
    authModal.classList.add("show");
    setAuthMode(true);
    showSection("upload");
    console.log("Login modal displayed for unauthenticated user");
  }
  
  // Mark initial auth resolution as complete
  if (!initialAuthResolved) {
    initialAuthResolved = true;
    console.log("Initial auth state resolved");
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
    navFavorites.addEventListener("click", async () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      showSection("favorites");
      await loadFavoritesList();
    });
  }

  if (navProfile) {
    navProfile.addEventListener("click", async () => {
      if (!currentUser) {
        alert("Please login to access this feature.");
        return;
      }
      showSection("profile");
      await updateProfileUI();
      await loadUploadHistory();
    });
  }

async function updateProfileUI() {
  if (!currentUser) {
    console.log("No currentUser available for profile update");
    return;
  }

  console.log("Updating profile UI with currentUser data:", currentUser);

  // Update basic profile information
  if (profileDisplayName) {
    profileDisplayName.textContent = currentUser.displayName || "N/A";
  }
  
  if (profileEmail) {
    profileEmail.textContent = currentUser.email || "N/A";
  }
  
  // Update profile avatar with new system
  const userAvatar = currentUser.avatar || 'avatar1';
  if (profileAvatar) {
    profileAvatar.src = `${userAvatar}.png`;
  }

  // Update profile editing fields
  const profileEditName = document.getElementById("profile-edit-name");
  if (profileEditName) {
    profileEditName.placeholder = `Current: ${currentUser.displayName || "User"}`;
  }

  // Highlight selected avatar in profile page
  const profileAvatarOptions = document.querySelectorAll("#profile-avatar-options .avatar-option");
  profileAvatarOptions.forEach((opt) => opt.classList.remove("active"));
  const selectedOption = document.querySelector(`#profile-avatar-options .avatar-option[data-avatar="${userAvatar}"]`);
  if (selectedOption) {
    selectedOption.classList.add("active");
  }

  try {
    // Fetch fresh data from Firestore for accurate counts
    const userDoc = await db.collection("users").doc(currentUser.uid).get();
    if (userDoc.exists) {
      const userData = userDoc.data();
      
      // Update solved challenges count
      if (profileSolvedCount) {
        profileSolvedCount.textContent = userData.solvedChallenges || 0;
      }
      
      console.log("Updated solved challenges count:", userData.solvedChallenges || 0);
    }

    // Fetch favorite challenges count
    const favoritesSnapshot = await db
      .collection("users")
      .doc(currentUser.uid)
      .collection("favorites")
      .get();
    
    if (profileFavoritesCount) {
      profileFavoritesCount.textContent = favoritesSnapshot.size;
    }
    
    console.log("Updated favorites count:", favoritesSnapshot.size);

    // Fetch uploaded documents count
    const uploadsSnapshot = await db
      .collection("users")
      .doc(currentUser.uid)
      .collection("uploads")
      .get();
    
    if (profileUploadsCount) {
      profileUploadsCount.textContent = uploadsSnapshot.size;
    }
    
    console.log("Updated uploads count:", uploadsSnapshot.size);
    
  } catch (error) {
    console.error("Error fetching profile statistics:", error);
    
    // Set default values if fetch fails
    if (profileSolvedCount) profileSolvedCount.textContent = "0";
    if (profileFavoritesCount) profileFavoritesCount.textContent = "0";
    if (profileUploadsCount) profileUploadsCount.textContent = "0";
  }
  
  console.log("Profile UI update completed");
}

  // ─── Logout Functionality ──────────────────────────────────────────────────
  if (logoutButton) {
    logoutButton.addEventListener("click", async () => {
      try {
        await auth.signOut();
        console.log("User signed out successfully");
      } catch (error) {
        console.error("Error signing out:", error);
        alert("Failed to sign out. Please try again.");
      }
    });
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

  // ─── Profile Bar Functions ──────────────────────────────────────────────────
  // Function to update profile generated count from challenges count
  function updateProfileGeneratedCount() {
    const challengesCountEl = document.getElementById('challenges-count');
    const profileGeneratedCountEl = document.getElementById('profile-generated-count');
    
    if (challengesCountEl && profileGeneratedCountEl) {
      const challengesText = challengesCountEl.textContent;
      const challengesNumber = challengesText.split(' ')[0];
      profileGeneratedCountEl.textContent = challengesNumber;
    }
  }

  // Function to handle successful file upload and add to upload history
  function onUploadSuccess(filename) {
    const ul = document.getElementById('upload-log-list');
    if (ul) {
      const date = new Date().toLocaleDateString();
      ul.insertAdjacentHTML('beforeend',
        `<li>${date}: ${filename}</li>`);
    }
  }

  // ─── Firestore Data Loader Functions ────────────────────────────────────────
  async function loadFavoritesList() {
    console.log("loadFavoritesList called");
    console.log("favoritesList element:", favoritesList);
    console.log("noFavorites element:", noFavorites);
    console.log("currentUser:", currentUser);
    
    if (!favoritesList || !noFavorites || !currentUser) {
      console.log("Early return from loadFavoritesList - missing elements or user");
      return;
    }
    
    // Restore challenges from localStorage if not available
    if (!window.allChallenges || window.allChallenges.length === 0) {
      console.log("allChallenges is empty, attempting to restore from localStorage");
      const restoredChallenges = restoreChallengesFromStorage();
      if (restoredChallenges.length > 0) {
        console.log("Successfully restored challenges from localStorage:", restoredChallenges.length);
      } else {
        console.log("No challenges found in localStorage");
      }
    }
    
    favoritesList.innerHTML = "";
    noFavorites.classList.add("hidden");
    
    try {
      console.log("Querying Firestore for favorites...");
      let snap;
      try {
        // Try with orderBy first
        snap = await db.collection("users").doc(currentUser.uid)
                       .collection("favorites")
                       .orderBy("favoritedAt","desc").get();
      } catch (orderError) {
        console.log("OrderBy query failed, trying without orderBy:", orderError);
        // Fallback to query without orderBy
        snap = await db.collection("users").doc(currentUser.uid)
                       .collection("favorites")
                       .get();
      }
      
      console.log("Firestore query completed. Empty:", snap.empty, "Size:", snap.size);
      
      if (snap.empty) { 
        console.log("No favorites found, showing empty state");
        noFavorites.classList.remove("hidden"); 
        return; 
      }
      
      console.log("Processing", snap.size, "favorite documents");
      
      // Process each favorite and fetch challenge data
      for (const doc of snap.docs) {
        const data = doc.data();
        console.log("Favorite document data:", data);
        
        const { challengeId, favoritedAt } = data;
        
        if (!challengeId) {
          console.log("No challengeId found, skipping");
          continue;
        }
        
        // Handle date formatting first (outside try block to avoid scope issues)
        let dateString = "Unknown date";
        try {
          if (favoritedAt && favoritedAt.toDate) {
            dateString = new Date(favoritedAt.toDate()).toLocaleDateString();
          } else if (favoritedAt) {
            dateString = new Date(favoritedAt).toLocaleDateString();
          }
        } catch (dateError) {
          console.log("Date formatting error:", dateError);
          dateString = "Invalid date";
        }
        
        try {
          // First try to get challenge data from Firestore (stored when favorited)
          let challengeData = data.challengeData || null;
          
          // If no stored data, try to find in allChallenges array as fallback
          if (!challengeData && window.allChallenges && Array.isArray(window.allChallenges)) {
            challengeData = window.allChallenges.find(c => c.id === challengeId);
            console.log("Found challenge in allChallenges as fallback:", challengeData);
          }
          
          // If still no data, try localStorage as last resort
          if (!challengeData) {
            const restoredChallenges = restoreChallengesFromStorage();
            if (restoredChallenges.length > 0) {
              challengeData = restoredChallenges.find(c => c.id === challengeId);
              console.log("Found challenge in localStorage as fallback:", challengeData);
            }
          }
          
          console.log("Final challenge data for", challengeId, ":", challengeData);
          
          // Extract question text from challenge data
          let questionText = "Challenge not available";
          if (challengeData) {
            questionText = challengeData.question || 
                          challengeData.challengeText || 
                          challengeData.title || 
                          challengeData.description || 
                          challengeData.prompt || 
                          challengeData.text || 
                          challengeData.content ||
                          "Challenge data incomplete";
          } else {
            // If challenge not found anywhere, show the challengeId
            questionText = `Challenge: ${challengeId}`;
            console.log("Challenge not found anywhere, using challengeId");
          }
          
          console.log("Extracted question text:", questionText);
          
          // Create full challenge card (like in renderChallenges)
          if (challengeData) {
            const card = document.createElement("div");
            card.className = "challenge-item favorite-challenge-card";
            card.dataset.type = challengeData.type || "unknown";
            card.dataset.challengeId = challengeId;
            
            const typeColors = {
              "multiple-choice": "#007bff",
              multiple_choice: "#007bff",
              debugging: "#ff8c00",
              "fill-in-the-blank": "#8a2be2",
              fill_in_blank: "#8a2be2",
            };
            
            const borderColor = typeColors[challengeData.type] || "#00ff41";
            card.style.setProperty("--border-color", borderColor);
            
            const typeLabel = challengeData.type && challengeData.type.includes("multiple")
              ? "Multiple Choice"
              : challengeData.type === "debugging"
              ? "Debugging"
              : challengeData.type === "fill_in_blank" || challengeData.type === "fill-in-the-blank"
              ? "Fill in the Blank"
              : "Challenge";
            
            const aiIcon = challengeData.ai_generated
              ? `<span class="ai-icon" title="AI-generated"><i class="fas fa-star"></i></span>`
              : "";
            
            // Build options HTML for multiple choice
            let optionsHTML = "";
            if (challengeData.type && challengeData.type.includes("multiple") && challengeData.options) {
              optionsHTML = `
                <div class="challenge-options">
                  ${challengeData.options.map((option, idx) => `
                    <label class="option-label">
                      <input type="radio" name="answer-${challengeId}" value="${option}" />
                      <span class="option-text">${option}</span>
                    </label>
                  `).join('')}
                </div>`;
            }
            
            card.innerHTML = `
              <div class="challenge-header">
                <span class="challenge-type">${typeLabel}</span>
                <h3>${challengeData.topic || 'Programming Challenge'}</h3>
                <span class="challenge-difficulty ${challengeData.difficulty || 'medium'}">
                  ${challengeData.difficulty ? challengeData.difficulty.charAt(0).toUpperCase() + challengeData.difficulty.slice(1) : 'Medium'}
                </span>
                ${aiIcon}
                <div class="favorite-date-badge">Favorited: ${dateString}</div>
              </div>
              <div class="challenge-question">
                <p>${questionText}</p>
                ${optionsHTML}
              </div>
              <div class="challenge-actions">
                <button class="btn btn-secondary hint-btn" data-challenge-id="${challengeId}">
                  <i class="fas fa-lightbulb"></i> Show Hint
                </button>
                <button class="btn btn-primary solve-btn" data-challenge-id="${challengeId}">
                  <i class="fas fa-play"></i> Solve Challenge
                </button>
                <button class="btn btn-warning unfavorite-btn favorited" data-challenge-id="${challengeId}" title="Remove from favorites">
                  <i class="fas fa-star"></i> Remove
                </button>
              </div>
            `;
            
            // Add event listeners for the buttons
            const hintBtn = card.querySelector('.hint-btn');
            const solveBtn = card.querySelector('.solve-btn');
            const unfavoriteBtn = card.querySelector('.unfavorite-btn');
            
            // Hint button functionality
            hintBtn.addEventListener('click', () => {
              if (challengeData.hint) {
                alert(`Hint: ${challengeData.hint}`);
              } else {
                alert("No hint available for this challenge.");
              }
            });
            
            // Solve button functionality
            solveBtn.addEventListener('click', () => {
              console.log("Solve button clicked for challenge:", challengeId);
              // Open challenge modal or navigate to solve view
              if (typeof openChallengeModal === 'function') {
                // Find the challenge index in allChallenges for modal
                const challengeIndex = window.allChallenges ? window.allChallenges.findIndex(c => c.id === challengeId) : -1;
                if (challengeIndex !== -1) {
                  const state = challengeStates[challengeIndex] || { attempts: 0, solved: false };
                  openChallengeModal(challengeIndex, challengeData, state);
                } else {
                  alert("Challenge modal not available. Please regenerate challenges.");
                }
              } else {
                alert("Challenge solving interface not available. Please upload a document first.");
              }
            });
            
            // Unfavorite button functionality
            unfavoriteBtn.addEventListener('click', async (e) => {
              e.stopPropagation();
              await toggleFavorite(challengeId, unfavoriteBtn);
              // Remove the card from favorites list after unfavoriting
              card.remove();
              
              // Check if no favorites left
              if (favoritesList.children.length === 0) {
                noFavorites.classList.remove("hidden");
              }
            });
            
            favoritesList.appendChild(card);
            console.log("Added full challenge card to DOM for:", challengeId);
            
          } else {
            // Fallback: create simple card if no challenge data
            const card = document.createElement("div");
            card.className = "favorite-item";
            card.innerHTML = `
              <div class="favorite-content">
                <div class="challenge-preview">Challenge: ${challengeId}</div>
                <div class="favorite-meta">
                  <span class="favorite-date">${dateString}</span>
                  <button class="favorite-star-btn favorited" data-challenge-id="${challengeId}" title="Remove from favorites">
                    <i class="fas fa-star"></i>
                  </button>
                </div>
              </div>`;
            
            // Add star button click handler for fallback case
            const starBtn = card.querySelector('.favorite-star-btn');
            starBtn.addEventListener('click', async (e) => {
              e.stopPropagation();
              await toggleFavorite(challengeId, starBtn);
              card.remove();
              if (favoritesList.children.length === 0) {
                noFavorites.classList.remove("hidden");
              }
            });
            
            favoritesList.appendChild(card);
          }
          
        } catch (challengeError) {
          console.error("Error processing challenge for", challengeId, ":", challengeError);
          
          // Still create a card but with limited info
          const card = document.createElement("div");
          card.className = "favorite-item";
          card.innerHTML = `
            <div class="favorite-content">
              <div class="challenge-preview">Challenge: ${challengeId}</div>
              <div class="favorite-meta">
                <span class="favorite-date">${dateString}</span>
                <button class="favorite-star-btn favorited" data-challenge-id="${challengeId}" title="Remove from favorites">
                  <i class="fas fa-star"></i>
                </button>
              </div>
            </div>`;
          
          // Add star button click handler for error case too
          const starBtn = card.querySelector('.favorite-star-btn');
          starBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            await toggleFavorite(challengeId, starBtn);
            card.remove();
            if (favoritesList.children.length === 0) {
              noFavorites.classList.remove("hidden");
            }
          });
          
          favoritesList.appendChild(card);
        }
      }
      
      console.log("Finished processing all favorites");
    } catch (error) {
      console.error("Error loading favorites:", error);
      noFavorites.classList.remove("hidden");
    }
  }

  // Function to load a specific challenge for solving again
  function loadSpecificChallenge(challengeData) {
    console.log("Loading specific challenge:", challengeData);
    // This would integrate with your existing challenge display system
    // You might need to adapt this based on how challenges are currently rendered
    if (typeof renderChallenges === 'function') {
      renderChallenges([challengeData]);
    }
  }

  // Make function globally accessible for debugging
  window.loadFavoritesList = loadFavoritesList;

  async function loadUploadHistory() {
    if (!uploadHistoryEl || !currentUser) return;
    
    uploadHistoryEl.innerHTML = "";
    
    try {
      const snap = await db.collection("users").doc(currentUser.uid)
                         .collection("uploads")
                         .orderBy("uploadedAt","desc").get();
      
      if (snap.empty) {
        uploadHistoryEl.innerHTML = `<li class="empty-state">No uploads yet</li>`;
        return;
      }
      
      snap.forEach(doc => {
        const { filename, downloadURL, uploadedAt } = doc.data();
        const li = document.createElement("li");
        li.innerHTML = `
          <a href="${downloadURL}" target="_blank">${filename}</a>
          <span class="upload-date">
            ${new Date(uploadedAt.toDate()).toLocaleString()}
          </span>`;
        uploadHistoryEl.appendChild(li);
      });
    } catch (error) {
      console.error("Error loading upload history:", error);
      uploadHistoryEl.innerHTML = `<li class="empty-state">Error loading uploads</li>`;
    }
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




