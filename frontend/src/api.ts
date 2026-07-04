import type { DailyChallengeResponse, GameSession } from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Retrieves the persisted player ID from localStorage, or generates
 * a new unique player ID if none exists.
 */
export function getPlayerId(): string {
  let playerId = localStorage.getItem('prompt_guesser_player_id');
  if (!playerId) {
    const randomSuffix = Math.random().toString(36).substring(2, 10);
    playerId = `pg_player_${randomSuffix}`;
    localStorage.setItem('prompt_guesser_player_id', playerId);
  }
  return playerId;
}

/**
 * Prepend backend base URL to relative image paths.
 */
export function formatImageUrl(url: string): string {
  if (!url) return '';
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  // Ensure we don't duplicate slashes
  const cleanBase = API_BASE_URL.replace(/\/+$/, '');
  const cleanPath = url.replace(/^\/+/, '');
  return `${cleanBase}/${cleanPath}`;
}

/**
 * Fetches today's challenge details and current active session.
 */
export async function getTodayChallenge(): Promise<DailyChallengeResponse> {
  const playerId = getPlayerId();
  const response = await fetch(`${API_BASE_URL}/api/v1/gameplay/today`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-Player-ID': playerId,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to retrieve today\'s challenge.');
  }

  const data: DailyChallengeResponse = await response.json();
  // Format the image URL
  data.image_url = formatImageUrl(data.image_url);
  return data;
}

/**
 * Submits a new guess attempt.
 */
export async function submitGuess(guessText: string): Promise<GameSession> {
  const playerId = getPlayerId();
  const response = await fetch(`${API_BASE_URL}/api/v1/gameplay/guess`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Player-ID': playerId,
    },
    body: JSON.stringify({ guess_text: guessText }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to submit guess.');
  }

  return response.json();
}

/**
 * Override today's daily challenge target prompt (Developer Option - Dev Mode only).
 */
export async function overrideChallengePrompt(promptText: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/v1/gameplay/debug/override-challenge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ prompt: promptText }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'Failed to override challenge.');
  }

  return response.json();
}

