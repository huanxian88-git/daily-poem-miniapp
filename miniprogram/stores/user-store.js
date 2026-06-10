/**
 * 用户状态管理 Store
 * 功能：全局用户状态管理，响应式数据
 */

import api from '../services/api'

class UserStore {
  constructor() {
    this._data = {
      // 用户基础信息
      isLoggedIn: false,
      userId: null,
      openid: null,
      nickname: '',
      avatarUrl: '',

      // 用户画像
      profile: {
        ageGroup: null,
        level: null,
        interests: [],
        reciteRhythm: 'every_2_days',
        reciteRhythmCustomDays: null,
        textbookVersion: null,
        textbookGrade: null,
        textbookSemester: null,
        isStudent: false,
      },

      // 背诵状态
      activeRecitations: [],  // 正在背诵的诗
      masteredCount: 0,      // 已掌握数量
      todayRecited: false,   // 今日是否已背诵
    }

    // 页面绑定列表（用于 notify）
    this._pages = []
  }

  /**
   * 获取数据（供页面模板使用）
   */
  get data() {
    return this._data
  }

  /**
   * 更新数据并通知所有绑定页面
   */
  set(partial) {
    const oldData = { ...this._data }

    // 深合并嵌套对象
    if (partial.profile) {
      this._data.profile = { ...this._data.profile, ...partial.profile }
      partial = { ...partial }
      delete partial.profile
    }

    this._data = { ...this._data, ...partial }

    // 通知所有绑定的页面
    this._pages.forEach(page => {
      if (page._userStoreUpdate) {
        page._userStoreUpdate(this._data, oldData)
      }
    })
  }

  /**
   * 页面绑定：在 onShow 时调用
   * page 需实现 _userStoreUpdate(newData, oldData) 方法
   */
  bind(page) {
    if (!this._pages.includes(page)) {
      this._pages.push(page)
    }
  }

  /**
   * 页面解绑：在 onHide 或 onUnload 时调用
   */
  unbind(page) {
    const idx = this._pages.indexOf(page)
    if (idx > -1) {
      this._pages.splice(idx, 1)
    }
  }

  /**
   * 微信登录
   */
  async login() {
    try {
      // 1. 获取微信 code
      const loginRes = await wx.login()
      const code = loginRes.code

      // 2. 后端 code2session + 签发 Token
      const tokenRes = await api.post('/auth/login', { code })

      // 3. 保存 Token
      api.saveTokens(tokenRes.access_token, tokenRes.refresh_token)

      // 4. 更新状态
      this.set({
        isLoggedIn: true,
        isNewUser: tokenRes.is_new_user,
      })

      // 同步全局 app 状态
      const app = getApp()
      app.globalData.isLoggedIn = true

      return {
        success: true,
        isNewUser: tokenRes.is_new_user,
      }
    } catch (e) {
      console.error('登录失败:', e)
      return { success: false, error: e }
    }
  }

  /**
   * 获取用户画像
   */
  async fetchProfile() {
    try {
      const profile = await api.get('/profile')
      this.set({ profile })
      return profile
    } catch (e) {
      console.error('获取画像失败:', e)
      return null
    }
  }

  /**
   * 更新用户画像
   */
  async updateProfile(data) {
    try {
      const updated = await api.put('/profile', data)
      this.set({ profile: updated })
      return updated
    } catch (e) {
      console.error('更新画像失败:', e)
      return null
    }
  }

  /**
   * 退出登录
   */
  logout() {
    api.clearTokens()
    this.set({
      isLoggedIn: false,
      userId: null,
      nickname: '',
      avatarUrl: '',
      profile: {
        ageGroup: null,
        level: null,
        interests: [],
        reciteRhythm: 'every_2_days',
        reciteRhythmCustomDays: null,
        textbookVersion: null,
        textbookGrade: null,
        textbookSemester: null,
        isStudent: false,
      },
    })

    const app = getApp()
    app.globalData.isLoggedIn = false
    app.globalData.userInfo = null
  }
}

// 导出单例
const userStore = new UserStore()
export default userStore
