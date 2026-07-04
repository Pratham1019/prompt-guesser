import React from 'react';
import type { GuessAttempt } from '../types';

interface GuessHistoryProps {
  attempts: GuessAttempt[];
}

export const GuessHistory: React.FC<GuessHistoryProps> = ({ attempts }) => {
  if (attempts.length === 0) {
    return (
      <div className="brutal-card" style={{ textAlign: 'center', padding: '32px 16px' }}>
        <span className="mono-label" style={{ color: '#666' }}>
          No guesses submitted yet. Make your first attempt above!
        </span>
      </div>
    );
  }

  // Reverse attempts list to show the latest on top
  const sortedAttempts = [...attempts].reverse();

  const getScoreColor = (score: number) => {
    if (score >= 90) return '#1CFF3B'; // Green
    if (score >= 70) return '#E0FF1C'; // Yellow
    if (score >= 40) return '#FFA000'; // Orange
    return '#FF1CAE'; // Pink
  };

  return (
    <div className="history-container">
      <h3 className="mono-label" style={{ fontSize: '0.875rem' }}>
        Guess history ({attempts.length}/5)
      </h3>
      
      <div className="history-list">
        {sortedAttempts.map((attempt) => {
          const badgeColor = getScoreColor(attempt.similarity_score);
          const isLowScore = attempt.similarity_score < 40;

          return (
            <div key={attempt.id} className="brutal-card history-item animate-pop">
              {/* Score circle badge */}
              <div
                className="score-badge brutal-border-sm"
                style={{
                  backgroundColor: badgeColor,
                  color: isLowScore ? '#FFFFFF' : '#111111',
                }}
              >
                <span className="score-badge-val">{Math.round(attempt.similarity_score)}%</span>
                <span className="score-badge-lbl">Score</span>
              </div>

              {/* Content info */}
              <div className="history-item-details">
                <div className="history-item-header">
                  <span
                    className="mono-label brutal-border-sm"
                    style={{
                      backgroundColor: '#1C3BFF',
                      color: '#FFFFFF',
                      padding: '2px 8px',
                      fontSize: '10px',
                    }}
                  >
                    Attempt #{attempt.attempt_number}
                  </span>
                  <span className="history-item-time">
                    {(() => {
                      const dateStr = attempt.created_at;
                      const utcDateStr = (dateStr && !dateStr.endsWith('Z') && !dateStr.includes('+'))
                        ? `${dateStr}Z`
                        : dateStr;
                      return new Date(utcDateStr).toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      });
                    })()}
                  </span>
                </div>
                
                <p className="history-item-text">
                  "{attempt.guess_text}"
                </p>
                
                <p className="history-item-feedback">
                  {attempt.evaluation_feedback}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
