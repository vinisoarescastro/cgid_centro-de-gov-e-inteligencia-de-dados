const API = 'http://localhost:8000'

function getHeaders(extra = {}) {
  const user = JSON.parse(sessionStorage.getItem('cgid_user') || '{}')
  const headers = { 'Content-Type': 'application/json', ...extra }
  if (user.id) headers['X-Usuario-Id'] = user.id
  return headers
}

export function apiFetch(path, options = {}) {
  const { body, ...rest } = options
  return fetch(`${API}${path}`, {
    ...rest,
    headers: getHeaders(rest.headers),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })
}

export default API
