export interface ProgressSummary {
  user_id: string;
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  accuracy_percent: number;
}

export interface LetterPerformance {
  target_letter: string;
  total_attempts: number;
  correct_attempts: number;
  incorrect_attempts: number;
  accepted_attempts: number;
  accuracy_percent: number;
  acceptance_rate_percent: number;
  average_confidence: number | null;
  weak_candidate: boolean;
}

export interface WeakLetter {
  target_letter: string;
  total_attempts: number;
  accuracy_percent: number;
  average_confidence: number | null;
  reason: string;
}

export interface RecentAttempt {
  id: string;
  target_letter: string;
  predicted_letter: string | null;
  confidence: number | null;
  accepted: boolean;
  is_correct: boolean;
  created_at: string;
}

export interface ProgressAnalytics {
  user_id: string;
  overall: ProgressSummary;
  letters_attempted: number;
  letter_performance: LetterPerformance[];
  weak_letters: WeakLetter[];
  weak_letter_count: number;
  low_confidence_attempts: number;
  low_confidence_threshold: number;
  recent_attempts: RecentAttempt[];
}

export interface LessonProgress {
  lesson_id: string;
  curriculum_id: string;
  assessment_attempts: number;
  latest_score_percent: number | null;
  latest_recommendation: string | null;
  best_score_percent: number | null;
  completed: boolean;
  latest_attempt_at: string | null;
}