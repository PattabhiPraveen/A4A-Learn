import {
  apiRequest,
} from "./apiClient";

import type {
  LessonProgress,
  ProgressAnalytics,
  ProgressSummary,
} from "../types/progress";


export async function getMyProgress(
  token: string,
): Promise<ProgressSummary> {
  return apiRequest<ProgressSummary>(
    "/progress/me",
    {
      method: "GET",
      token,
    },
  );
}


export async function getMyProgressAnalytics(
  token: string,
  recentLimit = 10,
): Promise<ProgressAnalytics> {
  return apiRequest<ProgressAnalytics>(
    `/progress/me/analytics?recent_limit=${recentLimit}`,
    {
      method: "GET",
      token,
    },
  );
}


export async function getLessonProgress(
  lessonId: string,
  token: string,
): Promise<LessonProgress> {
  return apiRequest<LessonProgress>(
    `/progress/lessons/${encodeURIComponent(
      lessonId,
    )}`,
    {
      method: "GET",
      token,
    },
  );
}