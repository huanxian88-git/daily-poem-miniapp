// pages/onboarding/onboarding.js - 用户画像采集页

import api from '../../services/api'
import userStore from '../../stores/user-store'

Page({
  data: {
    step: 1,

    // 第1步：年龄段
    ageGroupOptions: [
      { value: 'child', label: '少年', icon: '🌱' },
      { value: 'teen', label: '青春', icon: '🍃' },
      { value: 'young_adult', label: '而立', icon: '🌳' },
      { value: 'middle_age', label: '不惑', icon: '🍂' },
      { value: 'senior', label: '知天命', icon: '🌾' },
    ],
    selectedAgeGroup: '',

    // 第2步：诗词水平
    levelOptions: [
      { value: 'beginner', label: '初识' },
      { value: 'elementary', label: '入门' },
      { value: 'intermediate', label: '熟悉' },
      { value: 'advanced', label: '精通' },
    ],
    selectedLevel: '',

    // 第2步：兴趣偏好
    interestOptions: [
      { value: 'landscape', label: '山水田园' },
      { value: 'farewell', label: '离别送行' },
      { value: 'history', label: '咏史怀古' },
      { value: 'emotion', label: '闺情爱情' },
      { value: 'philosophy', label: '哲理禅意' },
      { value: 'border', label: '边塞军旅' },
      { value: 'folk', label: '民俗节令' },
      { value: 'friendship', label: '友情羁旅' },
    ],
    selectedInterests: [],

    // 第3步：是否学生
    isStudent: null,
    textbookVersions: ['人教版', '苏教版', '北师大版', '部编版'],
    gradeOptions: ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三'],
    selectedTextbook: '',
    selectedGrade: '',
    selectedSemester: '',

    // UI
    canNext: false,
    submitting: false,
  },

  onLoad() {
    this.updateCanNext()
  },

  /**
   * 选择年龄段
   */
  selectAgeGroup(e) {
    const value = e.currentTarget.dataset.value
    this.setData({ selectedAgeGroup: value })
    this.updateCanNext()
  },

  /**
   * 选择诗词水平
   */
  selectLevel(e) {
    const value = e.currentTarget.dataset.value
    this.setData({ selectedLevel: value })
    this.updateCanNext()
  },

  /**
   * 切换兴趣标签
   */
  toggleInterest(e) {
    const value = e.currentTarget.dataset.value
    let interests = this.data.selectedInterests.slice()
    const idx = interests.indexOf(value)
    if (idx > -1) {
      interests.splice(idx, 1)
    } else {
      interests.push(value)
    }
    this.setData({ selectedInterests: interests })
    this.updateCanNext()
  },

  /**
   * 选择是否学生
   */
  selectStudent(e) {
    const value = e.currentTarget.dataset.value === 'true'
    this.setData({ isStudent: value })
    this.updateCanNext()
  },

  /**
   * 课本版本选择
   */
  onTextbookVersionChange(e) {
    const idx = e.detail.value
    this.setData({ selectedTextbook: this.data.textbookVersions[idx] })
  },

  /**
   * 年级选择
   */
  onGradeChange(e) {
    const idx = e.detail.value
    this.setData({ selectedGrade: this.data.gradeOptions[idx] })
  },

  /**
   * 学期选择
   */
  selectSemester(e) {
    const value = e.currentTarget.dataset.value
    this.setData({ selectedSemester: value })
  },

  /**
   * 更新"下一步"按钮状态（每步都可以跳过，所以始终可点）
   */
  updateCanNext() {
    this.setData({ canNext: true })
  },

  /**
   * 下一步
   */
  nextStep() {
    if (this.data.step < 3) {
      this.setData({ step: this.data.step + 1 })
    } else {
      this.submitProfile()
    }
  },

  /**
   * 跳过当前步骤
   */
  skipStep() {
    if (this.data.step < 3) {
      this.setData({ step: this.data.step + 1 })
    } else {
      // 跳过全部，直接完成
      this.completeOnboarding()
    }
  },

  /**
   * 提交画像
   */
  async submitProfile() {
    this.setData({ submitting: true })

    const profileData = {
      age_group: this.data.selectedAgeGroup || 'young_adult',
      level: this.data.selectedLevel || 'elementary',
      interests: this.data.selectedInterests.length > 0
        ? this.data.selectedInterests
        : ['landscape', 'emotion'],
      is_student: this.data.isStudent === true,
      textbook_version: this.data.selectedTextbook || null,
      textbook_grade: this.data.selectedGrade || null,
      textbook_semester: this.data.selectedSemester || null,
    }

    try {
      await api.post('/profile', profileData)
      userStore.set({ profile: profileData })
      wx.showToast({ title: '设置完成', icon: 'success' })
      this.completeOnboarding()
    } catch (e) {
      wx.showToast({ title: '提交失败，请重试', icon: 'none' })
    } finally {
      this.setData({ submitting: false })
    }
  },

  /**
   * 完成采集，返回首页
   */
  completeOnboarding() {
    wx.switchTab({ url: '/pages/index/index' })
  },
})
