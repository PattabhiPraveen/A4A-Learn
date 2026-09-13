const API_PREFIX = "/api";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(
    status: number,
    detail: string,
  ) {
    super(detail);

    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

interface ApiRequestOptions extends RequestInit {
  token?: string | null;
}

const AUTH_EXPIRED_EVENT =
  "a4a-auth-expired";

export function notifyAuthenticationExpired() {
  window.dispatchEvent(
    new CustomEvent(
      AUTH_EXPIRED_EVENT,
    ),
  );
}

export function getAuthenticationExpiredEventName() {
  return AUTH_EXPIRED_EVENT;
}

async function parseErrorDetail(
  response: Response,
): Promise<string> {
  try {
    const body = await response.json();

    if (
      typeof body?.detail === "string"
    ) {
      return body.detail;
    }

    if (
      Array.isArray(body?.detail)
    ) {
      return body.detail
        .map(
          (
            item: {
              msg?: string;
            },
          ) =>
            item.msg ??
            "Validation error",
        )
        .join(", ");
    }
  } catch {
    // Response did not contain JSON.
  }

  return `Request failed with status ${response.status}.`;
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    token,
    headers,
    ...requestOptions
  } = options;

  const requestHeaders =
    new Headers(headers);

  if (
    requestOptions.body &&
    !(requestOptions.body instanceof FormData) &&
    !requestHeaders.has(
      "Content-Type",
    )
  ) {
    requestHeaders.set(
      "Content-Type",
      "application/json",
    );
  }

  if (token) {
    requestHeaders.set(
      "Authorization",
      `Bearer ${token}`,
    );
  }

  const response =
    await fetch(
      `${API_PREFIX}${path}`,
      {
        ...requestOptions,
        headers: requestHeaders,
      },
    );

  if (!response.ok) {
    const detail =
      await parseErrorDetail(
        response,
      );

    if (
      response.status === 401 &&
      token
    ) {
      notifyAuthenticationExpired();
    }

    throw new ApiError(
      response.status,
      detail,
    );
  }

  if (
    response.status === 204
  ) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}