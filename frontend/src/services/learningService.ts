import {
  apiRequest,
} from "./apiClient";

import type {
  ISLLessonManifest,
} from "../types/islContent";

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


export async function getLearningLessonISL(
  lessonId: string,
  token: string,
): Promise<ISLLessonManifest> {
  return apiRequest<
    ISLLessonManifest
  >(
    `/learning/lessons/${encodeURIComponent(
      lessonId,
    )}/isl`,
    {
      method: "GET",
      token,
    },
  );
}