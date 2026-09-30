import {
  apiRequest,
} from "./apiClient";

import type {
  LearningLessonDetail,
  LearningLessonSummary,
} from "../types/learning";


export async function getLearningLessons(
  token: string,
): Promise<LearningLessonSummary[]> {
  return apiRequest<
    LearningLessonSummary[]
  >(
    "/learning/lessons",
    {
      method: "GET",
      token,
    },
  );
}


export async function getLearningLesson(
  lessonId: string,
  token: string,
): Promise<LearningLessonDetail> {
  return apiRequest<
    LearningLessonDetail
  >(
    `/learning/lessons/${encodeURIComponent(
      lessonId,
    )}`,
    {
      method: "GET",
      token,
    },
  );
}