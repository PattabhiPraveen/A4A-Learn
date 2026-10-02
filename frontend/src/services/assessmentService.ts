import {
  apiRequest,
} from "./apiClient";

import type {
  Assessment,
  AssessmentResult,
  AssessmentSubmission,
} from "../types/assessment";


export async function getAssessment(
  lessonId: string,
  token: string,
): Promise<Assessment> {
  return apiRequest<Assessment>(
    `/assessments/lessons/${encodeURIComponent(
      lessonId,
    )}`,
    {
      method: "GET",
      token,
    },
  );
}


export async function submitAssessment(
  lessonId: string,
  submission: AssessmentSubmission,
  token: string,
): Promise<AssessmentResult> {
  return apiRequest<AssessmentResult>(
    `/assessments/lessons/${encodeURIComponent(
      lessonId,
    )}/submit`,
    {
      method: "POST",
      token,
      body: JSON.stringify(
        submission,
      ),
    },
  );
}