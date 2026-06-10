// pages/recite/recite.js - 吟诵Tab升级

import api from '../../services/api'

Page({
  data: {
    loading: true,
    recitations: [],
  },

  onShow() {
    this.loadRecitations()
  },

  /**
   * 加载在背列表
   */
  async loadRecitations() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/recite/list')
      this.setData({
        recitations: res.items || res || [],
        loading: false,
      })
    } catch (e) {
      // Mock数据
      this.setData({
        recitations: [
          {
            recitation_id: 'r1',
            poem_id: '1',
            title: '静夜思',
            dynasty: '唐',
            author: '李白',
            fill_score: 80,
            sort_score: 75,
            voice_score: null,
          },
          {
            recitation_id: 'r2',
            poem_id: '2',
            title: '春晓',
            dynasty: '唐',
            author: '孟浩然',
            fill_score: null,
            sort_score: null,
            voice_score: null,
          },
        ],
        loading: false,
      })
    }
  },

  /**
   * 进入背诵检查
   */
  goToReciteCheck(e) {
    const { poemId, title } = e.currentTarget.dataset
    wx.navigateTo({
      url: `/pages/recite-check/recite-check?poemId=${poemId}&title=${encodeURIComponent(title)}`
    })
  },

  /**
   * 去首页选诗
   */
  goToIndex() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.loadRecitations().finally(() => {
      wx.stopPullDownRefresh()
    })
  },
})
