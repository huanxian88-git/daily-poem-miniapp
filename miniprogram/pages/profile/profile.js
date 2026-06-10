// pages/profile/profile.js - 我的Tab

import userStore from '../../stores/user-store'

Page({
  data: {
    isLoggedIn: false,
    userProfile: null,
  },

  onShow() {
    userStore.bind(this)
    this.setData({
      isLoggedIn: userStore.data.isLoggedIn,
      userProfile: userStore.data.profile,
    })
  },

  onHide() {
    userStore.unbind(this)
  },

  _userStoreUpdate(newData) {
    this.setData({
      isLoggedIn: newData.isLoggedIn,
      userProfile: newData.profile,
    })
  },

  async handleLogin() {
    const result = await userStore.login()
    if (result.success) {
      wx.showToast({ title: '登录成功', icon: 'success' })
      if (result.isNewUser) {
        wx.navigateTo({ url: '/pages/onboarding/onboarding' })
      }
    } else {
      wx.showToast({ title: '登录失败', icon: 'none' })
    }
  },
})
