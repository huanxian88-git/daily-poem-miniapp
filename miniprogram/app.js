import userStore from './stores/user-store'

App({
  onLaunch() {
    console.log('天天半首诗启动')
    // 检查登录状态
    this.checkLogin()
  },

  globalData: {
    userInfo: null,
    isLoggedIn: false,
  },

  async checkLogin() {
    const token = wx.getStorageSync('access_token')
    if (token) {
      this.globalData.isLoggedIn = true
      userStore.set({ isLoggedIn: true })
    }
  },
})
