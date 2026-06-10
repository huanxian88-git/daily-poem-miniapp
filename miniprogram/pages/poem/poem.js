// pages/poem/poem.js - 诗词详情页

import api from '../../services/api'

Page({
  data: {
    loading: true,
    error: null,
    poemId: null,
    poem: null,
    sceneData: {},
    annotationExpanded: false,
    isFavorited: false,
  },

  onLoad(options) {
    const poemId = options.poemId || options.poem_id
    if (!poemId) {
      this.setData({ error: '缺少诗词ID', loading: false })
      return
    }
    this.setData({ poemId })
    this.fetchPoemDetail()
    this.fetchSceneData()
  },

  /**
   * 获取诗词详情
   */
  async fetchPoemDetail() {
    this.setData({ loading: true, error: null })
    try {
      const res = await api.get('/poems/' + this.data.poemId)
      this.setData({
        poem: res,
        isFavorited: res.is_favorited || false,
        loading: false,
      })
    } catch (e) {
      this.setData({
        error: '加载失败，请重试',
        loading: false,
      })
    }
  },

  /**
   * 获取AI联想场景
   */
  async fetchSceneData() {
    try {
      const res = await api.get('/poems/' + this.data.poemId + '/scene')
      this.setData({ sceneData: res })
    } catch (e) {
      // 场景图非关键，静默失败
      console.warn('获取场景图失败:', e)
    }
  },

  /**
   * 切换注释译文展开/折叠
   */
  toggleAnnotation() {
    this.setData({
      annotationExpanded: !this.data.annotationExpanded,
    })
  },

  /**
   * 珍藏/取消珍藏
   */
  async toggleFavorite() {
    if (!this.data.poem) return
    try {
      if (this.data.isFavorited) {
        await api.delete('/favorites/' + this.data.poemId)
        this.setData({ isFavorited: false })
        wx.showToast({ title: '已取消珍藏', icon: 'none' })
      } else {
        await api.post('/favorites/' + this.data.poemId)
        this.setData({ isFavorited: true })
        wx.showToast({ title: '已珍藏', icon: 'success' })
      }
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /**
   * 吟诵：进入背诵检查
   */
  startRecite() {
    if (!this.data.poem) return
    wx.navigateTo({
      url: `/pages/recite-check/recite-check?poemId=${this.data.poemId}&title=${encodeURIComponent(this.data.poem.title)}`
    })
  },
})
