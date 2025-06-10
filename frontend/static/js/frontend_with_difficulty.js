import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [topics, setTopics] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [currentChallenge, setCurrentChallenge] = useState(null);
  const [solution, setSolution] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [isPolling, setIsPolling] = useState(false);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
  };

  const handleDifficultyChange = (e) => {
    setDifficulty(e.target.value);
  };

  const handlePdfUpload = async (e) => {
    e.preventDefault();
    console.log("handlePdfUpload triggered");
    
    if (!file) {
      setUploadStatus('Please select a file first');
      return;
    }

    setUploadStatus('processing...');
    
    const formData = new FormData();
    formData.append('file', file);
    formData.append('difficulty', difficulty);

    try {
      const response = await fetch('http://localhost:5000/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setDocumentId(result.document_id);
      
      // Start polling for status
      if (result.document_id) {
        console.log(`Starting to poll status for document: ${result.document_id}`);
        setIsPolling(true);
        pollDocumentStatus(result.document_id);
      }
      
      console.log("handlePdfUpload finished.");
    } catch (error) {
      console.error('Error uploading PDF:', error);
      setUploadStatus(`Error uploading PDF: ${error.message}`);
    }
  };

  const pollDocumentStatus = async (docId) => {
    try {
      const response = await fetch(`http://localhost:5000/api/documents/${docId}/status`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const statusData = await response.json();
      console.log(`Document status: ${statusData.status}, Challenge count: ${statusData.generated_challenge_count}`);
      
      if (statusData.status === 'completed') {
        setUploadStatus(`PDF processed: ${statusData.topics_count} topics. Found ${statusData.generated_challenge_count} challenges.`);
        fetchChallenges(docId);
        setIsPolling(false);
      } else if (statusData.status === 'error') {
        setUploadStatus(`Error processing PDF: ${statusData.error || 'Unknown error'}`);
        setIsPolling(false);
      } else {
        // Continue polling
        setTimeout(() => pollDocumentStatus(docId), 2000);
      }
    } catch (error) {
      console.error('Error polling document status:', error);
      setUploadStatus(`Error checking status: ${error.message}`);
      setIsPolling(false);
    }
  };

  const fetchChallenges = async (docId) => {
    try {
      console.log(`Fetching challenges for document: ${docId}`);
      const response = await fetch(`http://localhost:5000/api/documents/${docId}/challenges`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setTopics(data.topics || []);
      setChallenges(data.challenges || []);
      console.log(`Fetched ${data.challenges.length} challenges for ${data.topics.length} topics`);
      
      if (data.challenges.length > 0) {
        // Display the first challenge
        setCurrentChallenge(data.challenges[0]);
        console.log("Displaying challenge: ", data.challenges[0]);
      } else {
        setUploadStatus('No challenges could be generated from this PDF.');
      }
    } catch (error) {
      console.error('Error fetching challenges:', error);
      setUploadStatus(`Error fetching challenges: ${error.message}`);
    }
  };

  const handleSolutionChange = (e) => {
    setSolution(e.target.value);
  };

  const handleSubmitSolution = async () => {
    if (!currentChallenge) return;
    
    try {
      const response = await fetch(`http://localhost:5000/api/submit/${currentChallenge.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ solution }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const result = await response.json();
      alert(`Result: ${result.result}\nFeedback: ${result.feedback}\nScore: ${result.score}`);
    } catch (error) {
      console.error('Error submitting solution:', error);
      alert(`Error submitting solution: ${error.message}`);
    }
  };

  const handleSelectChallenge = (challenge) => {
    setCurrentChallenge(challenge);
    setSolution('');
  };

  const handleBackToList = () => {
    setCurrentChallenge(null);
  };

  const renderChallengeList = () => {
    return (
      <div>
        <h2>Generated Challenges</h2>
        <div>
          <h3>Extracted Topics:</h3>
          <ul>
            {topics.map((topic, index) => (
              <li key={index}>{topic}</li>
            ))}
          </ul>
        </div>
        <div>
          <h3>Programming Challenges:</h3>
          {challenges.map((challenge, index) => (
            <div key={index} className="challenge-card">
              <h4>{challenge.topic} #{index + 1}</h4>
              <p>{challenge.type === 'multiple_choice' ? 'MULTIPLE CHOICE QUESTION' : 
                 challenge.type === 'debugging' ? 'DEBUGGING CHALLENGE' : 
                 'CODING CHALLENGE'}: {challenge.question_text.substring(0, 100)}...</p>
              <button onClick={() => handleSelectChallenge(challenge)}>View Challenge</button>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderMultipleChoiceChallenge = (challenge) => {
    return (
      <div>
        <h3>{challenge.topic}</h3>
        <p>{challenge.question_text}</p>
        <div className="options">
          {challenge.options.map((option, index) => (
            <div key={index} className="option">
              <input 
                type="radio" 
                id={`option-${index}`} 
                name="answer" 
                value={index} 
                onChange={() => setSolution(String(index))}
              />
              <label htmlFor={`option-${index}`}>{option}</label>
            </div>
          ))}
        </div>
        <button onClick={handleSubmitSolution}>Submit Answer</button>
        <button className="hint-button" onClick={() => alert(challenge.hint)}>Get a Hint</button>
      </div>
    );
  };

  const renderCodingChallenge = (challenge) => {
    return (
      <div>
        <h3>{challenge.topic}</h3>
        <p>{challenge.question_text}</p>
        <div>
          <h4>Your Solution:</h4>
          <textarea 
            className="code-editor"
            value={solution || challenge.code_stub}
            onChange={handleSolutionChange}
            rows={15}
          />
        </div>
        <button onClick={handleSubmitSolution}>Submit Solution</button>
      </div>
    );
  };

  const renderDebuggingChallenge = (challenge) => {
    return (
      <div>
        <h3>{challenge.topic}</h3>
        <p>{challenge.question_text}</p>
        <div>
          <h4>Buggy Code:</h4>
          <pre className="code-display">{challenge.code_stub}</pre>
          <h4>Your Fix:</h4>
          <textarea 
            className="code-editor"
            value={solution || challenge.code_stub}
            onChange={handleSolutionChange}
            rows={15}
          />
        </div>
        <button onClick={handleSubmitSolution}>Submit Fix</button>
        <button className="hint-button" onClick={() => alert(challenge.hint)}>Reveal Correct Code</button>
      </div>
    );
  };

  const renderChallenge = () => {
    if (!currentChallenge) return null;

    return (
      <div>
        <button className="back-button" onClick={handleBackToList}>← Back to Challenges</button>
        {currentChallenge.type === 'multiple_choice' ? renderMultipleChoiceChallenge(currentChallenge) :
         currentChallenge.type === 'debugging' ? renderDebuggingChallenge(currentChallenge) :
         renderCodingChallenge(currentChallenge)}
      </div>
    );
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Programming Challenge Generator</h1>
        <p>Upload a PDF document to generate programming challenges based on its content</p>
      </header>
      
      {!documentId || !challenges.length ? (
        <div className="upload-section">
          <form onSubmit={handlePdfUpload}>
            <div className="form-group">
              <label htmlFor="difficulty">Select Difficulty:</label>
              <select 
                id="difficulty" 
                value={difficulty} 
                onChange={handleDifficultyChange}
              >
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>
            <div className="form-group">
              <input type="file" accept=".pdf" onChange={handleFileChange} />
              <button type="submit" disabled={!file || isPolling}>
                {isPolling ? 'Processing...' : 'Upload and Generate Challenges'}
              </button>
            </div>
          </form>
          <p className="status">{uploadStatus}</p>
        </div>
      ) : (
        <div className="challenge-section">
          {currentChallenge ? renderChallenge() : renderChallengeList()}
        </div>
      )}
      
      <footer>
        <p>Programming Challenge Generator © 2025</p>
      </footer>
    </div>
  );
}

export default App;
