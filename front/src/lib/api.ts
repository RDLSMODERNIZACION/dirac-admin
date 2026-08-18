export const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'https://dirac-admin.onrender.com').replace(/\/$/, '');
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';
const AUTH_TOKEN_KEY = 'dirac_admin_token';

export function getAuthToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem(AUTH_TOKEN_KEY) || '';
}

export function setAuthToken(token: string) {
  if (typeof window !== 'undefined') localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearAuthToken() {
  if (typeof window !== 'undefined') localStorage.removeItem(AUTH_TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) { super(message); this.status = status; }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');
  if (API_KEY) headers.set('X-API-Key', API_KEY);
  const authToken = getAuthToken();
  if (authToken) headers.set('Authorization', `Bearer ${authToken}`);
  const res = await fetch(`${API_URL}${path}`, { ...init, headers, cache: 'no-store' });
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    clearAuthToken();
    if (typeof window !== 'undefined') window.dispatchEvent(new Event('dirac-auth-required'));
  }
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      const rawDetail = body?.detail ?? body;
      if (typeof rawDetail === 'string') detail = rawDetail;
      else if (Array.isArray(rawDetail)) {
        detail = rawDetail.map((item: any) => item?.msg || JSON.stringify(item)).join(' · ');
      } else if (rawDetail && typeof rawDetail === 'object') {
        detail = rawDetail.message || rawDetail.msg || JSON.stringify(rawDetail);
      }
    } catch {}
    throw new ApiError(detail, res.status);
  }
  if (res.status === 204) return undefined as T;
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T = any>(path: string, data: Record<string, any>) => request<T>(path, { method: 'POST', body: JSON.stringify(data) }),
  upload: <T = any>(path: string, form: FormData) => request<T>(path, { method: 'POST', body: form }),
  list: <T = any>(table: string, params = '') => request<T[]>(`/api/${table}${params}`),
  create: <T = any>(table: string, data: Record<string, any>) => request<T>(`/api/${table}`, { method: 'POST', body: JSON.stringify(data) }),
  update: <T = any>(table: string, id: string, data: Record<string, any>) => request<T>(`/api/${table}/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  remove: (table: string, id: string) => request<any>(`/api/${table}/${id}`, { method: 'DELETE' })
};
