const ACCESS_CODE_KEY = 'kf_access_code'

export function getAccessCode(): string {
  return localStorage.getItem(ACCESS_CODE_KEY) || ''
}

export function setAccessCode(code: string): void {
  localStorage.setItem(ACCESS_CODE_KEY, code)
}

export function clearAccessCode(): void {
  localStorage.removeItem(ACCESS_CODE_KEY)
}

export function appendAccessCode(url: string): string {
  const code = getAccessCode()
  if (!code || !url.startsWith('/static/uploads')) return url

  const [withoutHash, hash = ''] = url.split('#')
  const separator = withoutHash.includes('?') ? '&' : '?'
  const withCode = `${withoutHash}${separator}kf_access_code=${encodeURIComponent(code)}`
  return hash ? `${withCode}#${hash}` : withCode
}
