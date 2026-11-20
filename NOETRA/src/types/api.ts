/* Standardized API response shapes and error types. */

export interface ApiError {
  status: number
  message: string
  code?: string
  details?: unknown
}

export interface ApiResponse<T> {
  data: T
  meta?: {
    total?: number
    page?: number
    pageSize?: number
  }
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export class ApiErrorException extends Error implements ApiError {
  status: number
  code?: string
  details?: unknown

  constructor({ status, message, code, details }: ApiError) {
    super(message)
    this.name = 'ApiErrorException'
    this.status = status
    this.code = code
    this.details = details
  }
}

export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

export interface RequestOptions {
  method?: HttpMethod
  body?: unknown
  params?: Record<string, string | number | boolean | undefined>
  signal?: AbortSignal
  headers?: Record<string, string>
}
