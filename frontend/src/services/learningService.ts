import type {
  LearningLesson,
} from "../types/learning";

const lessons: LearningLesson[] = [
  {
    id: "lesson-1",
    title: "Introduction to Artificial Intelligence",
    description:
      "Learn the basic idea of artificial intelligence and how it is used.",
    topic: "Artificial Intelligence",
    content:
      "Artificial Intelligence helps computers perform tasks that normally require human intelligence. These tasks can include understanding information, recognising patterns, answering questions, and supporting decisions.",
  },
  {
    id: "lesson-2",
    title: "Machine Learning Basics",
    description:
      "Understand how computers can learn patterns from examples and data.",
    topic: "Machine Learning",
    content:
      "Machine Learning is an area of artificial intelligence where computer systems learn patterns from data. A trained model can use those patterns to make predictions or classifications on new information.",
  },
  {
    id: "lesson-3",
    title: "Responsible Artificial Intelligence",
    description:
      "Learn why fairness, safety, privacy and accountability matter when using AI.",
    topic: "Responsible AI",
    content:
      "Responsible AI focuses on developing and using artificial intelligence in ways that consider fairness, reliability and safety, privacy and security, inclusiveness, transparency, and accountability.",
  },
];

export function getLearningLessons(): LearningLesson[] {
  return lessons;
}