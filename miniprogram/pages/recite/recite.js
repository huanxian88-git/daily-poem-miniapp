// pages/recite/recite.js - 吟诵Tab：背诵管理

Page({
  data: {
    activeRecitations: [],
    todayRecited: false,
    loading: false,
  },

  onShow() {
    this.loadRecitations()
  },

  async loadRecitations() {
    this.setData({ loading: true })
    // TODO: 接入 API
    this.setData({ loading: false })
  },
})
