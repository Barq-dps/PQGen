// PQGen - Programming Challenge Generator JavaScript
// Enhanced with theme switching and improved functionality

// Global variables
let currentDocumentId = null;
let currentChallenges = [];
let currentChallengeIndex = 0;
let selectedTopics = [];
let currentTheme = 'dark';

// DOM elements
const elements = {
    // Theme toggle
    themeToggle: null,
    
    // Sections
    uploadSection: null,
    enhancedLoading: null,
    topicSection: null,
    generationProgress: null,
    challengesSection: null,
    errorSection: null,
    
    // Upload elements
    fileInput: null,
    uploadArea: null,
    uploadPrompt: null,
    fileSelected: null,
    fileName: null,
    fileStatus: null,
    processBtn: null,
    
    // Progress elements
    loadingMessage: null,
    loadingProgressFill: null,
    loadingProgressText: null,
    
    // Generation progress elements
    generationMessage: null,
    generationProgressFill: null,
    generationProgressText: null,
    generationDetails: null,
    
    // Topic elements
    topicsList: null,
    difficultySelect: null,
    selectAllBtn: null,
    clearBtn: null,
    generateBtn: null,
    
    // Challenge elements
    challengesList: null,
    challengesCount: null,
    challengesSolved: null,
    
    // Modal elements
    challengeModal: null,
    modalTitle: null,
    modalBody: null,
    modalClose: null,
    modalHint: null,
    modalSubmit: null,
    
    // Error elements
    errorMessage: null
};

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing PQGen...');
    initializeElements();
    initializeTheme();
    initializeEventListeners();
    initializeFileUpload();
    console.log('PQGen initialized successfully');
});

// Initialize DOM elements
function initializeElements() {
    // Theme toggle
    elements.themeToggle = document.getElementById('theme-toggle');
    
    // Sections
    elements.uploadSection = document.getElementById('upload-section');
    elements.enhancedLoading = document.getElementById('enhanced-loading');
    elements.topicSection = document.getElementById('topic-section');
    elements.generationProgress = document.getElementById('generation-progress');
    elements.challengesSection = document.getElementById('challenges-section');
    elements.errorSection = document.getElementById('error-section');
    
    // Upload elements
    elements.fileInput = document.getElementById('file-input');
    elements.uploadArea = document.getElementById('upload-area');
    elements.uploadPrompt = document.getElementById('upload-prompt');
    elements.fileSelected = document.getElementById('file-selected');
    elements.fileName = document.getElementById('file-name');
    elements.fileStatus = document.getElementById('file-status');
    elements.processBtn = document.getElementById('process-btn');
    
    // Progress elements
    elements.loadingMessage = document.getElementById('loading-message');
    elements.loadingProgressFill = document.getElementById('loading-progress-fill');
    elements.loadingProgressText = document.getElementById('loading-progress-text');
    
    // Generation progress elements
    elements.generationMessage = document.getElementById('generation-message');
    elements.generationProgressFill = document.getElementById('generation-progress-fill');
    elements.generationProgressText = document.getElementById('generation-progress-text');
    elements.generationDetails = document.getElementById('generation-details');
    
    // Topic elements
    elements.topicsList = document.getElementById('topics-list');
    elements.difficultySelect = document.getElementById('difficulty-select');
    elements.selectAllBtn = document.getElementById('select-all-topics');
    elements.clearBtn = document.getElementById('clear-topics');
    elements.generateBtn = document.getElementById('generate-challenges');
    
    // Challenge elements
    elements.challengesList = document.getElementById('challenges-list');
    elements.challengesCount = document.getElementById('challenges-count');
    elements.challengesSolved = document.getElementById('challenges-solved');
    
    // Modal elements
    elements.challengeModal = document.getElementById('challenge-modal');
    elements.modalTitle = document.getElementById('modal-title');
    elements.modalBody = document.getElementById('modal-body');
    elements.modalClose = document.getElementById('modal-close');
    elements.modalHint = document.getElementById('modal-hint');
    elements.modalSubmit = document.getElementById('modal-submit');
    
    // Error elements
    elements.errorMessage = document.getElementById('error-message');
    
    console.log('Elements initialized:', elements);
}

// Initialize theme system
function initializeTheme() {
    // Get saved theme or default to dark
    const savedTheme = localStorage.getItem('pqgen-theme') || 'dark';
    currentTheme = savedTheme;
    
    // Apply theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Update theme toggle icon
    updateThemeToggleIcon();
    
    console.log('Theme initialized:', currentTheme);
}

// Update theme toggle icon
function updateThemeToggleIcon() {
    if (elements.themeToggle) {
        const icon = elements.themeToggle.querySelector('i');
        if (icon) {
            icon.className = currentTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        }
    }
}

// Toggle theme
function toggleTheme() {
    currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    // Apply theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    
    // Save theme
    localStorage.setItem('pqgen-theme', currentTheme);
    
    // Update icon
    updateThemeToggleIcon();
    
    console.log('Theme toggled to:', currentTheme);
}

// Initialize event listeners
function initializeEventListeners() {
    // Theme toggle
    if (elements.themeToggle) {
        elements.themeToggle.addEventListener('click', toggleTheme);
    }
    
    // File input
    if (elements.fileInput) {
        elements.fileInput.addEventListener('change', handleFileSelect);
    }
    
    // Upload area drag and drop
    if (elements.uploadArea) {
        elements.uploadArea.addEventListener('dragover', handleDragOver);
        elements.uploadArea.addEventListener('dragleave', handleDragLeave);
        elements.uploadArea.addEventListener('drop', handleFileDrop);
        elements.uploadArea.addEventListener('click', () => elements.fileInput?.click());
    }
    
    // Topic selection buttons
    if (elements.selectAllBtn) {
        elements.selectAllBtn.addEventListener('click', selectAllTopics);
    }
    
    if (elements.clearBtn) {
        elements.clearBtn.addEventListener('click', clearAllTopics);
    }
    
    if (elements.generateBtn) {
        elements.generateBtn.addEventListener('click', handleChallengeGeneration);
    }
    
    // Modal close
    if (elements.modalClose) {
        elements.modalClose.addEventListener('click', closeModal);
    }
    
    if (elements.challengeModal) {
        elements.challengeModal.addEventListener('click', (e) => {
            if (e.target === elements.challengeModal) {
                closeModal();
            }
        });
    }
    
    // Escape key to close modal
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !elements.challengeModal?.classList.contains('hidden')) {
            closeModal();
        }
    });
    
    console.log('Event listeners initialized');
}

// Initialize file upload functionality
function initializeFileUpload() {
    // Show upload section by default
    showSection('upload-section');
}

// File handling functions
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        processFile(file);
    }
}

function handleDragOver(event) {
    event.preventDefault();
    elements.uploadArea?.classList.add('drag-over');
}

function handleDragLeave(event) {
    event.preventDefault();
    elements.uploadArea?.classList.remove('drag-over');
}

function handleFileDrop(event) {
    event.preventDefault();
    elements.uploadArea?.classList.remove('drag-over');
    
    const files = event.dataTransfer.files;
    if (files.length > 0) {
        const file = files[0];
        if (file.type === 'application/pdf') {
            processFile(file);
        } else {
            showError('Please select a PDF file.');
        }
    }
}

// Process uploaded file
async function processFile(file) {
    try {
        console.log('Processing file:', file.name);
        
        // Show file selected state
        showFileSelected(file.name);
        
        // Show loading section
        showSection('enhanced-loading');
        updateLoadingProgress(0, 'Uploading file...');
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload file
        updateLoadingProgress(25, 'Analyzing document...');
        const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!uploadResponse.ok) {
            throw new Error(`Upload failed: ${uploadResponse.statusText}`);
        }
        
        const uploadResult = await uploadResponse.json();
        currentDocumentId = uploadResult.document_id;
        
        console.log('File uploaded successfully:', uploadResult);
        
        // Extract topics
        updateLoadingProgress(50, 'Extracting topics...');
        const topicsResponse = await fetch(`/api/documents/${currentDocumentId}/topics`);
        
        if (!topicsResponse.ok) {
            throw new Error(`Topic extraction failed: ${topicsResponse.statusText}`);
        }
        
        const topicsResult = await topicsResponse.json();
        
        console.log('Topics extracted:', topicsResult);
        
        updateLoadingProgress(100, 'Complete!');
        
        // Show topic selection
        setTimeout(() => {
            showTopicSelection(topicsResult.topics);
        }, 1000);
        
    } catch (error) {
        console.error('Error processing file:', error);
        showError(`Failed to process file: ${error.message}`);
    }
}

// Show file selected state
function showFileSelected(fileName) {
    if (elements.fileName) {
        elements.fileName.textContent = fileName;
    }
    
    if (elements.uploadPrompt) {
        elements.uploadPrompt.classList.add('hidden');
    }
    
    if (elements.fileSelected) {
        elements.fileSelected.classList.remove('hidden');
    }
}

// Update loading progress
function updateLoadingProgress(percentage, message) {
    if (elements.loadingProgressFill) {
        elements.loadingProgressFill.style.width = `${percentage}%`;
    }
    
    if (elements.loadingProgressText) {
        elements.loadingProgressText.textContent = `${percentage}%`;
    }
    
    if (elements.loadingMessage && message) {
        elements.loadingMessage.textContent = message;
    }
}

// Show topic selection
function showTopicSelection(topics) {
    if (!elements.topicsList) return;
    
    // Clear existing topics
    elements.topicsList.innerHTML = '';
    
    // Add topics
    topics.forEach((topic, index) => {
        const topicItem = createTopicItem(topic, index);
        elements.topicsList.appendChild(topicItem);
    });
    
    // Show topic section
    showSection('topic-section');
    
    // Update generate button state
    updateGenerateButtonState();
}

// Create topic item
function createTopicItem(topic, index) {
    const div = document.createElement('div');
    div.className = 'topic-item';
    
    div.innerHTML = `
        <label class="topic-label">
            <input type="checkbox" class="topic-checkbox" data-topic="${topic}" data-index="${index}">
            <span class="topic-name">${topic}</span>
        </label>
        <select class="topic-difficulty" data-index="${index}">
            <option value="easy">Easy</option>
            <option value="medium" selected>Medium</option>
            <option value="hard">Hard</option>
        </select>
    `;
    
    // Add event listener for checkbox
    const checkbox = div.querySelector('.topic-checkbox');
    checkbox.addEventListener('change', updateGenerateButtonState);
    
    return div;
}

// Topic selection functions
function selectAllTopics() {
    const checkboxes = document.querySelectorAll('.topic-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = true;
    });
    updateGenerateButtonState();
}

function clearAllTopics() {
    const checkboxes = document.querySelectorAll('.topic-checkbox');
    checkboxes.forEach(checkbox => {
        checkbox.checked = false;
    });
    updateGenerateButtonState();
}

function updateGenerateButtonState() {
    const checkedBoxes = document.querySelectorAll('.topic-checkbox:checked');
    if (elements.generateBtn) {
        elements.generateBtn.disabled = checkedBoxes.length === 0;
    }
}

// Handle challenge generation
async function handleChallengeGeneration() {
    try {
        // Get selected topics
        const checkedBoxes = document.querySelectorAll('.topic-checkbox:checked');
        selectedTopics = Array.from(checkedBoxes).map(checkbox => ({
            topic: checkbox.dataset.topic,
            difficulty: document.querySelector(`[data-index="${checkbox.dataset.index}"]`).value
        }));
        
        console.log('Generating challenges for topics:', selectedTopics);
        
        // Show generation progress
        showSection('generation-progress');
        updateGenerationProgress(0, 'Starting challenge generation...');
        
        // Generate challenges
        const response = await fetch(`/api/documents/${currentDocumentId}/generate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                topics: selectedTopics.map(t => t.topic),
                difficulty: elements.difficultySelect?.value || 'medium'
            })
        });
        
        if (!response.ok) {
            throw new Error(`Challenge generation failed: ${response.statusText}`);
        }
        
        // Monitor progress
        await monitorGenerationProgress();
        
    } catch (error) {
        console.error('Error generating challenges:', error);
        showError(`Failed to generate challenges: ${error.message}`);
    }
}

// Monitor generation progress
async function monitorGenerationProgress() {
    const checkProgress = async () => {
        try {
            const response = await fetch(`/api/documents/${currentDocumentId}/progress`);
            
            if (!response.ok) {
                throw new Error('Failed to get progress');
            }
            
            const progress = await response.json();
            
            updateGenerationProgress(
                progress.percentage,
                progress.message,
                progress.details
            );
            
            if (progress.status === 'completed') {
                // Load challenges
                await loadChallenges();
            } else if (progress.status === 'error') {
                throw new Error(progress.error || 'Generation failed');
            } else {
                // Continue monitoring
                setTimeout(checkProgress, 1000);
            }
            
        } catch (error) {
            console.error('Error monitoring progress:', error);
            showError(`Generation failed: ${error.message}`);
        }
    };
    
    checkProgress();
}

// Update generation progress
function updateGenerationProgress(percentage, message, details) {
    if (elements.generationProgressFill) {
        elements.generationProgressFill.style.width = `${percentage}%`;
    }
    
    if (elements.generationProgressText) {
        elements.generationProgressText.textContent = `${percentage}%`;
    }
    
    if (elements.generationMessage && message) {
        elements.generationMessage.textContent = message;
    }
    
    if (elements.generationDetails && details) {
        elements.generationDetails.innerHTML = details.map(detail => 
            `<div class="detail-item">${detail}</div>`
        ).join('');
    }
}

// Load challenges
async function loadChallenges() {
    try {
        console.log('Loading challenges for document:', currentDocumentId);
        
        const response = await fetch(`/api/documents/${currentDocumentId}/challenges`);
        
        if (!response.ok) {
            throw new Error(`Failed to load challenges: ${response.statusText}`);
        }
        
        const result = await response.json();
        currentChallenges = result.challenges;
        
        console.log('Challenges loaded:', currentChallenges);
        
        // Display challenges
        displayChallenges(currentChallenges);
        
        // Show challenges section
        showSection('challenges-section');
        
    } catch (error) {
        console.error('Error loading challenges:', error);
        showError(`Failed to load challenges: ${error.message}`);
    }
}

// Display challenges
function displayChallenges(challenges) {
    if (!elements.challengesList) return;
    
    // Clear existing challenges
    elements.challengesList.innerHTML = '';
    
    // Update stats
    if (elements.challengesCount) {
        elements.challengesCount.textContent = `${challenges.length} challenges`;
    }
    
    // Add challenges
    challenges.forEach((challenge, index) => {
        const challengeCard = createChallengeCard(challenge, index);
        elements.challengesList.appendChild(challengeCard);
    });
    
    // Initialize filter buttons
    initializeFilterButtons();
}

// Create challenge card
function createChallengeCard(challenge, index) {
    const div = document.createElement('div');
    div.className = `challenge-card ${challenge.type}`;
    div.dataset.type = challenge.type;
    div.dataset.index = index;
    
    const typeIcon = getTypeIcon(challenge.type);
    const difficultyColor = getDifficultyColor(challenge.difficulty);
    
    div.innerHTML = `
        <div class="challenge-header">
            <div class="challenge-type">
                <i class="${typeIcon}"></i>
                ${challenge.type.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}
            </div>
            <div class="challenge-difficulty" style="color: ${difficultyColor}">
                ${challenge.difficulty}
            </div>
        </div>
        <h4 class="challenge-title">${challenge.topic}</h4>
        <p class="challenge-preview">${challenge.question.substring(0, 100)}...</p>
        <div class="challenge-footer">
            <button class="btn btn-primary btn-sm" onclick="openChallenge(${index})">
                Start Challenge
            </button>
        </div>
    `;
    
    return div;
}

// Get type icon
function getTypeIcon(type) {
    const icons = {
        'multiple-choice': 'fas fa-list-ul',
        'debugging': 'fas fa-bug',
        'fill-in-the-blank': 'fas fa-edit'
    };
    return icons[type] || 'fas fa-question';
}

// Get difficulty color
function getDifficultyColor(difficulty) {
    const colors = {
        'easy': '#28a745',
        'medium': '#ffc107',
        'hard': '#dc3545'
    };
    return colors[difficulty] || '#6c757d';
}

// Initialize filter buttons
function initializeFilterButtons() {
    const filterButtons = document.querySelectorAll('.filter-btn');
    
    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            // Update active state
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');
            
            // Filter challenges
            const filter = button.dataset.filter;
            filterChallenges(filter);
        });
    });
}

// Filter challenges
function filterChallenges(filter) {
    const challengeCards = document.querySelectorAll('.challenge-card');
    
    challengeCards.forEach(card => {
        if (filter === 'all' || card.dataset.type === filter) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

// Open challenge modal
function openChallenge(index) {
    const challenge = currentChallenges[index];
    if (!challenge) return;
    
    currentChallengeIndex = index;
    
    // Set modal content
    if (elements.modalTitle) {
        elements.modalTitle.textContent = challenge.topic;
    }
    
    if (elements.modalBody) {
        elements.modalBody.innerHTML = renderChallengeContent(challenge);
    }
    
    // Show modal
    if (elements.challengeModal) {
        elements.challengeModal.classList.remove('hidden');
    }
    
    // Focus on modal
    elements.challengeModal?.focus();
}

// Render challenge content
function renderChallengeContent(challenge) {
    switch (challenge.type) {
        case 'multiple-choice':
            return renderMultipleChoice(challenge);
        case 'debugging':
            return renderDebugging(challenge);
        case 'fill-in-the-blank':
            return renderFillInTheBlank(challenge);
        default:
            return `<p>${challenge.question}</p>`;
    }
}

// Render multiple choice challenge
function renderMultipleChoice(challenge) {
    const options = challenge.options.map((option, index) => 
        `<label class="option-label">
            <input type="radio" name="answer" value="${index}">
            <span>${option}</span>
        </label>`
    ).join('');
    
    return `
        <div class="challenge-content">
            <p class="challenge-question">${challenge.question}</p>
            <div class="challenge-options">
                ${options}
            </div>
        </div>
    `;
}

// Render debugging challenge
function renderDebugging(challenge) {
    return `
        <div class="challenge-content">
            <p class="challenge-question">${challenge.question}</p>
            <div class="code-container">
                <pre><code>${challenge.code_stub}</code></pre>
            </div>
            <textarea class="code-input" placeholder="Enter your corrected code here..." rows="10"></textarea>
        </div>
    `;
}

// Render fill in the blank challenge
function renderFillInTheBlank(challenge) {
    return `
        <div class="challenge-content">
            <p class="challenge-question">${challenge.question}</p>
            <div class="code-container">
                <pre><code>${challenge.code_stub}</code></pre>
            </div>
            <div class="blank-inputs">
                <!-- Blank inputs will be generated based on the code -->
            </div>
        </div>
    `;
}

// Close modal
function closeModal() {
    if (elements.challengeModal) {
        elements.challengeModal.classList.add('hidden');
    }
}

// Show section
function showSection(sectionId) {
    // Hide all sections
    const sections = ['upload-section', 'enhanced-loading', 'topic-section', 'generation-progress', 'challenges-section', 'error-section'];
    
    sections.forEach(id => {
        const section = document.getElementById(id);
        if (section) {
            section.classList.add('hidden');
        }
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.classList.remove('hidden');
        
        // Scroll to section
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    
    console.log('Showing section:', sectionId);
}

// Show error
function showError(message) {
    console.error('Error:', message);
    
    if (elements.errorMessage) {
        elements.errorMessage.textContent = message;
    }
    
    showSection('error-section');
}

// Utility functions
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for global access
window.openChallenge = openChallenge;
window.toggleTheme = toggleTheme;

console.log('PQGen JavaScript loaded successfully');

