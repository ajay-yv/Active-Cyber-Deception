const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-encoding',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
])

function sendJson(res, status, detail) {
  res.statusCode = status
  res.setHeader('content-type', 'application/json; charset=utf-8')
  res.end(JSON.stringify({ detail }))
}

function getBackendUrl(req) {
  const requestUrl = new URL(req.url || '/api', 'http://vercel.local')
  if (requestUrl.pathname !== '/api' && !requestUrl.pathname.startsWith('/api/')) {
    return null
  }

  const configuredUrl = process.env.HOSPITAL_API_BASE_URL?.trim()
  if (!configuredUrl) return undefined

  let base
  try {
    base = new URL(configuredUrl)
  } catch {
    throw new Error('HOSPITAL_API_BASE_URL must be a valid absolute URL.')
  }

  const isLocalHttp = base.protocol === 'http:' &&
    (base.hostname === 'localhost' || base.hostname === '127.0.0.1')
  if (base.protocol !== 'https:' && !isLocalHttp) {
    throw new Error('HOSPITAL_API_BASE_URL must use HTTPS outside local development.')
  }
  if (base.username || base.password || base.search || base.hash) {
    throw new Error('HOSPITAL_API_BASE_URL must not contain credentials, query parameters, or a fragment.')
  }
  if (base.pathname !== '/') {
    throw new Error('HOSPITAL_API_BASE_URL must be the backend origin without a path.')
  }
  const target = new URL(requestUrl.pathname + requestUrl.search, base.origin)
  return target
}

module.exports = async function hospitalApiProxy(req, res) {
  let targetUrl
  try {
    targetUrl = getBackendUrl(req)
  } catch (error) {
    sendJson(res, 500, error instanceof Error ? error.message : 'Invalid hospital API configuration.')
    return
  }

  if (targetUrl === null) {
    sendJson(res, 404, 'Unknown API route.')
    return
  }

  if (!targetUrl) {
    sendJson(
      res,
      503,
      'Hospital API is not configured. Set HOSPITAL_API_BASE_URL to the deployed backend HTTPS URL in Vercel.',
    )
    return
  }

  const headers = new Headers()
  for (const [name, value] of Object.entries(req.headers || {})) {
    if (value !== undefined && !HOP_BY_HOP_HEADERS.has(name.toLowerCase())) {
      headers.set(name, Array.isArray(value) ? value.join(', ') : String(value))
    }
  }

  const method = (req.method || 'GET').toUpperCase()
  const requestOptions = { method, headers, redirect: 'manual' }
  if (method !== 'GET' && method !== 'HEAD') {
    if (req.body !== undefined) {
      const body = Buffer.isBuffer(req.body) || typeof req.body === 'string'
        ? req.body
        : JSON.stringify(req.body)
      requestOptions.body = body
      if (!headers.has('content-type') && typeof req.body !== 'string' && !Buffer.isBuffer(req.body)) {
        headers.set('content-type', 'application/json')
      }
    } else {
      requestOptions.body = req
      requestOptions.duplex = 'half'
    }
  }

  let backendResponse
  try {
    backendResponse = await fetch(targetUrl, requestOptions)
  } catch {
    sendJson(res, 502, 'The hospital API backend could not be reached. Check HOSPITAL_API_BASE_URL and backend availability.')
    return
  }

  res.statusCode = backendResponse.status
  backendResponse.headers.forEach((value, name) => {
    if (!HOP_BY_HOP_HEADERS.has(name.toLowerCase())) res.setHeader(name, value)
  })
  res.setHeader('cache-control', 'no-store')
  res.setHeader('x-content-type-options', 'nosniff')
  const responseBody = Buffer.from(await backendResponse.arrayBuffer())
  res.end(responseBody)
}