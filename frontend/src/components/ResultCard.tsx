import React, { useState } from 'react';
import { Share2, RefreshCw } from 'lucide-react';
import type { GuessAttempt } from '../types';

interface ResultCardProps {
  bestScore: number;
  attemptsUsed: number;
  revealedPrompt: string;
  attempts: GuessAttempt[];
  publishDate: string;
  onReset: () => void;
}

export const ResultCard: React.FC<ResultCardProps> = ({
  bestScore,
  attemptsUsed,
  revealedPrompt,
  attempts,
  publishDate,
  onReset,
}) => {
  const [shared, setShared] = useState(false);
  const isPerfect = bestScore >= 100;

  const getEmojiGrid = () => {
    return attempts
      .map((att) => {
        const score = att.similarity_score;
        if (score >= 90) return '🟩';
        if (score >= 70) return '🟨';
        if (score >= 40) return '🟧';
        return '🟥';
      })
      .join(' ');
  };

  const handleShare = () => {
    const emojiGrid = getEmojiGrid();
    const shareText = `Prompt Guesser [${publishDate}]
Best Score: ${Math.round(bestScore)}%
Attempts: ${attemptsUsed}/5
Grid: ${emojiGrid}

Play at http://localhost:5173`;

    navigator.clipboard.writeText(shareText);
    setShared(true);
    setTimeout(() => setShared(false), 2000);
  };



  return (
    <div className="brutal-card result-card animate-pop">
      {/* Banner */}
      <div
        className="result-card-banner"
        style={{
          backgroundColor: isPerfect ? '#1CFF3B' : '#FFA000',
          textAlign: 'center',
        }}
      >
        <h2>
          {isPerfect ? 'Challenge Completed!' : 'Challenge Over!'}
        </h2>
        <span className="mono-label" style={{ fontSize: '14px', fontWeight: 600 }}>
          {isPerfect ? 'You guessed it in ' + attemptsUsed + ' attempts!' : '5 attempts used'}
        </span>
      </div>

      {/* Grid stats */}
      <div className="result-stats-row">
        <div style={{ textAlign: 'center' }}>
          <span className="mono-label" style={{ color: '#555', fontSize: '12px' }}>Best Score</span>
          <span className="result-stat-val">{Math.round(bestScore)}%</span>
        </div>
        <div style={{ textAlign: 'center' }}>
          <span className="mono-label" style={{ color: '#555', fontSize: '12px' }}>Attempts</span>
          <span className="result-stat-val">{attemptsUsed}/5</span>
        </div>
      </div>

      {/* Emoji share block */}
      <div className="result-emoji-block" style={{ textAlign: 'center' }}>
        <span className="mono-label" style={{ color: '#555', fontSize: '13px' }}>Guess Pattern</span>
        <div className="result-emoji-grid">{getEmojiGrid()}</div>
      </div>

      {/* Revealed prompt */}
      <div className="result-prompt-section">
        <span
          className="mono-label brutal-border-sm"
          style={{
            backgroundColor: '#1C3BFF',
            color: '#FFFFFF',
            padding: '2px 8px',
            alignSelf: 'flex-start',
          }}
        >
          Original Target Prompt
        </span>
        <div className="result-prompt-box">
          "{revealedPrompt}"
        </div>
      </div>

      {/* Best Guess */}
      <div className="result-prompt-section">
        <span
          className="mono-label brutal-border-sm"
          style={{
            backgroundColor: '#FF1CAE',
            color: '#FFFFFF',
            padding: '2px 8px',
            alignSelf: 'flex-start',
          }}
        >
          Your Best Guess
        </span>
        <div className="result-prompt-box">
          "{[...attempts].sort((a, b) => b.similarity_score - a.similarity_score)[0]?.guess_text || ''}"
        </div>
      </div>

      {/* Share actions */}
      <div className="result-actions">
        <button
          onClick={handleShare}
          className="brutal-btn"
          style={{ backgroundColor: '#1CFF3B' }}
        >
          <Share2 size={16} />
          {shared ? 'Copied to Clipboard!' : 'Share Results'}
        </button>

        <button
          onClick={onReset}
          className="brutal-btn"
          style={{ backgroundColor: '#FF1CAE' }}
          title="Play Again (Erase Session)"
        >
          <RefreshCw size={16} />
          Reset Play
        </button>
      </div>
    </div>
  );
};
