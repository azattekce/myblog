export interface Paged<T> {
  items: T[];
  page: number;
  size: number;
  total: number;
  pages: number;
}

export interface ProblemDetails {
  type?: string;
  title?: string;
  status: number;
  detail: string;
  code: string;
  correlation_id?: string;
  errors?: { field: string; message: string }[];
}
