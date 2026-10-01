import {
  apiRequest,
} from "./apiClient";

import type {
  ISLPredictionResponse,
} from "../types/isl";


export async function predictISLAlphabet(
  targetLetter: string,
  file: File,
  token: string,
): Promise<ISLPredictionResponse> {
  const formData = new FormData();

  formData.append(
    "target_letter",
    targetLetter,
  );

  formData.append(
    "file",
    file,
  );

  return apiRequest<ISLPredictionResponse>(
    "/isl/predict",
    {
      method: "POST",
      token,
      body: formData,
    },
  );
}
