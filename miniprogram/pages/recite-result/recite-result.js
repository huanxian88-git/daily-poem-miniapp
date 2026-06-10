// pages/recite-result/recite-result.js - 背诵结果页

import api from '../../services/api'

Page({
  data: {
    loading: true,
    poemId: null,
    poemTitle: '',
    recitationId: null,
    result: null,
  },

  onLoad(options) {
    const poemId = options.poemId
    const title = options.title ? decodeURIComponent(options.title) : ''
    const recitationId = options.recitation_id || null

    this.setData({ poemId, poemTitle: title, recitationId })
    this.fetchResult()
  },

  /**
   * 获取背诵结果
   */
  async fetchResult() {
    this.setData({ loading: true })
    try {
      const id = this.data.recitationId || this.data.poemId
      const res = await api.get('/recite/' + id + '/result')
      this.setData({
        result: res,
        loading: false,
      })
    } catch (e) {
      // Mock数据
      this.setData({
        result: {
          mastered: true,
          fillScore: 80,
          sortScore: 75,
          voiceScore: 90,
          totalCorrectChars: 18,
          wrongDetails: [
            { correct: '明', wrong: '月' },
          ],
        },
        loading: false,
      })
    }
  },

  /**
   * 返回
   */
  goBack() {
    wx.navigateBack({ delta: 1 })
  },

  /**
   * 回到首页
   */
  goHome() {
    wx.switchTab({ url: '/pages/index/index' })
  },

  /**
   * 重新挑战
   */
  retry() {
    wx.redirectTo({
      url: `/pages/recite-check/recite-check?poemId=${this.data.poemId}&title=${encodeURIComponent(this.data.poemTitle)}`
    })
  },
})
