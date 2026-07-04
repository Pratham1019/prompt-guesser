import React, { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';

interface PromptInputProps {
  onSubmit: (guess: string) => Promise<void>;
  attemptsRemaining: number;
  disabled: boolean;
}

export const PromptInput: React.FC<PromptInputProps> = ({
  onSubmit,
  attemptsRemaining,
  disabled,
}) => {
  const [guess, setGuess] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanGuess = guess.trim();

    if (!cleanGuess) return;

    setLoading(true);
    setError(null);
    try {
      await onSubmit(cleanGuess);
      setGuess(''); // Clear input on success
    } catch (err: any) {
      setError(err.message || 'Failed to submit guess. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="brutal-card prompt-input-card">
      <div className="prompt-input-header">
        <span className="mono-label">Enter your guess</span>
        <span className="badge-brutal bg-[#FF1CAE] text-white">
          {attemptsRemaining} attempts left
        </span>
      </div>

      <form onSubmit={handleSubmit} className="prompt-input-form">
        <input
          type="text"
          value={guess}
          onChange={(e) => {
            setGuess(e.target.value);
            if (error) setError(null);
          }}
          placeholder="A tiny astronaut fishing from Saturn's rings..."
          disabled={disabled || loading}
          maxLength={1000}
          autoComplete="off"
          autoCorrect="off"
          autoCapitalize="none"
          spellCheck={false}
          className="brutal-input"
          required
        />
        <button
          type="submit"
          disabled={disabled || loading || !guess.trim()}
          className="brutal-btn"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={16} />
              Evaluating...
            </>
          ) : (
            <>
              <Send size={16} />
              Submit guess
            </>
          )}
        </button>
      </form>

      {error && (
        <div className="error-bubble">
          <span>{error}</span>
        </div>
      )}
    </div>
  );
};
