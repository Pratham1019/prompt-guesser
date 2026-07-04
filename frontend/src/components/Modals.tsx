import React, { useState } from 'react';
import { X, Copy, RotateCcw, AlertTriangle } from 'lucide-react';
import { getPlayerId, overrideChallengePrompt } from '../api';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const BaseModal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="brutal-card modal-card">
        {/* Modal Header */}
        <div className="modal-header">
          <h2>{title}</h2>
          <button
            onClick={onClose}
            className="brutal-btn modal-close-btn"
            style={{ backgroundColor: '#FF1CAE', width: '36px', height: '36px', padding: '0' }}
          >
            <X size={20} />
          </button>
        </div>
        {/* Modal Content */}
        <div className="modal-body">{children}</div>
      </div>
    </div>
  );
};

export const HelpModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="How to Play">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <p style={{ fontWeight: 600, fontSize: '1.1rem', margin: 0 }}>
          Decode the AI prompt behind today's daily image!
        </p>

        <ol style={{ paddingLeft: '20px', margin: 0, display: 'flex', flexDirection: 'column', gap: '12px', fontWeight: 600 }}>
          <li>Inspect the image carefully to identify subjects, action, environment, styles, and mood.</li>
          <li>Submit a guess prompt describing the image in detail.</li>
          <li>
            Receive a score from <strong style={{ color: '#1C3BFF' }}>0% to 100%</strong> based on how closely your guess matches the meaning of the original prompt.
          </li>
          <li>
            You have a maximum of <strong style={{ color: '#FF1CAE' }}>5 attempts</strong>.
          </li>
          <li>
            A score of <strong style={{ color: '#1CFF3B' }}>100%</strong> wins the game instantly!
          </li>
        </ol>

        <div className="brutal-card brutal-shadow" style={{ backgroundColor: '#E0FF1C', padding: '16px', fontSize: '0.875rem', marginTop: '16px' }}>
          <p style={{ fontWeight: 800, margin: '0 0 8px 0', display: 'flex', alignItems: 'center', gap: '6px' }}>
            Pro Tip:
          </p>
          <p style={{ fontWeight: 600, margin: 0 }}>
            Gemini matches meaning rather than exact words. Focus on describing:
            <br />
            <strong>Subject + Action + Setting + Art Style + Lighting</strong>.
          </p>
        </div>
      </div>
    </BaseModal>
  );
};

export const AboutModal: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="About Game">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontWeight: 600 }}>
        <p style={{ margin: 0 }}>
          <strong>Prompt Guesser</strong> is a modern daily puzzle game where players test their reverse-engineering intuition against AI interpretation.
        </p>

        <p style={{ margin: 0 }}>
          Built using a modern technical stack:
        </p>

        <ul style={{ paddingLeft: '20px', margin: 0, display: 'flex', flexDirection: 'column', gap: '6px' }}>
          <li><strong>Frontend:</strong> React, TypeScript, Vite, Vanilla CSS</li>
          <li><strong>Design Language:</strong> Neo-Brutalism</li>
          <li><strong>Backend:</strong> FastAPI, SQLite, SQLAlchemy, Alembic</li>
          <li><strong>AI Content Generation:</strong> Imagen 4.0</li>
          <li><strong>Semantic Scoring:</strong> Gemini 2.5 Flash</li>
        </ul>

        <p style={{ fontSize: '0.875rem', borderTop: '2px solid #111111', paddingTop: '12px', margin: '12px 0 0 0', color: '#555' }}>
          Created for prompt engineering enthusiasts and general gamers alike.
        </p>
      </div>
    </BaseModal>
  );
};



export const SettingsModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  onReset: () => void;
  onOverrideChallenge?: () => void;
}> = ({ isOpen, onClose, onReset, onOverrideChallenge }) => {
  const [copied, setCopied] = useState(false);
  const [overridePrompt, setOverridePrompt] = useState('');
  const [overrideLoading, setOverrideLoading] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);
  const [overrideSuccess, setOverrideSuccess] = useState(false);
  const [overrideResponse, setOverrideResponse] = useState<any>(null);
  const playerId = getPlayerId();

  const handleCopyId = () => {
    navigator.clipboard.writeText(playerId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const cleanPrompt = overridePrompt.trim();
    if (!cleanPrompt) return;

    setOverrideLoading(true);
    setOverrideError(null);
    setOverrideSuccess(false);
    setOverrideResponse(null);
    try {
      const res = await overrideChallengePrompt(cleanPrompt);
      setOverrideResponse(res);
      setOverrideSuccess(true);
      setOverridePrompt('');
      if (onOverrideChallenge) {
        onOverrideChallenge();
      }
    } catch (err: any) {
      setOverrideError(err.message || 'Failed to override challenge.');
    } finally {
      setOverrideLoading(false);
    }
  };

  return (
    <BaseModal isOpen={isOpen} onClose={onClose} title="Settings">
      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        {/* Player Profile Details */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label className="mono-label" style={{ fontSize: '11px', display: 'block' }}>Player Identifier</label>
          <div style={{ display: 'flex', gap: '8px' }}>
            <input
              type="text"
              readOnly
              value={playerId}
              className="brutal-input"
              style={{ fontSize: '0.875rem', backgroundColor: '#FFFFFF', cursor: 'default', flex: 1 }}
            />
            <button
              onClick={handleCopyId}
              className="brutal-btn"
              style={{ backgroundColor: '#1C3BFF', color: '#FFFFFF', padding: '0', width: '48px', height: '48px' }}
              title="Copy ID"
            >
              <Copy size={16} />
            </button>
          </div>
          {copied && (
            <p className="mono-label" style={{ color: '#1CFF3B', fontSize: '10px', margin: 0 }}>
              Player ID copied to clipboard!
            </p>
          )}
        </div>

        {/* Developer Override Options (DEV MODE ONLY) */}
        {import.meta.env.DEV && (
          <div style={{ borderTop: '4px solid #111111', paddingTop: '16px', marginTop: '8px' }}>
            <h3 className="mono-label" style={{ color: '#1C3BFF', display: 'flex', alignItems: 'center', gap: '6px', margin: '0 0 8px 0' }}>
              Developer Overrides (Dev Only)
            </h3>
            <p style={{ fontSize: '0.875rem', fontWeight: 600, margin: '0 0 12px 0' }}>
              Override today's daily challenge target prompt. All sessions will be reset.
            </p>
            <form onSubmit={handleOverrideSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <input
                type="text"
                value={overridePrompt}
                onChange={(e) => {
                  setOverridePrompt(e.target.value);
                  if (overrideError) setOverrideError(null);
                  if (overrideSuccess) setOverrideSuccess(false);
                }}
                placeholder="Enter new target prompt..."
                className="brutal-input"
                style={{ fontSize: '0.875rem', backgroundColor: '#FFFFFF' }}
                disabled={overrideLoading}
                required
              />
              <button
                type="submit"
                className="brutal-btn"
                style={{ backgroundColor: '#E0FF1C', color: '#111111', width: '100%' }}
                disabled={overrideLoading || !overridePrompt.trim()}
              >
                {overrideLoading ? 'Updating...' : 'Override Target Prompt'}
              </button>
            </form>
            {overrideSuccess && overrideResponse && (
              <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#e5e5e5', border: '2px solid #111111', fontSize: '10px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                <p style={{ color: '#1CFF3B', fontWeight: 'bold', margin: 0 }}>Challenge overridden successfully!</p>
                <p style={{ margin: 0 }}><strong>Image URL:</strong> {overrideResponse.image_url}</p>
                <p style={{ margin: 0 }}><strong>Imagen status:</strong> {overrideResponse.debug_info?.image_generation}</p>
                <p style={{ margin: 0 }}><strong>Embed status:</strong> {overrideResponse.debug_info?.embedding_generation}</p>
              </div>
            )}
            {overrideError && (
              <p className="mono-label" style={{ color: '#FF1CAE', fontSize: '10px', marginTop: '8px', margin: '8px 0 0 0' }}>
                Error: {overrideError}
              </p>
            )}
          </div>
        )}

        {/* Danger Zone: Session Reset */}
        <div style={{ borderTop: '4px dashed #111111', paddingTop: '16px', marginTop: '8px' }}>
          <h3 className="mono-label" style={{ color: '#FF1CAE', display: 'flex', alignItems: 'center', gap: '6px', margin: '0 0 8px 0' }}>
            <AlertTriangle size={18} />
            Danger Zone
          </h3>
          <p style={{ fontSize: '0.875rem', fontWeight: 600, margin: '0 0 12px 0' }}>
            Resetting your session will delete your current attempts and generate a new player identity.
          </p>
          <button
            onClick={() => {
              if (confirm('Are you sure you want to reset your player session? All progress for today will be lost.')) {
                onReset();
                onClose();
              }
            }}
            className="brutal-btn"
            style={{ backgroundColor: '#FF1CAE', color: '#FFFFFF', width: '100%' }}
          >
            <RotateCcw size={16} />
            Reset Session Data
          </button>
        </div>
      </div>
    </BaseModal>
  );
};
