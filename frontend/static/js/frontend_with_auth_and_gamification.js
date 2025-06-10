import React, { useState, useEffect } from 'react';
import { 
  registerUser, 
  loginUser, 
  logoutUser, 
  resetPassword, 
  getCurrentUser,
  updateUserScore,
  getLeaderboard,
  getUserProfile,
  getXpForNextLevel,
  getLevelProgress
} from './firebase_auth_and_gamification';
import './App.css';

function App() {
  // State for PDF upload and challenges
  const [file, setFile] = useState(null);
  const [uploadStatus, setUploadStatus] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [topics, setTopics] = useState([]);
  const [challenges, setChallenges] = useState([]);
  const [currentChallenge, setCurrentChallenge] = useState(null);
  const [solution, setSolution] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [isPolling, setIsPolling] = useState(false);
  
  // State for authentication and user profile
  const [user, setUser] = useState(null);
  const [userProfile, setUserProfile] = useState(null);
  const [authMode, setAuthMode] = useState('login'); // 'login', 'register', 'reset'
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [authError, setAuthError] = useState('');
  const [authSuccess, setAuthSuccess] = useState('');
  
  // State for gamification
  const [leaderboard, setLeaderboard] = useState([]);
  const [showLeaderboard, setShowLeaderboard] = useState(false);
  const [lastScoreUpdate, setLastScoreUpdate] = useState(null);
  
  // Check if user is logged in on component mount
  useEffect(() => {
    const checkUser = async () => {
      const currentUser = await getCurrentUser();
      if (currentUser) {
        setUser(currentUser);
        const profileResult = await getUserProfile(currentUser.uid);
        if (profileResult.success) {
          setUserProfile(profileResult.profile);
        }
      }
    };
    
    checkUser();
  }, []);
  
  // Fetch leaderboard when requested
  useEffect(() => {
    if (showLeaderboard) {
      fetchLeaderboard();
    }
  }, [showLeaderboard]);
  
  const fetchLeaderboard = async () => {
    const result = await getLeaderboard(10);
    if (result.success) {
      setLeaderboard(result.leaderboard);
    }
  };
  
  // Authentication handlers
  const handleRegister = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    
    if (!email || !password || !displayName) {
      setAuthError('All fields are required');
      return;
    }
    
    const result = await registerUser(email, password, displayName);
    if (result.success) {
      setUser(result.user);
      setAuthSuccess('Registration successful! Welcome to Programming Challenge Generator.');
      setAuthMode('login');
      
      // Fetch user profile
      const profileResult = await getUserProfile(result.user.uid);
      if (profileResult.success) {
        setUserProfile(profileResult.profile);
      }
      
      // Clear form
      setEmail('');
      setPassword('');
      setDisplayName('');
    } else {
      setAuthError(result.error);
    }
  };
  
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    
    if (!email || !password) {
      setAuthError('Email and password are required');
      return;
    }
    
    const result = await loginUser(email, password);
    if (result.success) {
      setUser(result.user);
      setAuthSuccess('Login successful!');
      
      // Fetch user profile
      const profileResult = await getUserProfile(result.user.uid);
      if (profileResult.success) {
        setUserProfile(profileResult.profile);
      }
      
      // Clear form
      setEmail('');
      setPassword('');
    } else {
      setAuthError(result.error);
    }
  };
  
  const handleLogout = async () => {
    const result = await logoutUser();
    if (result.success) {
      setUser(null);
      setUserProfile(null);
      setDocumentId('');
      setChallenges([]);
      setCurrentChallenge(null);
    }
  };
  
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthSuccess('');
    
    if (!email) {
      setAuthError('Email is required');
      return;
    }
    
    const result = await resetPassword(email);
    if (result.success) {
      setAuthSuccess('Password reset email sent. Check your inbox.');
      setAuthMode('login');
    } else {
      setAuthError(result.error);
    }
  };
  
  // PDF upload and challenge handlers
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
    if (!currentChallenge || !user) return;
    
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
      
      // Update user score in Firebase
      if (result.result === 'correct') {
        const baseScore = 10;
        const scoreResult = await updateUserScore(user.uid, baseScore, difficulty);
        
        if (scoreResult.success) {
          setLastScoreUpdate(scoreResult);
          
          // Update user profile
          const profileResult = await getUserProfile(user.uid);
          if (profileResult.success) {
            setUserProfile(profileResult.profile);
          }
          
          // Update leaderboard if it's visible
          if (showLeaderboard) {
            fetchLeaderboard();
          }
        }
      }
      
      // Show result to user
      alert(`Result: ${result.result}\nFeedback: ${result.feedback}\nScore: ${result.score}`);
    } catch (error) {
      console.error('Error submitting solution:', error);
      alert(`Error submitting solution: ${error.message}`);
    }
  };

  const handleSelectChallenge = (challenge) => {
    setCurrentChallenge(challenge);
    setSolution('');
    setLastScoreUpdate(null);
  };

  const handleBackToList = () => {
    setCurrentChallenge(null);
    setLastScoreUpdate(null);
  };
  
  // Render functions
  const renderAuthForm = () => {
    if (authMode === 'login') {
      return (
        <div className="auth-form">
          <h2>Login</h2>
          {authError && <p className="error">{authError}</p>}
          {authSuccess && <p className="success">{authSuccess}</p>}
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input 
                type="email" 
                id="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input 
                type="password" 
                id="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
            </div>
            <button type="submit">Login</button>
          </form>
          <p>
            Don't have an account? 
            <button 
              className="text-button" 
              onClick={() => setAuthMode('register')}
            >
              Register
            </button>
          </p>
          <p>
            Forgot password? 
            <button 
              className="text-button" 
              onClick={() => setAuthMode('reset')}
            >
              Reset Password
            </button>
          </p>
        </div>
      );
    } else if (authMode === 'register') {
      return (
        <div className="auth-form">
          <h2>Register</h2>
          {authError && <p className="error">{authError}</p>}
          {authSuccess && <p className="success">{authSuccess}</p>}
          <form onSubmit={handleRegister}>
            <div className="form-group">
              <label htmlFor="displayName">Display Name:</label>
              <input 
                type="text" 
                id="displayName" 
                value={displayName} 
                onChange={(e) => setDisplayName(e.target.value)} 
                required 
              />
            </div>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input 
                type="email" 
                id="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
              />
            </div>
            <div className="form-group">
              <label htmlFor="password">Password:</label>
              <input 
                type="password" 
                id="password" 
                value={password} 
                onChange={(e) => setPassword(e.target.value)} 
                required 
              />
            </div>
            <button type="submit">Register</button>
          </form>
          <p>
            Already have an account? 
            <button 
              className="text-button" 
              onClick={() => setAuthMode('login')}
            >
              Login
            </button>
          </p>
        </div>
      );
    } else if (authMode === 'reset') {
      return (
        <div className="auth-form">
          <h2>Reset Password</h2>
          {authError && <p className="error">{authError}</p>}
          {authSuccess && <p className="success">{authSuccess}</p>}
          <form onSubmit={handleResetPassword}>
            <div className="form-group">
              <label htmlFor="email">Email:</label>
              <input 
                type="email" 
                id="email" 
                value={email} 
                onChange={(e) => setEmail(e.target.value)} 
                required 
              />
            </div>
            <button type="submit">Send Reset Email</button>
          </form>
          <p>
            Remember your password? 
            <button 
              className="text-button" 
              onClick={() => setAuthMode('login')}
            >
              Back to Login
            </button>
          </p>
        </div>
      );
    }
  };
  
  const renderUserProfile = () => {
    if (!userProfile) return null;
    
    const levelProgress = getLevelProgress(userProfile.xp, userProfile.level);
    const xpForNextLevel = getXpForNextLevel(userProfile.level);
    
    return (
      <div className="user-profile">
        <h3>Welcome, {userProfile.displayName}!</h3>
        <div className="profile-stats">
          <div className="stat">
            <span className="stat-label">Level:</span>
            <span className="stat-value">{userProfile.level}</span>
          </div>
          <div className="stat">
            <span className="stat-label">XP:</span>
            <span className="stat-value">{userProfile.xp} / {xpForNextLevel}</span>
            <div className="progress-bar">
              <div className="progress" style={{ width: `${levelProgress}%` }}></div>
            </div>
          </div>
          <div className="stat">
            <span className="stat-label">Streak:</span>
            <span className="stat-value">{userProfile.streak} days 🔥</span>
          </div>
          <div className="stat">
            <span className="stat-label">Total Score:</span>
            <span className="stat-value">{userProfile.totalScore}</span>
          </div>
          <div className="stat">
            <span className="stat-label">Challenges Completed:</span>
            <span className="stat-value">{userProfile.challengesCompleted}</span>
          </div>
        </div>
        <div className="profile-actions">
          <button onClick={() => setShowLeaderboard(!showLeaderboard)}>
            {showLeaderboard ? 'Hide Leaderboard' : 'Show Leaderboard'}
          </button>
          <button onClick={handleLogout}>Logout</button>
        </div>
      </div>
    );
  };
  
  const renderLeaderboard = () => {
    if (!showLeaderboard) return null;
    
    return (
      <div className="leaderboard">
        <h3>Leaderboard</h3>
        {leaderboard.length === 0 ? (
          <p>Loading leaderboard...</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Rank</th>
                <th>Player</th>
                <th>Level</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {leaderboard.map((entry, index) => (
                <tr key={entry.id} className={entry.userId === user?.uid ? 'current-user' : ''}>
                  <td>{index + 1}</td>
                  <td>{entry.displayName}</td>
                  <td>{entry.level}</td>
                  <td>{entry.score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    );
  };
  
  const renderScoreUpdate = () => {
    if (!lastScoreUpdate) return null;
    
    return (
      <div className="score-update">
        <h3>Challenge Completed!</h3>
        <div className="update-details">
          <p>Score: +{lastScoreUpdate.scoreAdded}</p>
          <p>XP: +{lastScoreUpdate.xpGained}</p>
          {lastScoreUpdate.leveledUp && (
            <p className="level-up">Level Up! You are now level {lastScoreUpdate.newLevel}! 🎉</p>
          )}
          {lastScoreUpdate.streakIncreased && (
            <p className="streak-up">Streak increased to {lastScoreUpdate.newStreak} days! 🔥</p>
          )}
        </div>
      </div>
    );
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
              <div className={`difficulty-badge difficulty-${challenge.difficulty}`}>
                {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
              </div>
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
        <div className={`difficulty-badge difficulty-${challenge.difficulty}`}>
          {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
        </div>
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
        <div className={`difficulty-badge difficulty-${challenge.difficulty}`}>
          {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
        </div>
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
        <div className={`difficulty-badge difficulty-${challenge.difficulty}`}>
          {challenge.difficulty.charAt(0).toUpperCase() + challenge.difficulty.slice(1)}
        </div>
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
        {renderScoreUpdate()}
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
      
      {!user ? (
        renderAuthForm()
      ) : (
        <div className="main-content">
          {renderUserProfile()}
          {renderLeaderboard()}
          
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
        </div>
      )}
      
      <footer>
        <p>Programming Challenge Generator © 2025</p>
      </footer>
    </div>
  );
}

export default App;
