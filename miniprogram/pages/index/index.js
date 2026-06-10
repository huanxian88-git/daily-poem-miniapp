// pages/index/index.js - 首页：每日推荐

const app = getApp()
import api from '../../services/api'
import userStore from '../../stores/user-store'
import { formatDate, difficultyStars } from '../../utils/util'

Page({
  data: {
    // 状态
    loading: true,
    error: null,

    // 今日推荐
    todayDate: '',
    poem: null,
    reason: '',
    canSwitch: true,
    switchCount: 0,
    maxSwitchCount: 3,

    // AI场景图
    sceneImage: '',

    // 用户画像（来自 Store）
    userProfile: null,
    isLoggedIn: false,

    // UI
    stars: '',
  },

  onLoad() {
    this.setData({
      todayDate: formatDate(new Date(), 'YYYY年M月D日')
    })
  },

  onShow() {
    userStore.bind(this)
    this.syncUserState()
    this.fetchTodayRecommendation()
  },

  onHide() {
    userStore.unbind(this)
  },

  /**
   * 从 Store 同步用户状态到页面
   */
  _userStoreUpdate(newData, oldData) {
    this.syncUserState()
  },

  syncUserState() {
    this.setData({
      isLoggedIn: userStore.data.isLoggedIn,
      userProfile: userStore.data.profile,
    })
  },

  /**
   * 微信登录
   */
  async login() {
    wx.showLoading({ title: '登录中...' })
    try {
      const res = await userStore.login()
      if (res.success) {
        wx.showToast({ title: '登录成功', icon: 'success' })
        this.syncUserState()
        this.fetchTodayRecommendation()
      } else {
        wx.showToast({ title: '登录失败', icon: 'none' })
      }
    } catch (e) {
      wx.showToast({ title: '登录失败', icon: 'none' })
    } finally {
      wx.hideLoading()
    }
  },

  /**
   * 获取今日推荐
   */
  async fetchTodayRecommendation() {
    if (!userStore.data.isLoggedIn) {
      this.setData({ loading: false })
      return
    }

    this.setData({ loading: true, error: null })

    try {
      const res = await api.get('/daily/today')
      this.setData({
        poem: res.poem,
        reason: res.reason,
        canSwitch: res.can_switch,
        switchCount: 0,
        sceneImage: res.poem?.scene_image_url || '',
        stars: difficultyStars(res.poem?.difficulty || 1),
        loading: false,
      })
    } catch (e) {
      this.setData({
        error: '加载失败，请下拉刷新',
        loading: false,
      })
    }
  },

  /**
   * "换一首"
   */
  async switchPoem() {
    if (!this.data.canSwitch) {
      wx.showToast({ title: '今日更换次数已用完', icon: 'none' })
      return
    }

    try {
      const res = await api.post('/daily/switch')
      this.setData({
        poem: res.poem,
        reason: res.reason,
        canSwitch: res.can_switch,
        switchCount: this.data.switchCount + 1,
        sceneImage: res.poem?.scene_image_url || '',
        stars: difficultyStars(res.poem?.difficulty || 1),
      })
    } catch (e) {
      wx.showToast({ title: '换一首失败', icon: 'none' })
    }
  },

  /**
   * 珍藏
   */
  async toggleFavorite() {
    if (!this.data.poem) return
    try {
      await api.post('/favorites/' + this.data.poem.id)
      wx.showToast({ title: '已珍藏', icon: 'success' })
    } catch (e) {
      wx.showToast({ title: '操作失败', icon: 'none' })
    }
  },

  /**
   * 吟诵：智能入口
   */
  async startRecite() {
    if (!this.data.poem) return
    wx.navigateTo({
      url: `/pages/recite-check/recite-check?poemId=${this.data.poem.id}&title=${encodeURIComponent(this.data.poem.title)}`
    })
  },

  /**
   * 查看诗词详情
   */
  viewPoemDetail() {
    if (!this.data.poem) return
    wx.navigateTo({
      url: `/pages/poem/poem?poemId=${this.data.poem.id}`
    })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    this.fetchTodayRecommendation().finally(() => {
      wx.stopPullDownRefresh()
    })
  },

  /**
   * 转到吟诵页
   */
  goToRecite() {
    wx.switchTab({ url: '/pages/recite/recite' })
  },

  /**
   * 转到我的
   */
  goToProfile() {
    wx.switchTab({ url: '/pages/profile/profile' })
  },
})
