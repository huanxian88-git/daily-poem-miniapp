const api = require('./api')
const userStore = require('../stores/user-store')
const { TOKEN_KEYS } = require('../utils/constants')

function login() {
  return new Promise(function (resolve, reject) {
    wx.login({
      success: function (loginRes) {
        if (!loginRes.code) {
          reject({ message: 'wx.login 获取 code 失败' })
          return
        }
        api.post('/auth/login', { code: loginRes.code }).then(function (res) {
          const tokenData = res.data || res
          userStore.setTokens(
            tokenData.access_token,
            tokenData.refresh_token
          )
          if (tokenData.user) {
            userStore.updateUserInfo(tokenData.user)
          }
          resolve(tokenData)
        }).catch(function (err) {
          reject(err)
        })
      },
      fail: function (err) {
        reject({ message: err.errMsg || 'wx.login 调用失败' })
      },
    })
  })
}

function refreshAccessToken() {
  const refreshToken = wx.getStorageSync(TOKEN_KEYS.REFRESH_TOKEN)
  if (!refreshToken) {
    return Promise.reject({ message: '无 refresh_token' })
  }
  return new Promise(function (resolve, reject) {
    wx.request({
      url: (getApp().globalData && getApp().globalData.apiBaseUrl || 'http://localhost:8000/api/v1') + '/auth/refresh',
      method: 'POST',
      header: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + refreshToken,
      },
      success: function (res) {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const tokenData = res.data.data || res.data
          userStore.setTokens(
            tokenData.access_token,
            tokenData.refresh_token || refreshToken
          )
          resolve(tokenData)
        } else {
          logout()
          reject({ code: res.statusCode, message: '刷新token失败' })
        }
      },
      fail: function (err) {
        reject({ message: err.errMsg || '刷新token网络错误' })
      },
    })
  })
}

function logout() {
  userStore.clearAll()
  const app = getApp()
  if (app && app.globalData) {
    app.globalData.isLoggedIn = false
    app.globalData.userInfo = null
  }
}

function ensureLogin() {
  if (userStore.isLoggedIn()) {
    return Promise.resolve()
  }
  return login()
}

module.exports = {
  login,
  refreshAccessToken,
  logout,
  ensureLogin,
}
