import { API_BASE_URL, USE_MOCK_API } from '@/config/endpoints'
import { ApiErrorException, type ApiResponse, type RequestOptions } from '@/types/api'

function buildUrl(path: string, params?: RequestOptions['params']): string {
  const url = new URL(path, API_BASE_URL)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value))
      }
    })
  }
  return url.toString()
}

function buildHeaders(headers?: Record<string, string>): Headers {
  const h = new Headers({
    'Content-Type': 'application/json',
    Accept: 'application/json',
    ...headers,
  })
  return h
}

/**
 * Core HTTP client for the NOETRA API.
 *
 * - Configurable base URL via VITE_API_BASE_URL
 * - Standardized error handling via ApiErrorException
 * - Request cancellation via AbortSignal
 * - Mock-mode flag (VITE_USE_MOCK_API) for future development
 *
 * No actual backend calls are made yet — this is the foundation layer.
 */
export const apiClient = {
  baseUrl: API_BASE_URL,
  useMock: USE_MOCK_API,

  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const { method = 'GET', body, params, signal, headers } = options

    const url = buildUrl(path, params)
    const requestHeaders = buildHeaders(headers)

    let response: Response
    try {
      response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body !== undefined ? JSON.stringify(body) : undefined,
        signal,
      })
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        throw err
      }
      throw new ApiErrorException({
        status: 0,
        message: 'Network error — could not reach the server.',
      })
    }

    const contentType = response.headers.get('content-type') ?? ''
    const isJson = contentType.includes('application/json')

    if (!response.ok) {
      const errorBody = isJson ? await response.json().catch(() => null) : null
      throw new ApiErrorException({
        status: response.status,
        message: errorBody?.detail ?? errorBody?.message ?? response.statusText,
        code: errorBody?.code,
        details: errorBody,
      })
    }

    if (response.status === 204 || !isJson) {
      return undefined as T
    }

    const data = (await response.json()) as ApiResponse<T> | T
    // Backend may return a wrapped { data } envelope or the raw resource.
    if (data && typeof data === 'object' && 'data' in data) {
      return (data as ApiResponse<T>).data
    }
    return data as T
  },

  get<T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...options, method: 'GET' })
  },

  post<T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...options, method: 'POST', body })
  },

  put<T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...options, method: 'PUT', body })
  },

  patch<T>(path: string, body?: unknown, options?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...options, method: 'PATCH', body })
  },

  delete<T>(path: string, options?: Omit<RequestOptions, 'method' | 'body'>) {
    return this.request<T>(path, { ...options, method: 'DELETE' })
  },
}

/** Helper to create an AbortController for cancelling in-flight requests. */
export function createAbortController(): AbortController {
  return new AbortController()
}
