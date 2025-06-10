// Frontend JavaScript for Programming Challenge Generator

document.addEventListener("DOMContentLoaded", () => {
    // --- Get DOM Elements based on your index.html ---
    const uploadSection = document.getElementById("upload-section");
    const uploadForm = document.getElementById("upload-form");
    const pdfFile = document.getElementById("pdf-file");
    const generateBtn = document.getElementById("generate-btn");
    const uploadStatus = document.getElementById("upload-status");

    const challengesSection = document.getElementById("challenges-section");
    const topicsList = document.getElementById("topics-list");
    const challengesListContainer = document.getElementById("challenges-list");

    const challengeDetailSection = document.getElementById("challenge-detail-section");
    const backToChallengesButton = document.getElementById("back-to-challenges");
    const challengeTitle = document.getElementById("challenge-title");
    const challengeDescription = document.getElementById("challenge-description");
    const challengeDifficulty = document.getElementById("challenge-difficulty");

    const mcqArea = document.getElementById("mcq-area");
    const mcqOptionsContainer = document.getElementById("mcq-options-container");
    const hintButton = document.getElementById("hint-button");

    const debuggingArea = document.getElementById("debugging-area");
    const buggyCodeDisplay = document.getElementById("buggy-code-display");
    const codeEditor = document.getElementById("code-editor");
    const submitCodeDebugButton = document.getElementById("submit-code-debug");
    const revealSolutionButton = document.getElementById("reveal-solution-button");

    const generalCodingArea = document.getElementById("general-coding-area");
    const generalCodeEditor = document.getElementById("general-code-editor");
    const submitCodeGeneralButton = document.getElementById("submit-code-general");

    const evaluationResultArea = document.getElementById("evaluation-result");
    const resultStatus = document.getElementById("result-status");
    const resultMessage = document.getElementById("result-message");
    const resultExplanation = document.getElementById("result-explanation");
    const correctSolutionContainer = document.getElementById("correct-solution-container");
    const correctCodeDisplay = document.getElementById("correct-code-display");
    const correctCodeExplanation = document.getElementById("correct-code-explanation");

    let allFetchedChallenges = [];
    let currentChallenge = null;
    let actualHintForCurrentDebugChallenge = null;
    let hintUsedForMcq = false;
    let pollingInterval = null;

    const API_BASE_URL = "http://localhost:5000";
    const POLLING_INTERVAL_MS = 2000; // Poll every 2 seconds

    showSection("upload");

    // Make handlePdfUpload available globally for the fallback script
    window.handlePdfUpload = handlePdfUpload;

    // Use button click instead of form submit to avoid refresh issues
    if (generateBtn) {
        generateBtn.addEventListener("click", function() {
            try {
                console.log("Generate button clicked");
                handlePdfUpload({preventDefault: function(){}});
            } catch (error) {
                console.error("Error in generate button handler:", error);
                if(uploadStatus) {
                    uploadStatus.textContent = `Error: ${error.message}`;
                    uploadStatus.style.display = 'block';
                }
            }
        });
    } else {
        console.error("Generate button not found!");
        if(uploadStatus) uploadStatus.textContent = "Error: Generate button element missing in HTML.";
    }

    if (backToChallengesButton) {
        backToChallengesButton.addEventListener("click", () => {
            showSection("challenges");
        });
    }

    if (submitCodeDebugButton) {
        submitCodeDebugButton.addEventListener("click", () => handleSubmitCode("debug"));
    }

    if (submitCodeGeneralButton) {
        submitCodeGeneralButton.addEventListener("click", () => handleSubmitCode("general"));
    }

    if (hintButton) {
        hintButton.addEventListener("click", handleHint);
    }
    
    if (revealSolutionButton) {
        revealSolutionButton.addEventListener("click", handleRevealSolution);
    }

    function showSection(sectionName) {
        if(uploadSection) uploadSection.classList.add("hidden");
        if(challengesSection) challengesSection.classList.add("hidden");
        if(challengeDetailSection) challengeDetailSection.classList.add("hidden");

        if (sectionName === "upload" && uploadSection) {
            uploadSection.classList.remove("hidden");
        } else if (sectionName === "challenges" && challengesSection) {
            challengesSection.classList.remove("hidden");
        } else if (sectionName === "detail" && challengeDetailSection) {
            challengeDetailSection.classList.remove("hidden");
        }
    }

    function handlePdfUpload(event) {
        try {
            // Prevent default form submission (even though we're using a button now)
            if (event && event.preventDefault) {
                event.preventDefault();
            }
            
            console.log("handlePdfUpload triggered"); // For debugging

            if (!pdfFile || !pdfFile.files || !pdfFile.files.length) {
                if(uploadStatus) {
                    uploadStatus.textContent = "Please select a PDF file.";
                    uploadStatus.style.display = 'block';
                }
                return;
            }

            const formData = new FormData();
            formData.append("file", pdfFile.files[0]);

            if(uploadStatus) {
                uploadStatus.innerHTML = '<div class="spinner"></div> Processing PDF and generating challenges... This may take a few minutes.';
                uploadStatus.style.display = 'block'; // Ensure it's visible
                console.log("Upload status set to processing..."); // For debugging
            }

            // Clear previous challenge displays immediately
            if(challengesListContainer) challengesListContainer.innerHTML = "";
            if(topicsList) topicsList.innerHTML = "";
            if(challengeDetailSection) challengeDetailSection.classList.add("hidden");

            // Clear any existing polling interval
            if (pollingInterval) {
                clearInterval(pollingInterval);
                pollingInterval = null;
            }

            // Use fetch with proper error handling
            fetch(`${API_BASE_URL}/api/upload`, {
                method: "POST",
                body: formData,
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || `HTTP error! status: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(result => {
                if (result.document_id) {
                    // Start polling for document processing status
                    pollDocumentStatus(result.document_id);
                } else {
                    if(uploadStatus) uploadStatus.textContent = "Error: No document ID returned from server.";
                }
            })
            .catch(error => {
                console.error("Error uploading PDF:", error);
                if(uploadStatus) {
                    uploadStatus.textContent = `Error: ${error.message}`;
                    uploadStatus.style.display = 'block';
                }
            });
            
            console.log("handlePdfUpload fetch initiated."); // For debugging
        } catch (error) {
            console.error("Critical error in handlePdfUpload:", error);
            if(uploadStatus) {
                uploadStatus.textContent = `Critical error: ${error.message}`;
                uploadStatus.style.display = 'block';
            }
        }
    }

    async function pollDocumentStatus(documentId) {
        console.log(`Starting to poll status for document: ${documentId}`);
        
        // Clear any existing polling interval
        if (pollingInterval) {
            clearInterval(pollingInterval);
        }
        
        // Function to check document status
        const checkStatus = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/status`);
                const result = await response.json();
                
                if (!response.ok) {
                    throw new Error(result.error || `HTTP error! status: ${response.status}`);
                }
                
                console.log(`Document status: ${result.status}`);
                
                if (result.status === "completed") {
                    // Stop polling once processing is complete
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    // Update status message
                    if(uploadStatus) {
                        uploadStatus.textContent = `PDF processing complete. Fetching challenges...`;
                    }
                    
                    // Fetch challenges
                    await fetchAndDisplayChallengeList(documentId);
                } else if (result.status === "error") {
                    // Stop polling on error
                    clearInterval(pollingInterval);
                    pollingInterval = null;
                    
                    if(uploadStatus) uploadStatus.textContent = `Error processing PDF: ${result.error || "Unknown error"}`;
                } else {
                    // Still processing, update status message
                    if(uploadStatus) {
                        uploadStatus.innerHTML = '<div class="spinner"></div> Still processing PDF... This may take a few minutes.';
                    }
                }
            } catch (error) {
                console.error("Error checking document status:", error);
                if(uploadStatus) uploadStatus.textContent = `Error checking status: ${error.message}`;
                
                // Stop polling on error
                clearInterval(pollingInterval);
                pollingInterval = null;
            }
        };
        
        // Check status immediately
        await checkStatus();
        
        // Then check periodically
        pollingInterval = setInterval(checkStatus, POLLING_INTERVAL_MS);
    }

    async function fetchAndDisplayChallengeList(documentId) {
        try {
            console.log(`Fetching challenges for document: ${documentId}`);
            const response = await fetch(`${API_BASE_URL}/api/documents/${documentId}/challenges`);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }
            
            allFetchedChallenges = result.challenges || [];
            const topics = result.topics || [];
            
            console.log(`Fetched ${allFetchedChallenges.length} challenges for ${topics.length} topics`);

            if(uploadStatus) {
                uploadStatus.textContent = `Found ${allFetchedChallenges.length} challenges across ${topics.length} topics.`;
                setTimeout(() => {
                    if(uploadStatus) uploadStatus.style.display = 'none';
                }, 3000);
            }

            if(topicsList) {
                topicsList.innerHTML = "";
                if (topics && topics.length > 0) {
                    topics.forEach(topic => {
                        const li = document.createElement("li");
                        li.textContent = topic;
                        topicsList.appendChild(li);
                    });
                } else {
                    topicsList.innerHTML = "<li>No topics extracted.</li>";
                }
            }

            if(challengesListContainer) {
                challengesListContainer.innerHTML = "";
                if (allFetchedChallenges && allFetchedChallenges.length > 0) {
                    allFetchedChallenges.forEach((challenge, index) => {
                        const challengeItem = document.createElement("div");
                        challengeItem.classList.add("challenge-list-item");
                        
                        // Use question if available, otherwise fall back to question_text
                        const questionText = challenge.question || challenge.question_text || "No question text";
                        
                        // Get difficulty and capitalize first letter
                        const difficulty = challenge.difficulty || "medium";
                        const displayDifficulty = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
                        
                        // Add difficulty badge with appropriate color
                        const difficultyClass = `difficulty-${difficulty.toLowerCase()}`;
                        
                        challengeItem.innerHTML = `
                            <h4>${escapeHtml(challenge.topic || "Challenge")} #${index + 1}</h4>
                            <p>${escapeHtml(questionText.substring(0, 100))}...</p>
                            <div class="challenge-meta">
                                <span class="difficulty-badge ${difficultyClass}">${displayDifficulty}</span>
                                <span class="challenge-type">${challenge.type || "Unknown"}</span>
                            </div>
                            <button class="btn view-challenge-btn" data-index="${index}">View Challenge</button>
                        `;
                        challengesListContainer.appendChild(challengeItem);
                    });

                    document.querySelectorAll(".view-challenge-btn").forEach(button => {
                        button.addEventListener("click", (e) => {
                            const challengeIndex = parseInt(e.target.dataset.index);
                            displayChallengeDetail(allFetchedChallenges[challengeIndex]);
                        });
                    });
                } else {
                    challengesListContainer.innerHTML = "<p>No challenges found for this document.</p>";
                }
            }
            showSection("challenges");
        } catch (error) {
            console.error("Error fetching challenges:", error);
            if(uploadStatus) uploadStatus.textContent = `Error: ${error.message}`;
            if(challengesListContainer) challengesListContainer.innerHTML = "<p>Failed to fetch challenges.</p>";
            showSection("challenges");
        }
    }

    function displayChallengeDetail(challenge) {
        currentChallenge = challenge;
        if (!currentChallenge) {
            console.error("No challenge data to display");
            return;
        }

        console.log("Displaying challenge:", currentChallenge);

        hintUsedForMcq = false;
        actualHintForCurrentDebugChallenge = null;
        if(evaluationResultArea) evaluationResultArea.classList.add("hidden");
        if(correctSolutionContainer) correctSolutionContainer.classList.add("hidden");

        if(challengeTitle) challengeTitle.textContent = escapeHtml(currentChallenge.topic || "Challenge Details");
        
        // Use question if available, otherwise fall back to question_text
        const questionText = currentChallenge.question || currentChallenge.question_text || "No question text";
        if(challengeDescription) challengeDescription.innerHTML = `<p>${escapeHtml(questionText)}</p>`;
        
        // Display difficulty if available
        if(challengeDifficulty) {
            const difficulty = currentChallenge.difficulty || "medium";
            const displayDifficulty = difficulty.charAt(0).toUpperCase() + difficulty.slice(1);
            const difficultyClass = `difficulty-${difficulty.toLowerCase()}`;
            
            challengeDifficulty.innerHTML = `<span class="difficulty-badge ${difficultyClass}">${displayDifficulty}</span>`;
            challengeDifficulty.classList.remove("hidden");
        }

        let type = "coding";
        if (currentChallenge.options && currentChallenge.options.length > 0) type = "mcq";
        else if (currentChallenge.code_stub && questionText.toLowerCase().includes("bug")) type = "debug";
        else if (currentChallenge.code_stub || currentChallenge.function_template) type = "coding";
        
        currentChallenge.type = type;

        if(mcqArea) mcqArea.classList.add("hidden");
        if(debuggingArea) debuggingArea.classList.add("hidden");
        if(generalCodingArea) generalCodingArea.classList.add("hidden");
        if(hintButton) hintButton.style.display = "none";

        if (type === "mcq" && mcqArea && mcqOptionsContainer) {
            mcqArea.classList.remove("hidden");
            mcqOptionsContainer.innerHTML = "";
            
            // Handle both array of objects and array of strings for options
            const options = currentChallenge.options || [];
            options.forEach((option, index) => {
                const button = document.createElement("button");
                button.classList.add("btn", "option-btn");
                button.dataset.index = index;
                
                // Handle both {text: "option"} and "option" formats
                const optionText = typeof option === 'object' ? (option.text || '') : option;
                button.textContent = escapeHtml(optionText);
                
                button.addEventListener("click", handleMcOptionClick);
                mcqOptionsContainer.appendChild(button);
            });
            
            if (hintButton && (currentChallenge.hint || currentChallenge.options.length > 2)) {
                 hintButton.style.display = "inline-block";
            }
        } else if (type === "debug" && debuggingArea && buggyCodeDisplay && codeEditor) {
            debuggingArea.classList.remove("hidden");
            
            // Use buggy_code if available, otherwise fall back to code_stub
            let codeToDisplay = currentChallenge.buggy_code || currentChallenge.code_stub || "";
            
            const bugCommentRegex = /^.*\/\/\s*BUG[:\s].*$/im;
            const match = codeToDisplay.match(bugCommentRegex);
            if (match) {
                actualHintForCurrentDebugChallenge = match[0].trim();
                codeToDisplay = codeToDisplay.replace(bugCommentRegex, "").trim();
            }
            
            buggyCodeDisplay.textContent = codeToDisplay;
            codeEditor.value = codeToDisplay;
            if(hintButton) hintButton.style.display = "inline-block";
        } else if (generalCodingArea && generalCodeEditor) { 
            generalCodingArea.classList.remove("hidden");
            
            // Use function_template if available, otherwise fall back to code_stub
            generalCodeEditor.value = currentChallenge.function_template || currentChallenge.code_stub || "";
            
            if (hintButton && currentChallenge.hint) {
                hintButton.style.display = "inline-block";
            }
        }
        showSection("detail");
    }

    function handleMcOptionClick(event) {
        if (!currentChallenge || currentChallenge.type !== "mcq" || !evaluationResultArea || !resultStatus || !resultExplanation || !mcqOptionsContainer) return;

        const selectedIndex = parseInt(event.target.dataset.index);
        
        // Handle both array of objects with correct property and correct_option index
        let correctIndex = -1;
        if (Array.isArray(currentChallenge.options)) {
            if (typeof currentChallenge.options[0] === 'object') {
                // Array of objects with correct property
                correctIndex = currentChallenge.options.findIndex(opt => opt.correct);
            } else if (typeof currentChallenge.correct_index === 'number') {
                // Array of strings with correct_index
                correctIndex = currentChallenge.correct_index;
            } else if (typeof currentChallenge.correct_option === 'number') {
                // Array of strings with correct_option index
                correctIndex = currentChallenge.correct_option;
            }
        }

        evaluationResultArea.classList.remove("hidden");
        resultExplanation.innerHTML = "";

        mcqOptionsContainer.querySelectorAll(".option-btn").forEach(btn => {
            btn.disabled = true;
            btn.classList.remove("correct", "incorrect", "correct-answer-reveal");
        });

        if (selectedIndex === correctIndex) {
            resultStatus.textContent = "Correct!";
            resultStatus.className = "status-correct";
            event.target.classList.add("correct");
            if (currentChallenge.explanation) {
                resultExplanation.innerHTML = `<p>${escapeHtml(currentChallenge.explanation)}</p>`;
            }
        } else {
            resultStatus.textContent = "Incorrect.";
            resultStatus.className = "status-incorrect";
            event.target.classList.add("incorrect");
            const correctButton = mcqOptionsContainer.querySelector(`.option-btn[data-index="${correctIndex}"]`);
            if (correctButton) correctButton.classList.add("correct-answer-reveal");
            if (currentChallenge.explanation) {
                resultExplanation.innerHTML = `<p>${escapeHtml(currentChallenge.explanation)}</p>`;
            }
        }
    }

    async function handleSubmitCode(type) {
        if (!currentChallenge || !evaluationResultArea || !resultStatus || !resultExplanation || !uploadStatus) return;

        let userCode = "";
        if (type === "debug" && codeEditor) {
            userCode = codeEditor.value;
        } else if (type === "general" && generalCodeEditor) {
            userCode = generalCodeEditor.value;
        } else {
            console.error("Unknown code submission type or editor not found");
            return;
        }

        uploadStatus.textContent = "Evaluating your submission...";
        uploadStatus.style.display = 'block';

        evaluationResultArea.classList.remove("hidden");
        resultStatus.textContent = "Evaluating...";
        if(resultMessage) resultMessage.textContent = "";
        resultExplanation.innerHTML = "";
        if(correctSolutionContainer) correctSolutionContainer.classList.add("hidden");

        try {
            const response = await fetch(`${API_BASE_URL}/api/submit/${currentChallenge.id}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ code: userCode }),
            });
            const result = await response.json();
            uploadStatus.textContent = ""; 
            uploadStatus.style.display = 'none';

            if (!response.ok) {
                throw new Error(result.error || `HTTP error! status: ${response.status}`);
            }

            resultStatus.textContent = `Status: ${escapeHtml(result.status)}`;
            resultStatus.className = result.status === "correct" ? "status-correct" : "status-incorrect";
            
            if (result.feedback) {
                resultExplanation.innerHTML += `<p><b>Feedback:</b> ${escapeHtml(result.feedback)}</p>`;
            }

            if (type === "debug" && resultMessage) {
                if (result.status !== "correct") {
                    resultMessage.textContent = "Try again. Look for syntax errors or logical bugs.";
                } else {
                    resultMessage.textContent = "Great job! You fixed the bug.";
                }
            }
        } catch (error) {
            console.error("Error submitting code:", error);
            if(uploadStatus) uploadStatus.textContent = "";
            if(uploadStatus) uploadStatus.style.display = 'none';
            if(resultStatus) resultStatus.textContent = "Error";
            if(resultStatus) resultStatus.className = "status-error";
            if(resultExplanation) resultExplanation.innerHTML = `<p>Error submitting code: ${escapeHtml(error.message)}</p>`;
        }
    }

    function handleHint() {
        if (!currentChallenge || !hintButton) return;

        if (currentChallenge.type === "mcq") {
            if (hintUsedForMcq) return;
            hintUsedForMcq = true;

            // For MCQ, eliminate one wrong option
            const options = currentChallenge.options || [];
            let correctIndex = -1;
            
            if (typeof options[0] === 'object') {
                correctIndex = options.findIndex(opt => opt.correct);
            } else if (typeof currentChallenge.correct_index === 'number') {
                correctIndex = currentChallenge.correct_index;
            } else if (typeof currentChallenge.correct_option === 'number') {
                correctIndex = currentChallenge.correct_option;
            }

            if (correctIndex >= 0 && mcqOptionsContainer) {
                // Find wrong options
                const wrongIndices = [];
                for (let i = 0; i < options.length; i++) {
                    if (i !== correctIndex) {
                        wrongIndices.push(i);
                    }
                }

                // Randomly select one wrong option to eliminate
                if (wrongIndices.length > 0) {
                    const indexToEliminate = wrongIndices[Math.floor(Math.random() * wrongIndices.length)];
                    const buttonToDisable = mcqOptionsContainer.querySelector(`.option-btn[data-index="${indexToEliminate}"]`);
                    if (buttonToDisable) {
                        buttonToDisable.disabled = true;
                        buttonToDisable.classList.add("eliminated");
                        buttonToDisable.title = "Eliminated by hint";
                    }
                }
            }
        } else if (currentChallenge.type === "debug") {
            // For debugging, show the bug comment
            if (actualHintForCurrentDebugChallenge && resultExplanation) {
                resultExplanation.innerHTML = `<p><b>Hint:</b> ${escapeHtml(actualHintForCurrentDebugChallenge)}</p>`;
                evaluationResultArea.classList.remove("hidden");
            } else if (currentChallenge.hint && resultExplanation) {
                resultExplanation.innerHTML = `<p><b>Hint:</b> ${escapeHtml(currentChallenge.hint)}</p>`;
                evaluationResultArea.classList.remove("hidden");
            }
        } else if (currentChallenge.hint && resultExplanation) {
            // For other types, show the hint text
            resultExplanation.innerHTML = `<p><b>Hint:</b> ${escapeHtml(currentChallenge.hint)}</p>`;
            evaluationResultArea.classList.remove("hidden");
        }
    }

    function handleRevealSolution() {
        if (!currentChallenge || !correctSolutionContainer || !correctCodeDisplay) return;

        correctSolutionContainer.classList.remove("hidden");
        
        if (currentChallenge.solution) {
            correctCodeDisplay.textContent = currentChallenge.solution;
        } else {
            correctCodeDisplay.textContent = "No solution available for this challenge.";
        }
        
        if (correctCodeExplanation) {
            if (currentChallenge.explanation) {
                correctCodeExplanation.innerHTML = `<p>${escapeHtml(currentChallenge.explanation)}</p>`;
            } else {
                correctCodeExplanation.innerHTML = "";
            }
        }
    }

    // Helper function to escape HTML
    function escapeHtml(unsafe) {
        if (typeof unsafe !== 'string') return '';
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
});
