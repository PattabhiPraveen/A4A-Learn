export interface LearningLessonSummary {
  id: string;
  curriculum_id: string;
  title: string;
  course: string;
  level: string;
  sequence: number;
  estimated_minutes: number;
  topic: string;
  description: string;
}

export interface LearningLessonDetail extends LearningLessonSummary {
  content: string;
}