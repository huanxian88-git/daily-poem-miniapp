/**
 * API HTTP 基类
 * 功能：Token 鉴权拦截 + 自动刷新 + 错误处理 + 请求重试
 */

const BASE_URL = 'https://your-api.example.com/api/v1'  // 上线前替换

class ApiService {
  constructor() {
    this.baseUrl = BASE_URL
    this.isRefreshing = false
    this.refreshQueue = []
  }

  /**
   * 获取存储的 Access Token
   */
  getAccessToken() {
    return wx.getStorageSync('access_token')
  }

  /**
   * 获取存储的 Refresh Token
   */
  getRefreshToken() {
    return wx.getStorageSync('refresh_token')
  }

  /**
   * 保存 Token
   */
  saveTokens(accessToken, refreshToken) {
    wx.setStorageSync('access_token', accessToken)
    if (refreshToken) {
      wx.setStorageSync('refresh_token', refreshToken)
    }
  }

  /**
   * 清除 Token
   */
  clearTokens() {
    wx.removeStorageSync('access_token')
    wx.removeStorageSync('refresh_token')
  }

  /**
   * 刷新 Access Token
   */
  async refreshAccessToken() {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) return false

    try {
      const res = await new Promise((resolve, reject) => {
        wx.request({
          url: `${this.baseUrl}/auth/refresh`,
          method: 'POST',
          data: { refresh_token: refreshToken },
          success: resolve,
          fail: reject,
        })
      })

      if (res.statusCode === 200 && res.data.access_token) {
        this.saveTokens(res.data.access_token, refreshToken)
        return true
      }
    } catch (e) {
      console.error('Token 刷新失败:', e)
    }

    // 刷新失败，清除 Token
    this.clearTokens()
    return false
  }

  /**
   * 核心请求方法
   */
  request(options) {
    const { url, method = 'GET', data, header = {}, retry = true } = options

    return new Promise((resolve, reject) => {
      const doRequest = () => {
        const token = this.getAccessToken()

        wx.request({
          url: `${this.baseUrl}${url}`,
          method,
          data,
          header: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...header,
          },
          success: (res) => {
            if (res.statusCode === 401 && retry) {
              // Token 过期，尝试刷新后重试
              this.refreshAccessToken().then((success) => {
                if (success) {
                  // 刷新成功，用新 token 重试（但不再 retry）
                  this.request({ ...options, retry: false })
                    .then(resolve)
                    .catch(reject)
                } else {
                  // 刷新失败，跳转登录
                  this.clearTokens()
                  this.redirectToLogin()
                  reject(new Error('登录已过期，请重新登录'))
                }
              })
              return
            }

            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(res.data)
            } else {
              this.handleError(res)
              reject(res)
            }
          },
          fail: (err) => {
            wx.showToast({
              title: '网络异常，请稍后重试',
              icon: 'none',
            })
            reject(err)
          },
        })
      }

      doRequest()
    })
  }

  /**
   * 统一错误处理
   */
  handleError(res) {
    const statusCode = res.statusCode
    const msg = res.data?.detail || res.data?.message || '请求失败'

    switch (statusCode) {
      case 401:
        // 已在 request 中处理
        break
      case 403:
        wx.showToast({ title: '暂无权限', icon: 'none' })
        break
      case 429:
        wx.showToast({ title: '操作太频繁，请稍后再试', icon: 'none' })
        break
      case 500:
        wx.showToast({ title: '服务器异常，请稍后重试', icon: 'none' })
        break
      default:
        wx.showToast({ title: msg, icon: 'none' })
    }
  }

  /**
   * 跳转登录页
   */
  redirectToLogin() {
    const app = getApp()
    app.globalData.isLoggedIn = false
    app.globalData.userInfo = null
    wx.reLaunch({ url: '/pages/index/index' })
  }

  // --- 便捷方法 ---

  get(url, params) {
    const query = params
      ? '?' + Object.entries(params)
          .map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
          .join('&')
      : ''
    return this.request({ url: url + query, method: 'GET' })
  }

  post(url, data) {
    return this.request({ url, method: 'POST', data })
  }

  put(url, data) {
    return this.request({ url, method: 'PUT', data })
  }

  delete(url) {
    return this.request({ url, method: 'DELETE' })
  }
}

// 导出单例
const api = new ApiService()
export default api
