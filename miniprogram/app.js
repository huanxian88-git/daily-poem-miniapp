App({
  onLaunch() {
    console.log('每日背诗启动')
    // 检查登录状态
    this.checkLogin()
  },

  globalData: {
    userInfo: null,
    isLoggedIn: false,
  },

  checkLogin() {
    const token = wx.getStorageSync('access_token')
    if (token) {
      this.globalData.isLoggedIn = true
    }
  },
})
