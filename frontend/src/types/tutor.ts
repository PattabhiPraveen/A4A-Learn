export interface RAGQuestion {
  question: string;

  // Optional governed lesson context.
  // This identifier is sent only after the
  // frontend has successfully validated the
  // lesson through the learning API.
  lesson_id?: string;
}


export type RAGSourceType =
  | "curriculum"
  | "web";


export interface RAGSource {
  title: string;
  source: string | null;

  // Curriculum sources may contain the real vector
  // retrieval distance. Web evidence does not have
  // an equivalent distance measurement.
  distance: number | null;

  // Identifies the provenance of the evidence.
  source_type: RAGSourceType;
}


export interface RAGResponse {
  question: string;
  answer: string;
  grounded: boolean;
  sources: RAGSource[];

  workflow_decision: string;
  escalation_reason: string;

  requires_human_review: boolean;

  review_id: string | null;
}