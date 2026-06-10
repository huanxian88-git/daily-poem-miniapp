// pages/index/index.js - 首页升级

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
    isFavorited: false,

    // AI场景图
    sceneImage: '',

    // 用户画像（来自 Store）
    userProfile: null,
    isLoggedIn: false,

    // 零压力提示（新用户前3天）
    showZeroPressureHint: false,
    daysSinceSignup: 0,

    // 双入口数据
    reciteCount: 0,
    reviewCount: 0,

    // 课本信息
    isStudent: false,
    textbookInfo: '',

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
    this.fetchEntryCounts()
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
    const profile = userStore.data.profile || {}
    const isLoggedIn = userStore.data.isLoggedIn

    // 课本信息
    let textbookInfo = ''
    let isStudent = false
    if (profile.isStudent && profile.textbookVersion) {
      isStudent = true
      textbookInfo = `${profile.textbookVersion} ${profile.textbookGrade || ''} ${profile.textbookSemester || ''}`
    }

    // 零压力提示：新用户前3天
    const daysSinceSignup = profile.daysSinceSignup || 0
    const showZeroPressureHint = isLoggedIn && daysSinceSignup <= 3

    this.setData({
      isLoggedIn,
      userProfile: profile,
      isStudent,
      textbookInfo,
      showZeroPressureHint,
      daysSinceSignup,
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
        this.fetchEntryCounts()
        if (res.isNewUser) {
          wx.navigateTo({ url: '/pages/onboarding/onboarding' })
        }
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
        isFavorited: res.poem?.is_favorited || false,
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
   * 获取吟诵/临帖入口数据
   */
  async fetchEntryCounts() {
    if (!userStore.data.isLoggedIn) return

    try {
      const [reciteRes, reviewRes] = await Promise.all([
        api.get('/recite/list').catch(() => ({ items: [] })),
        api.get('/review/queue').catch(() => ({ items: [] })),
      ])
      const reciteItems = reciteRes.items || reciteRes || []
      const reviewItems = reviewRes.items || reviewRes || []
      this.setData({
        reciteCount: reciteItems.length,
        reviewCount: reviewItems.length,
      })
    } catch (e) {
      // 静默失败
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
        isFavorited: res.poem?.is_favorited || false,
      })
    } catch (e) {
      wx.showToast({ title: '换一首失败', icon: 'none' })
    }
  },

  /**
   * 珍藏/取消珍藏
   */
  async toggleFavorite() {
    if (!this.data.poem) return
    try {
      if (this.data.isFavorited) {
        await api.delete('/favorites/' + this.data.poem.id)
        this.setData({ isFavorited: false })
        wx.showToast({ title: '已取消珍藏', icon: 'none' })
      } else {
        await api.post('/favorites/' + this.data.poem.id)
        this.setData({ isFavorited: true })
        wx.showToast({ title: '已珍藏', icon: 'success' })
      }
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
   * 转到吟诵页
   */
  goToRecite() {
    wx.switchTab({ url: '/pages/recite/recite' })
  },

  /**
   * 转到临帖页
   */
  goToReview() {
    wx.navigateTo({ url: '/pages/review/review' })
  },

  /**
   * 下拉刷新
   */
  onPullDownRefresh() {
    Promise.all([
      this.fetchTodayRecommendation(),
      this.fetchEntryCounts(),
    ]).finally(() => {
      wx.stopPullDownRefresh()
    })
  },
})
