import {
  clearAuthSession,
  getAuthSession,
  updateAuthTokens,
} from "@/lib/auth/session";

import type {
  RefreshTokenResponse,
} from "@/types/auth";

const DIRECT_BACKEND_API =
  "http://127.0.0.1:8001/api/v1";

const CONFIGURED_API_BASE =
  process.env
    .NEXT_PUBLIC_API_BASE_URL ??
  "/backend";

export type ApiQueryValue =
  | string
  | number
  | boolean
  | null
  | undefined;

export interface ApiRequestOptions {
  responseType?: "json" | "blob";
  auth?: boolean;

  retryOnUnauthorized?: boolean;

  token?: string | null;

  query?: Record<
    string,
    ApiQueryValue
  >;

  headers?: HeadersInit;
}

export interface ApiErrorPayload {
  detail?: unknown;

  message?: string;

  error?: unknown;

  [key: string]: unknown;
}

export class ApiError extends Error {
  readonly status: number;

  readonly payload:
    | ApiErrorPayload
    | null;

  constructor(
    message: string,
    status: number,
    payload:
      | ApiErrorPayload
      | null,
  ) {
    super(message);

    this.name = "ApiError";
    this.status = status;
    this.payload = payload;
  }
}

let refreshPromise:
  | Promise<string>
  | null = null;

function normalizeBase(
  value: string,
) {
  return value.replace(
    /\/+$/,
    "",
  );
}

function buildUrl(
  path: string,
  query?: Record<
    string,
    ApiQueryValue
  >,
): string {
  if (
    path.startsWith(
      "http://",
    ) ||
    path.startsWith(
      "https://",
    )
  ) {
    const absoluteUrl =
      new URL(path);

    appendQuery(
      absoluteUrl,
      query,
    );

    return absoluteUrl.toString();
  }

  const normalizedPath =
    path.startsWith("/")
      ? path
      : `/${path}`;

  const configuredBase =
    normalizeBase(
      CONFIGURED_API_BASE,
    );

  let url: URL;

  if (
    configuredBase.startsWith(
      "http://",
    ) ||
    configuredBase.startsWith(
      "https://",
    )
  ) {
    url = new URL(
      `${configuredBase}${normalizedPath}`,
    );
  } else if (
    typeof window !==
    "undefined"
  ) {
    url = new URL(
      `${configuredBase}${normalizedPath}`,
      window.location.origin,
    );
  } else {
    url = new URL(
      `${DIRECT_BACKEND_API}${normalizedPath}`,
    );
  }

  appendQuery(
    url,
    query,
  );

  return url.toString();
}

function appendQuery(
  url: URL,
  query?: Record<
    string,
    ApiQueryValue
  >,
) {
  if (!query) {
    return;
  }

  for (const [
    key,
    value,
  ] of Object.entries(query)) {
    if (
      value === null ||
      value === undefined ||
      value === ""
    ) {
      continue;
    }

    url.searchParams.set(
      key,
      String(value),
    );
  }
}

async function parseResponseBody(
  response: Response,
): Promise<unknown> {
  const contentType =
    response.headers.get(
      "content-type",
    ) ?? "";

  if (
    contentType.includes(
      "application/json",
    )
  ) {
    try {
      return await response.json();
    } catch {
      return null;
    }
  }

  try {
    const text =
      await response.text();

    return text || null;
  } catch {
    return null;
  }
}

function extractErrorMessage(
  body: unknown,
  fallback: string,
): string {
  if (
    typeof body === "string" &&
    body.trim()
  ) {
    return body;
  }

  if (
    !body ||
    typeof body !== "object"
  ) {
    return fallback;
  }

  const payload =
    body as Record<
      string,
      unknown
    >;

  if (
    typeof payload.message ===
      "string" &&
    payload.message.trim()
  ) {
    return payload.message;
  }

  if (
    typeof payload.detail ===
    "string"
  ) {
    return payload.detail;
  }

  /*
   * WorkforceOS structured error:
   *
   * {
   *   error: {
   *     code: "...",
   *     message: "...",
   *     request_id: "..."
   *   }
   * }
   */
  if (
    payload.error &&
    typeof payload.error ===
      "object"
  ) {
    const errorObject =
      payload.error as Record<
        string,
        unknown
      >;

    if (
      typeof errorObject.message ===
        "string" &&
      errorObject.message.trim()
    ) {
      return errorObject.message;
    }
  }

  if (
    typeof payload.error ===
      "string" &&
    payload.error.trim()
  ) {
    return payload.error;
  }

  /*
   * FastAPI validation errors.
   */
  if (
    Array.isArray(
      payload.detail,
    )
  ) {
    const messages =
      payload.detail
        .map((item) => {
          if (
            !item ||
            typeof item !==
              "object"
          ) {
            return null;
          }

          const record =
            item as Record<
              string,
              unknown
            >;

          if (
            typeof record.msg ===
              "string"
          ) {
            return record.msg;
          }

          return null;
        })
        .filter(
          (
            value,
          ): value is string =>
            Boolean(value),
        );

    if (
      messages.length > 0
    ) {
      return messages.join(
        " ",
      );
    }
  }

  return fallback;
}

async function refreshAccessToken():
  Promise<string> {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise =
    (async () => {
      const session =
        getAuthSession();

      if (
        !session?.refreshToken
      ) {
        clearAuthSession();

        throw new ApiError(
          "Authentication session is unavailable.",
          401,
          null,
        );
      }

      let response: Response;

      try {
        response =
          await fetch(
            buildUrl(
              "/auth/refresh",
            ),
            {
              method: "POST",

              headers: {
                Accept:
                  "application/json",

                "Content-Type":
                  "application/json",
              },

              body:
                JSON.stringify({
                  refresh_token:
                    session.refreshToken,
                }),

              cache: "no-store",
            },
          );
      } catch {
        throw new ApiError(
          "Unable to connect to Workforce OS API.",
          0,
          null,
        );
      }

      const body =
        await parseResponseBody(
          response,
        );

      if (!response.ok) {
        clearAuthSession();

        throw new ApiError(
          extractErrorMessage(
            body,
            "Your session has expired. Please sign in again.",
          ),

          response.status,

          body &&
          typeof body ===
            "object"
            ? (body as ApiErrorPayload)
            : null,
        );
      }

      const tokens =
        body as RefreshTokenResponse;

      if (
        !tokens.access_token ||
        !tokens.refresh_token
      ) {
        clearAuthSession();

        throw new ApiError(
          "The authentication server returned invalid refresh tokens.",
          500,
          null,
        );
      }

      updateAuthTokens(
        tokens,
      );

      return tokens.access_token;
    })();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  options: ApiRequestOptions = {},
): Promise<T> {
  const {
    auth = true,

    retryOnUnauthorized =
      true,

    token,

    query,

    headers:
      optionHeaders,
  } = options;

  const headers =
    new Headers(
      init.headers,
    );

  if (optionHeaders) {
    const extraHeaders =
      new Headers(
        optionHeaders,
      );

    extraHeaders.forEach(
      (
        value,
        key,
      ) => {
        headers.set(
          key,
          value,
        );
      },
    );
  }

  headers.set(
    "Accept",
    "application/json",
  );

  if (
    init.body !== undefined &&
    init.body !== null &&
    !headers.has(
      "Content-Type",
    ) &&
    !(
      typeof FormData !==
        "undefined" &&
      init.body instanceof
        FormData
    )
  ) {
    headers.set(
      "Content-Type",
      "application/json",
    );
  }

  if (auth) {
    const accessToken =
      token ??
      getAuthSession()
        ?.accessToken;

    if (accessToken) {
      headers.set(
        "Authorization",
        `Bearer ${accessToken}`,
      );
    }
  }

  const url =
    buildUrl(
      path,
      query,
    );

  let response: Response;

  try {
    response =
      await fetch(
        url,
        {
          ...init,

          headers,

          cache:
            init.cache ??
            "no-store",
        },
      );
  } catch {
    throw new ApiError(
      "Unable to connect to Workforce OS API.",
      0,
      null,
    );
  }

  if (
    response.status === 401 &&
    auth &&
    retryOnUnauthorized
  ) {
    const newAccessToken =
      await refreshAccessToken();

    headers.set(
      "Authorization",
      `Bearer ${newAccessToken}`,
    );

    try {
      response =
        await fetch(
          url,
          {
            ...init,

            headers,

            cache:
              init.cache ??
              "no-store",
          },
        );
    } catch {
      throw new ApiError(
        "Unable to connect to Workforce OS API.",
        0,
        null,
      );
    }
  }

  if (response.ok && options.responseType === "blob") {
    return await response.blob() as T;
  }

  const body =
    await parseResponseBody(
      response,
    );

  if (!response.ok) {
    throw new ApiError(
      extractErrorMessage(
        body,
        `Request failed with status ${response.status}.`,
      ),

      response.status,

      body &&
      typeof body ===
        "object"
        ? (body as ApiErrorPayload)
        : null,
    );
  }

  if (
    response.status ===
    204
  ) {
    return undefined as T;
  }

  return body as T;
}

function withJsonBody(
  body: unknown,
): string {
  return JSON.stringify(
    body,
  );
}

export const api = {
  postForm<T>(path: string, body: FormData, options: ApiRequestOptions = {}): Promise<T> {
    return request<T>(path, { method: "POST", body }, options);
  },

  request<T>(
    path: string,
    init: RequestInit = {},
    options: ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(path, init, options);
  },

  get<T>(
    path: string,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "GET",
      },

      options,
    );
  },

  post<T>(
    path: string,
    body?: unknown,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "POST",

        body:
          body === undefined
            ? undefined
            : withJsonBody(
                body,
              ),
      },

      options,
    );
  },

  patch<T>(
    path: string,
    body?: unknown,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "PATCH",

        body:
          body === undefined
            ? undefined
            : withJsonBody(
                body,
              ),
      },

      options,
    );
  },

  put<T>(
    path: string,
    body?: unknown,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "PUT",

        body:
          body === undefined
            ? undefined
            : withJsonBody(
                body,
              ),
      },

      options,
    );
  },

  delete<T>(
    path: string,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "DELETE",
      },

      options,
    );
  },

  deleteWithBody<T>(
    path: string,
    body: unknown,
    options:
      ApiRequestOptions = {},
  ): Promise<T> {
    return request<T>(
      path,

      {
        method: "DELETE",

        body:
          withJsonBody(
            body,
          ),
      },

      options,
    );
  },
};
