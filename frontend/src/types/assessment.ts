export interface AssessmentQuestion {
  id: string;
  question: string;
  options: string[];
}

export interface Assessment {
  lesson_id: string;
  curriculum_id: string;
  title: string;
  questions: AssessmentQuestion[];
}

export interface AssessmentAnswer {
  question_id: string;
  selected_option: number;
}

export interface AssessmentSubmission {
  answers: AssessmentAnswer[];
}

export interface AssessmentQuestionResult {
  question_id: string;
  selected_option: number;
  is_correct: boolean;
}

export interface AssessmentResult {
  lesson_id: string;
  curriculum_id: string;
  correct_answers: number;
  total_questions: number;
  score_percent: number;
  recommendation: string;
  question_results: AssessmentQuestionResult[];
}