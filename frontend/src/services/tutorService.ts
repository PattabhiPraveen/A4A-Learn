import {
  apiRequest,
} from "./apiClient";

import type {
  RAGQuestion,
  RAGResponse,
} from "../types/tutor";


export async function askTutor(
  question: string,
  token: string,
): Promise<RAGResponse> {
  const payload: RAGQuestion = {
    question,
  };

  return apiRequest<RAGResponse>(
    "/rag/ask",
    {
      method: "POST",
      token,
      body: JSON.stringify(
        payload,
      ),
    },
  );
}