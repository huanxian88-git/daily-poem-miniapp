const TOKEN_KEYS = {
  ACCESS_TOKEN: 'access_token',
  REFRESH_TOKEN: 'refresh_token',
}

const ERROR_CODES = {
  TOKEN_EXPIRED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  SERVER_ERROR: 500,
  NETWORK_ERROR: -1,
  TIMEOUT: -2,
}

const APP_CONFIG = {
  APP_ID: 'wxcb715f5de1dee100',
  API_BASE_URL: 'http://localhost:8000/api/v1',
  REQUEST_TIMEOUT: 10000,
  MAX_RETRY: 2,
  MAX_REFRESH_RETRY: 1,
}

module.exports = {
  TOKEN_KEYS,
  ERROR_CODES,
  APP_CONFIG,
}
