import { useState, useEffect } from 'react';
import { getTodayChallenge, submitGuess } from './api';
import type { DailyChallengeResponse } from './types';
import { Header } from './components/Header';
import { ChallengeImage } from './components/ChallengeImage';
import { PromptInput } from './components/PromptInput';
import { GuessHistory } from './components/GuessHistory';
import { ResultCard } from './components/ResultCard';
import { HelpModal, AboutModal, SettingsModal } from './components/Modals';
import { AlertCircle, RefreshCw } from 'lucide-react';

function App() {
  const [challenge, setChallenge] = useState<DailyChallengeResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [imageToken, setImageToken] = useState(Date.now());

  // Modals state
  const [helpOpen, setHelpOpen] = useState(false);
  const [aboutOpen, setAboutOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  // Load the challenge on startup
  const fetchChallenge = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getTodayChallenge();
      setChallenge(data);
      setImageToken(Date.now());
    } catch (err: any) {
      console.error(err);
      setError(
        err.message || 'Could not connect to the backend server. Make sure it is running at http://localhost:8000.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChallenge();
  }, []);

  // Handle a guess submission
  const handleGuessSubmit = async (guessText: string) => {
    if (!challenge) return;

    // Call API
    const updatedSession = await submitGuess(guessText);

    // Update state
    setChallenge({
      ...challenge,
      session: updatedSession,
    });
  };

  // Erases local player session data to reset state (forces a clean game start)
  const handleResetSession = () => {
    localStorage.removeItem('prompt_guesser_player_id');
    setChallenge(null);
    fetchChallenge();
  };

  const isCompleted = challenge?.session?.is_completed || false;
  const attempts = challenge?.session?.attempts || [];
  const bestScore = challenge?.session?.best_score || 0;
  const attemptsRemaining = challenge?.session?.attempts_remaining ?? 5;
  const attemptsUsed = challenge?.session?.attempts_used ?? 0;
  const revealedPrompt = challenge?.session?.revealed_prompt ?? '';

  return (
    <div className="app-layout">
      {/* Navigation Header */}
      <Header
        onOpenHelp={() => setHelpOpen(true)}
        onOpenAbout={() => setAboutOpen(true)}
        onOpenSettings={() => setSettingsOpen(true)}
        bestScore={bestScore}
      />

      {/* Main Game Interface */}
      <main className="app-main">
        {loading ? (
          /* Loading Skeleton Grid */
          <div className="loading-skeleton-grid">
            <div>
              <div className="brutal-skeleton" style={{ width: '100%', aspectRatio: '4/3' }} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div className="brutal-skeleton" style={{ height: '96px', width: '100%' }} />
              <div className="brutal-skeleton" style={{ height: '192px', width: '100%' }} />
            </div>
          </div>
        ) : error ? (
          /* Error Card Panel */
          <div className="brutal-card error-card-wrapper brutal-shadow-lg">
            <div className="error-card-icon">
              <AlertCircle size={48} />
            </div>
            <h2>CONNECTION FAULT</h2>
            <p style={{ fontWeight: 600, fontSize: '1rem', margin: 0 }}>
              {error}
            </p>
            <button
              onClick={fetchChallenge}
              className="brutal-btn"
              style={{ backgroundColor: '#E0FF1C', color: '#111111', width: '100%', marginTop: '16px' }}
            >
              <RefreshCw size={16} />
              RETRY CONNECTION
            </button>
          </div>
        ) : challenge ? (
          /* Game Layout */
          <div>
            {isCompleted ? (
              /* Completion Screen Grid */
              <div className="game-grid">
                <div>
                  <ChallengeImage
                    imageUrl={challenge.image_url}
                    publishDate={challenge.publish_date}
                    loading={false}
                    imageToken={imageToken}
                  />
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  <ResultCard
                    bestScore={bestScore}
                    attemptsUsed={attemptsUsed}
                    revealedPrompt={revealedPrompt}
                    attempts={attempts}
                    publishDate={challenge.publish_date}
                    onReset={handleResetSession}
                  />
                  <GuessHistory attempts={attempts} />
                </div>
              </div>
            ) : (
              /* Active Gameplay Grid */
              <div className="game-grid">
                {/* Left Side: Challenge image */}
                <div>
                  <ChallengeImage
                    imageUrl={challenge.image_url}
                    publishDate={challenge.publish_date}
                    loading={false}
                    imageToken={imageToken}
                  />
                </div>

                {/* Right Side: Gameplay submission and history */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* Guess submission component */}
                  <PromptInput
                    onSubmit={handleGuessSubmit}
                    attemptsRemaining={attemptsRemaining}
                    disabled={isCompleted}
                  />

                  {/* Guess attempt stack */}
                  <GuessHistory attempts={attempts} />
                </div>
              </div>
            )}
          </div>
        ) : null}
      </main>

      {/* Footer copyright */}
      <footer className="footer-bar">
        <span className="mono-label" style={{ color: '#666', fontSize: '10px' }}>
          PROMPT GUESSER ARCADE © 2026 · ALL SYSTEMS OPERATIONAL
        </span>
      </footer>

      {/* Modals components */}
      <HelpModal isOpen={helpOpen} onClose={() => setHelpOpen(false)} />
      <AboutModal isOpen={aboutOpen} onClose={() => setAboutOpen(false)} />
      <SettingsModal
        isOpen={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onReset={handleResetSession}
      />
    </div>
  );
}

export default App;
