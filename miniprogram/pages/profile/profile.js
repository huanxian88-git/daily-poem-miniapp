// pages/profile/profile.js - 我的Tab升级

import api from '../../services/api'
import userStore from '../../stores/user-store'

// 画像显示映射
const AGE_GROUP_MAP = {
  child: '少年',
  teen: '青春',
  young_adult: '而立',
  middle_age: '不惑',
  senior: '知天命',
}

const LEVEL_MAP = {
  beginner: '初识',
  elementary: '入门',
  intermediate: '熟悉',
  advanced: '精通',
}

const RHYTHM_MAP = {
  every_day: '每天',
  every_2_days: '每2天',
  every_3_days: '每3天',
  weekly: '每周',
}

Page({
  data: {
    isLoggedIn: false,
    userInfo: {},
    userProfile: null,
    stats: {
      masteredCount: 0,
      streakDays: 0,
      totalRecited: 0,
    },
    profileDisplay: {},
    profileTag: '',

    // 背诵节奏
    showRhythm: false,
    rhythmOptions: [
      { value: 'every_day', label: '每天' },
      { value: 'every_2_days', label: '每2天' },
      { value: 'every_3_days', label: '每3天' },
      { value: 'weekly', label: '每周' },
    ],
  },

  onShow() {
    userStore.bind(this)
    this.syncUserState()
    if (userStore.data.isLoggedIn) {
      this.fetchStats()
    }
  },

  onHide() {
    userStore.unbind(this)
  },

  _userStoreUpdate(newData) {
    this.syncUserState()
  },

  /**
   * 同步用户状态
   */
  syncUserState() {
    const isLoggedIn = userStore.data.isLoggedIn
    const profile = userStore.data.profile || {}

    // 构建画像显示文本
    const profileDisplay = {
      ageGroup: AGE_GROUP_MAP[profile.ageGroup] || '',
      level: LEVEL_MAP[profile.level] || '',
      rhythm: RHYTHM_MAP[profile.reciteRhythm] || '',
      textbook: '',
    }
    if (profile.isStudent && profile.textbookVersion) {
      profileDisplay.textbook = `${profile.textbookVersion} ${profile.textbookGrade || ''} ${profile.textbookSemester || ''}`
    }

    // 画像标签
    const tags = []
    if (profileDisplay.level) tags.push(profileDisplay.level)
    if (profile.isStudent) tags.push('学生')
    const profileTag = tags.length > 0 ? tags.join(' · ') : ''

    this.setData({
      isLoggedIn,
      userInfo: {
        nickname: userStore.data.nickname || '',
        avatarUrl: userStore.data.avatarUrl || '',
      },
      userProfile: profile,
      profileDisplay,
      profileTag,
    })
  },

  /**
   * 获取统计摘要
   */
  async fetchStats() {
    try {
      const res = await api.get('/stats/summary')
      this.setData({
        stats: {
          masteredCount: res.mastered_count || 0,
          streakDays: res.streak_days || 0,
          totalRecited: res.total_recited || 0,
        },
      })
    } catch (e) {
      // 静默失败，保持默认值
    }
  },

  /**
   * 微信登录
   */
  async handleLogin() {
    const result = await userStore.login()
    if (result.success) {
      wx.showToast({ title: '登录成功', icon: 'success' })
      this.syncUserState()
      this.fetchStats()
      if (result.isNewUser) {
        wx.navigateTo({ url: '/pages/onboarding/onboarding' })
      }
    } else {
      wx.showToast({ title: '登录失败', icon: 'none' })
    }
  },

  /**
   * 退出登录
   */
  handleLogout() {
    wx.showModal({
      title: '退出登录',
      content: '确定要退出吗？你的背诵记录会保留',
      confirmColor: '#C44536',
      success: (res) => {
        if (res.confirm) {
          userStore.logout()
          this.setData({
            isLoggedIn: false,
            userInfo: {},
            stats: { masteredCount: 0, streakDays: 0, totalRecited: 0 },
          })
        }
      },
    })
  },

  /**
   * 修改画像
   */
  goToOnboarding() {
    wx.navigateTo({ url: '/pages/onboarding/onboarding' })
  },

  /**
   * 背诵节奏选择
   */
  showRhythmPicker() {
    this.setData({ showRhythm: true })
  },

  onRhythmChange(e) {
    const idx = e.detail.value
    const selected = this.data.rhythmOptions[idx]
    this.setData({ showRhythm: false })

    userStore.updateProfile({ recite_rhythm: selected.value })
    this.setData({
      'profileDisplay.rhythm': selected.label,
    })
  },

  onRhythmCancel() {
    this.setData({ showRhythm: false })
  },

  /**
   * 关于
   */
  showAbout() {
    wx.showModal({
      title: '天天半首诗',
      content: '每日半首，积少成多\n让诗词融入日常\n\n版本 0.4.0',
      showCancel: false,
      confirmText: '知道了',
    })
  },
})
