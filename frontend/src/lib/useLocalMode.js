// Hook that detects if running from scanllm ui (localhost:5787) vs SaaS
export function useLocalMode() {
  const isLocal = window.location.port === '5787' || window.location.hostname === 'localhost';
  const apiBase = isLocal ? '' : (process.env.REACT_APP_API_URL || '');
  return { isLocal, apiBase };
}
