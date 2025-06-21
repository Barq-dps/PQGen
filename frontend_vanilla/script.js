// PQGen Vanilla Frontend JavaScript

// Configuration
const API_BASE_URL = 'http://localhost:5000';

// State
let currentChallenges = [];
let currentDocumentId = null;
let currentTheme = localStorage.getItem('theme') || 'light';

// DOM Elements
const elements = {
    themeToggle: document.getElementById('theme-toggle'),
    fileInput: document.getElementById('file-input'),
    uploadZone: document.getElementById('upload-zone'),
    generateBtn: document.getElementById('generate-btn'),
    uploadStatus: document.getElementById('upload-status'),
    difficultySelect: document.getElementById('difficulty-select'),
    challengesGrid: document.getElementById('challenges-grid'),
    searchInput: document.getElementById('search-input'),
    challengeModal: document.getElementById('challenge-modal'),
    modalTitle: document.getElementById('modal-title'),
    modalContent: document.getElementById('modal-challenge-content'),
    submitAnswer: document.getElementById('submit-answer'),
    loadingOverlay: document.getElementById('loading-overlay')
};

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
    setupEventListeners();
    loadSampleChallenges();
});

// Theme Management
function initializeTheme() {
    document.documentElement.setAttribute('data-theme', currentTheme);
    elements.themeToggle.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    localStorage.setItem('theme', currentTheme);
    initializeTheme();
}

// Event Listeners
function setupEventListeners() {
    // Theme toggle
    elements.themeToggle.addEventListener('click', toggleTheme);
    
    // Navigation
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = this.getAttribute('href').substring(1);
            showSection(target);
            updateActiveNavLink(this);
        });
    });
    
    // File upload
    elements.uploadZone.addEventListener('click', () => elements.fileInput.click());
    elements.uploadZone.addEventListener('dragover', handleDragOver);
    elements.uploadZone.addEventListener('dragleave', handleDragLeave);
    elements.uploadZone.addEventListener('drop', handleDrop);
    elements.fileInput.addEventListener('change', handleFileSelect);
    
    // Generate button
    elements.generateBtn.addEventListener('click', generateChallenges);
    
    // Search and filters
    elements.searchInput.addEventListener('input', filterChallenges);
    document.querySelectorAll('.filter-checkboxes input').forEach(checkbox => {
        checkbox.addEventListener('change', filterChallenges);
    });
    
    // Modal close
    elements.challengeModal.addEventListener('click', function(e) {
        if (e.target === this) closeModal();
    });
}

// Navigation
function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => {
        section.classList.remove('active');
    });
    document.getElementById(sectionId).classList.add('active');
}

function updateActiveNavLink(activeLink) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    activeLink.classList.add('active');
}

// File Upload Handling
function handleDragOver(e) {
    e.preventDefault();
    elements.uploadZone.classList.add('dragover');
}

function handleDragLeave(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    elements.uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        handleFile(files[0]);
    } else {
        showStatus('Please select a valid PDF file.', 'error');
    }
}

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    if (file.type !== 'application/pdf') {
        showStatus('Please select a PDF file.', 'error');
        return;
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB limit
        showStatus('File size must be less than 10MB.', 'error');
        return;
    }
    
    elements.generateBtn.disabled = false;
    elements.generateBtn.textContent = `Generate Challenges from "${file.name}"`;
    showStatus(`Selected: ${file.name} (${formatFileSize(file.size)})`, 'success');
}

// Challenge Generation
async function generateChallenges() {
    const file = elements.fileInput.files[0];
    if (!file) {
        showStatus('Please select a PDF file first.', 'error');
        return;
    }
    
    const difficulty = elements.difficultySelect.value;
    
    try {
        showLoading(true);
        showStatus('Uploading document...', 'processing');
        
        // Upload document
        const uploadResponse = await uploadDocument(file, difficulty);
        currentDocumentId = uploadResponse.document_id;
        
        showStatus('Processing document...', 'processing');
        
        // Poll for completion
        const challenges = await waitForProcessing(currentDocumentId);
        
        currentChallenges = challenges;
        renderChallenges(challenges);
        
        showStatus(`Successfully generated ${challenges.length} challenges!`, 'success');
        
    } catch (error) {
        console.error('Error generating challenges:', error);
        showStatus(`Error: ${error.message}`, 'error');
    } finally {
        showLoading(false);
    }
}

// API Functions
async function uploadDocument(file, difficulty) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload?difficulty=${difficulty}`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
}

async function checkDocumentStatus(documentId) {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`);
    
    if (!response.ok) {
        throw new Error(`Status check failed: ${response.statusText}`);
    }
    
    return await response.json();
}

async function getChallenges(documentId) {
    const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/challenges`);
    
    if (!response.ok) {
        throw new Error(`Failed to get challenges: ${response.statusText}`);
    }
    
    return await response.json();
}

async function waitForProcessing(documentId) {
    const maxAttempts = 60; // 5 minutes max
    let attempts = 0;
    
    while (attempts < maxAttempts) {
        const status = await checkDocumentStatus(documentId);
        
        if (status.status === 'completed') {
            const challengesData = await getChallenges(documentId);
            return challengesData.challenges || [];
        } else if (status.status === 'error') {
            throw new Error(status.error || 'Processing failed');
        }
        
        // Wait 5 seconds before next check
        await new Promise(resolve => setTimeout(resolve, 5000));
        attempts++;
    }
    
    throw new Error('Processing timeout');
}

// Challenge Rendering
function renderChallenges(challenges) {
    if (!challenges || challenges.length === 0) {
        elements.challengesGrid.innerHTML = '<div class="no-challenges"><p>No challenges generated.</p></div>';
        return;
    }
    
    const challengesHTML = challenges.map(challenge => createChallengeCard(challenge)).join('');
    elements.challengesGrid.innerHTML = challengesHTML;
    
    // Add click listeners to challenge cards
    document.querySelectorAll('.challenge-card').forEach(card => {
        card.addEventListener('click', function() {
            const challengeId = this.dataset.challengeId;
            const challenge = challenges.find(c => c.id === challengeId);
            if (challenge) {
                openChallengeModal(challenge);
            }
        });
    });
}

function createChallengeCard(challenge) {
    const typeIcons = {
        'multiple-choice': '❓',
        'debugging': '🐛',
        'coding': '💻'
    };
    
    const typeLabels = {
        'multiple-choice': 'Multiple Choice',
        'debugging': 'Debugging',
        'coding': 'Coding'
    };
    
    return `
        <div class="challenge-card" data-challenge-id="${challenge.id}">
            <div class="challenge-header">
                <div class="challenge-type">
                    <span>${typeIcons[challenge.type] || '📝'}</span>
                    <span>${typeLabels[challenge.type] || challenge.type}</span>
                </div>
                <div class="challenge-difficulty difficulty-${challenge.difficulty}">
                    ${challenge.difficulty}
                </div>
            </div>
            <h3 class="challenge-title">${challenge.topic || challenge.title || 'Programming Challenge'}</h3>
            <p class="challenge-description">${truncateText(challenge.question || challenge.description || 'Click to view challenge details.', 120)}</p>
            <div class="challenge-footer">
                <button class="start-button" onclick="event.stopPropagation(); openChallengeModal(currentChallenges.find(c => c.id === '${challenge.id}'))">
                    Start Challenge
                </button>
            </div>
        </div>
    `;
}

// Challenge Modal
function openChallengeModal(challenge) {
    elements.modalTitle.textContent = challenge.topic || challenge.title || 'Programming Challenge';
    elements.modalContent.innerHTML = createChallengeContent(challenge);
    elements.challengeModal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    elements.challengeModal.classList.add('hidden');
    document.body.style.overflow = 'auto';
}

function createChallengeContent(challenge) {
    switch (challenge.type) {
        case 'multiple-choice':
            return createMultipleChoiceContent(challenge);
        case 'debugging':
            return createDebuggingContent(challenge);
        case 'coding':
            return createCodingContent(challenge);
        default:
            return `<p>${challenge.question || 'Challenge content not available.'}</p>`;
    }
}

function createMultipleChoiceContent(challenge) {
    const options = challenge.options || ['Option A', 'Option B', 'Option C', 'Option D'];
    const optionsHTML = options.map((option, index) => 
        `<label class="option-label">
            <input type="radio" name="mcq-option" value="${index}">
            <span>${option}</span>
        </label>`
    ).join('');
    
    return `
        <div class="challenge-question">
            <p><strong>Question:</strong></p>
            <p>${challenge.question}</p>
        </div>
        <div class="challenge-options">
            <p><strong>Choose the correct answer:</strong></p>
            <div class="options-list">
                ${optionsHTML}
            </div>
        </div>
        <style>
            .challenge-question { margin-bottom: 1.5rem; }
            .options-list { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem; }
            .option-label { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem; border: 1px solid var(--border-color); border-radius: var(--radius-md); cursor: pointer; transition: all 0.2s; }
            .option-label:hover { background-color: var(--surface-color); border-color: var(--primary-color); }
            .option-label input[type="radio"] { margin: 0; }
        </style>
    `;
}

function createDebuggingContent(challenge) {
    return `
        <div class="challenge-question">
            <p><strong>Debug the following code:</strong></p>
            <p>${challenge.question}</p>
        </div>
        <div class="challenge-code">
            <pre><code>${challenge.buggy_code || challenge.code_stub || 'Code not available'}</code></pre>
        </div>
        <div class="challenge-answer">
            <label for="debug-answer"><strong>Describe the bug and provide the fix:</strong></label>
            <textarea id="debug-answer" rows="6" placeholder="Explain what's wrong with the code and how to fix it..."></textarea>
        </div>
        <style>
            .challenge-code { margin: 1.5rem 0; }
            .challenge-code pre { background-color: var(--surface-color); padding: 1rem; border-radius: var(--radius-md); overflow-x: auto; }
            .challenge-answer textarea { width: 100%; margin-top: 0.5rem; resize: vertical; }
        </style>
    `;
}

function createCodingContent(challenge) {
    return `
        <div class="challenge-question">
            <p><strong>Problem:</strong></p>
            <p>${challenge.question}</p>
        </div>
        <div class="challenge-code">
            <label for="code-editor"><strong>Write your solution:</strong></label>
            <textarea id="code-editor" rows="12" placeholder="Write your code here...">${challenge.code_stub || ''}</textarea>
        </div>
        <style>
            .challenge-code { margin-top: 1.5rem; }
            .challenge-code textarea { width: 100%; margin-top: 0.5rem; font-family: 'Courier New', monospace; resize: vertical; }
        </style>
    `;
}

// Filtering and Search
function filterChallenges() {
    const searchTerm = elements.searchInput.value.toLowerCase();
    const selectedTypes = Array.from(document.querySelectorAll('.filter-checkboxes input:checked')).map(cb => cb.value);
    
    const filteredChallenges = currentChallenges.filter(challenge => {
        const matchesSearch = !searchTerm || 
            (challenge.topic && challenge.topic.toLowerCase().includes(searchTerm)) ||
            (challenge.question && challenge.question.toLowerCase().includes(searchTerm));
        
        const matchesType = selectedTypes.length === 0 || selectedTypes.includes(challenge.type);
        
        return matchesSearch && matchesType;
    });
    
    renderChallenges(filteredChallenges);
}

// Sample Challenges (fallback)
function loadSampleChallenges() {
    const sampleChallenges = [
        {
            id: 'sample-1',
            type: 'multiple-choice',
            difficulty: 'easy',
            topic: 'JavaScript Basics',
            question: 'What is the correct way to declare a variable in JavaScript?',
            options: ['var x = 5;', 'variable x = 5;', 'v x = 5;', 'declare x = 5;'],
            correct_index: 0
        },
        {
            id: 'sample-2',
            type: 'debugging',
            difficulty: 'medium',
            topic: 'Array Methods',
            question: 'Find and fix the bug in this array sorting function.',
            buggy_code: `function sortNumbers(arr) {
    return arr.sort();
}

console.log(sortNumbers([10, 5, 40, 25, 1000, 1]));
// Expected: [1, 5, 10, 25, 40, 1000]
// Actual: [1, 10, 1000, 25, 40, 5]`
        },
        {
            id: 'sample-3',
            type: 'coding',
            difficulty: 'hard',
            topic: 'Algorithm Design',
            question: 'Implement a function that finds the longest palindromic substring in a given string.',
            code_stub: `function longestPalindrome(s) {
    // Your code here
    
}`
        }
    ];
    
    currentChallenges = sampleChallenges;
    renderChallenges(sampleChallenges);
}

// Utility Functions
function showStatus(message, type) {
    elements.uploadStatus.textContent = message;
    elements.uploadStatus.className = `upload-status ${type}`;
    elements.uploadStatus.classList.remove('hidden');
    
    if (type === 'success') {
        setTimeout(() => {
            elements.uploadStatus.classList.add('hidden');
        }, 5000);
    }
}

function showLoading(show) {
    if (show) {
        elements.loadingOverlay.classList.remove('hidden');
    } else {
        elements.loadingOverlay.classList.add('hidden');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function truncateText(text, maxLength) {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

// Global functions for inline event handlers
window.showSection = showSection;
window.openChallengeModal = openChallengeModal;
window.closeModal = closeModal;

