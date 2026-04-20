type JsonBody = Record<string, unknown>

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers ?? {}) },
    ...init,
  })
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${url}: ${text}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  get<T>(url: string): Promise<T> {
    return request<T>(url)
  },

  post<T>(url: string, body: JsonBody): Promise<T> {
    return request<T>(url, {
      method: 'POST',
      body: JSON.stringify(body),
    })
  },
}
