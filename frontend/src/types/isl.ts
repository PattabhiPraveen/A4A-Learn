export interface ISLPredictionResponse {
  label: string | null;
  predicted_label: string | null;
  confidence: number;
  accepted: boolean;
  threshold: number;
  model: string;
  hand_detected: boolean;
  message: string;

  attempt_id: string | null;
  target_letter: string | null;
  is_correct: boolean | null;

  workflow_decision: string;
  escalation_reason: string;
  requires_human_review: boolean;
  review_id: string | null;
}
