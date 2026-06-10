// pages/review/review.js - 临帖（复习）页

import api from '../../services/api'

Page({
  data: {
    loading: true,
    queue: [],
  },

  onShow() {
    this.fetchReviewQueue()
  },

  /**
   * 获取复习队列
   */
  async fetchReviewQueue() {
    this.setData({ loading: true })
    try {
      const res = await api.get('/review/queue')
      this.setData({
        queue: res.items || res || [],
        loading: false,
      })
    } catch (e) {
      // Mock数据
      this.setData({
        queue: [
          {
            poem_id: '1',
            title: '静夜思',
            dynasty: '唐',
            author: '李白',
            next_review_date: '2026-06-08',
            urgency: 'high',
          },
          {
            poem_id: '2',
            title: '春晓',
            dynasty: '唐',
            author: '孟浩然',
            next_review_date: '2026-06-10',
            urgency: 'normal',
          },
        ],
        loading: false,
      })
    }
  },

  /**
   * 查看诗词详情（鉴赏模式）
   */
  viewPoem(e) {
    const poemId = e.currentTarget.dataset.poemId
    wx.navigateTo({
      url: `/pages/poem/poem?poemId=${poemId}`
    })
  },

  /**
   * 自评：简单/合适/困难
   */
  async assessPoem(e) {
    const poemId = e.currentTarget.dataset.poemId
    const level = e.currentTarget.dataset.level

    try {
      await api.post('/review/' + poemId + '/done', { assessment: level })
      wx.showToast({
        title: level === 'easy' ? '简单！' : level === 'ok' ? '记住了' : '再巩固',
        icon: 'none',
        duration: 800,
      })
      // 从队列中移除该项
      const queue = this.data.queue.filter(item => item.poem_id !== poemId)
      this.setData({ queue })
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.fetchReviewQueue().finally(() => {
      wx.stopPullDownRefresh()
    })
  },
})
