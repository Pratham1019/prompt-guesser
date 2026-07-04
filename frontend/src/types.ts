export interface GuessAttempt {
  id: number;
  game_session_id: number;
  attempt_number: number;
  guess_text: string;
  similarity_score: number;
  evaluation_feedback: string;
  created_at: string;
}

export interface GameSession {
  id: number;
  player_id: string;
  prompt_challenge_id: number;
  status: 'active' | 'completed';
  attempts_used: number;
  attempts_remaining: number;
  best_score: number;
  created_at: string;
  completed_at: string | null;
  is_completed: boolean;
  revealed_prompt: string | null;
  attempts: GuessAttempt[];
}

export interface DailyChallengeResponse {
  challenge_id: number;
  image_url: string;
  publish_date: string;
  session: GameSession;
}
