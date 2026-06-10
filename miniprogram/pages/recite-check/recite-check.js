// pages/recite-check/recite-check.js - 背诵检查页（三关流程）

import api from '../../services/api'
import { createRecorder } from '../../utils/util'

Page({
  data: {
    // 基础信息
    poemId: null,
    poemTitle: '',
    recitationId: null,
    currentStage: 1, // 1=补阙填词, 2=排序归位, 3=语音背诵

    stageLabels: ['第一关 · 补阙填词', '第二关 · 排序归位', '第三关 · 语音背诵'],
    stageLabel: '',

    // 第一关：补阙填词
    fillLines: [],

    // 第二关：排序归位
    sortLines: [],
    sortSelectedIdx: -1,

    // 第三关：语音背诵
    isRecording: false,
    recordingDuration: 0,
    recognizedText: '',
    poemFirstLine: '',
    _recorder: null,
    _recordingTimer: null,

    // 关卡结果
    showStageResult: false,
    stageResult: {
      score: 0,
      passed: false,
      correctCount: 0,
      errors: [],
    },

    submitting: false,
  },

  onLoad(options) {
    const poemId = options.poemId
    const title = options.title ? decodeURIComponent(options.title) : '诗词'
    const recitationId = options.recitation_id || null

    this.setData({
      poemId,
      poemTitle: title,
      recitationId,
      stageLabel: '第一关 · 补阙填词',
    })

    this.loadStageData(1)
  },

  onUnload() {
    this.stopRecordingTimer()
    if (this.data._recorder) {
      try {
        this.data._recorder.stop()
      } catch (e) { /* ignore */ }
    }
  },

  /**
   * 加载关卡数据
   */
  async loadStageData(stage) {
    wx.showLoading({ title: '加载中...' })
    try {
      if (stage === 1) {
        const res = await api.get('/recite/' + this.data.poemId + '/fill')
        this.setData({
          fillLines: res.lines || [],
          poemFirstLine: res.first_line || '',
        })
      } else if (stage === 2) {
        const res = await api.get('/recite/' + this.data.poemId + '/sort')
        const sortLines = (res.lines || []).map((text, idx) => ({
          id: idx,
          text,
          displayNum: idx + 1,
          isCorrect: false,
          originalIdx: idx,
        }))
        this.setData({ sortLines, sortSelectedIdx: -1 })
      } else if (stage === 3) {
        // 语音背诵无需额外数据加载
        const res = await api.get('/recite/' + this.data.poemId + '/voice')
        this.setData({ poemFirstLine: res.first_line || '' })
      }
    } catch (e) {
      // 如果API不可用，使用mock数据
      this.loadMockData(stage)
    } finally {
      wx.hideLoading()
    }
  },

  /**
   * Mock数据（API不可用时）
   */
  loadMockData(stage) {
    if (stage === 1) {
      const mockLines = [
        {
          lineIdx: 0,
          parts: [
            { type: 'text', content: '床前' },
            { type: 'blank', blankIdx: 0, filled: '' },
            { type: 'text', content: '光，' },
          ]
        },
        {
          lineIdx: 1,
          parts: [
            { type: 'text', content: '疑是地上' },
            { type: 'blank', blankIdx: 1, filled: '' },
            { type: 'text', content: '。' },
          ]
        },
        {
          lineIdx: 2,
          parts: [
            { type: 'blank', blankIdx: 2, filled: '' },
            { type: 'text', content: '举头望明月，' },
          ]
        },
        {
          lineIdx: 3,
          parts: [
            { type: 'text', content: '低头思' },
            { type: 'blank', blankIdx: 3, filled: '' },
            { type: 'text', content: '。' },
          ]
        },
      ]
      this.setData({ fillLines: mockLines, poemFirstLine: '床前明月光' })
    } else if (stage === 2) {
      const mockSortLines = [
        { id: 0, text: '低头思故乡', displayNum: 1, isCorrect: false, originalIdx: 3 },
        { id: 1, text: '床前明月光', displayNum: 2, isCorrect: false, originalIdx: 0 },
        { id: 2, text: '举头望明月', displayNum: 3, isCorrect: false, originalIdx: 2 },
        { id: 3, text: '疑是地上霜', displayNum: 4, isCorrect: false, originalIdx: 1 },
      ]
      this.setData({ sortLines: mockSortLines, sortSelectedIdx: -1 })
    } else if (stage === 3) {
      this.setData({ poemFirstLine: '床前明月光' })
    }
  },

  // ========== 第一关：补阙填词 ==========

  /**
   * 填空输入
   */
  onFillInput(e) {
    const lineIdx = e.currentTarget.dataset.lineIdx
    const blankIdx = e.currentTarget.dataset.blankIdx
    const value = e.detail.value

    const fillLines = this.data.fillLines.slice()
    const line = fillLines.find(l => l.lineIdx === lineIdx)
    if (line) {
      const part = line.parts.find(p => p.blankIdx === blankIdx)
      if (part) {
        part.filled = value
      }
    }
    this.setData({ fillLines })
  },

  /**
   * 提交第一关
   */
  async submitFill() {
    this.setData({ submitting: true })
    try {
      // 收集填空答案
      const answers = []
      this.data.fillLines.forEach(line => {
        line.parts.forEach(part => {
          if (part.type === 'blank') {
            answers.push({
              line_idx: line.lineIdx,
              blank_idx: part.blankIdx,
              answer: part.filled || '',
            })
          }
        })
      })

      const res = await api.post('/recite/' + this.data.poemId + '/fill', { answers })
      this.showStageResultPopup(res)
    } catch (e) {
      // Mock通过
      this.showStageResultPopup({
        score: 80,
        passed: true,
        correctCount: 4,
        errors: [{ expected: '明', actual: '月' }],
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // ========== 第二关：排序归位 ==========

  /**
   * 点击排序行（点击交换）
   */
  onSortLineTap(e) {
    const idx = e.currentTarget.dataset.index
    const sortSelectedIdx = this.data.sortSelectedIdx

    if (sortSelectedIdx === -1) {
      // 第一次点击，选中
      this.setData({ sortSelectedIdx: idx })
    } else if (sortSelectedIdx === idx) {
      // 再次点击同一行，取消选中
      this.setData({ sortSelectedIdx: -1 })
    } else {
      // 点击另一行，交换
      const sortLines = this.data.sortLines.slice()
      const temp = sortLines[sortSelectedIdx]
      sortLines[sortSelectedIdx] = sortLines[idx]
      sortLines[idx] = temp

      // 更新序号
      sortLines.forEach((line, i) => {
        line.displayNum = i + 1
        line.isCorrect = line.originalIdx === i
      })

      this.setData({ sortLines, sortSelectedIdx: -1 })
    }
  },

  /**
   * 提交第二关
   */
  async submitSort() {
    this.setData({ submitting: true })
    try {
      const order = this.data.sortLines.map(line => line.originalIdx)
      const res = await api.post('/recite/' + this.data.poemId + '/sort', { order })
      this.showStageResultPopup(res)
    } catch (e) {
      // Mock通过
      this.showStageResultPopup({
        score: 75,
        passed: true,
        correctCount: 3,
        errors: [],
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // ========== 第三关：语音背诵 ==========

  /**
   * 切换录音状态
   */
  toggleRecording() {
    if (this.data.isRecording) {
      this.stopRecording()
    } else {
      this.startRecording()
    }
  },

  /**
   * 开始录音
   */
  startRecording() {
    const recorder = createRecorder()
    this.setData({ _recorder: recorder, isRecording: true, recordingDuration: 0, recognizedText: '' })

    recorder.onStart(() => {
      // 开始计时
      this.startRecordingTimer()
    })

    recorder.onStop((res) => {
      this.stopRecordingTimer()
      this.setData({ isRecording: false })
      // 阶段3用mock：模拟识别结果
      this.mockRecognize(res.tempFilePath)
    })

    recorder.start(recorder._options)
  },

  /**
   * 停止录音
   */
  stopRecording() {
    if (this.data._recorder) {
      this.data._recorder.stop()
    }
    this.stopRecordingTimer()
    this.setData({ isRecording: false })
  },

  /**
   * 录音计时器
   */
  startRecordingTimer() {
    let duration = 0
    const timer = setInterval(() => {
      duration += 1
      this.setData({ recordingDuration: duration })
      if (duration >= 60) {
        this.stopRecording()
      }
    }, 1000)
    this.setData({ _recordingTimer: timer })
  },

  stopRecordingTimer() {
    const timer = this.data._recordingTimer
    if (timer) {
      clearInterval(timer)
      this.setData({ _recordingTimer: null })
    }
  },

  /**
   * Mock语音识别
   */
  mockRecognize(tempFilePath) {
    wx.showLoading({ title: '识别中...' })
    setTimeout(() => {
      wx.hideLoading()
      // 模拟识别结果
      this.setData({
        recognizedText: '床前明月光，疑是地上霜。举头望明月，低头思故乡。',
      })
    }, 1500)
  },

  /**
   * 提交第三关
   */
  async submitVoice() {
    if (!this.data.recognizedText) {
      wx.showToast({ title: '请先背诵录音', icon: 'none' })
      return
    }
    this.setData({ submitting: true })
    try {
      const res = await api.post('/recite/' + this.data.poemId + '/voice', {
        recognized_text: this.data.recognizedText,
      })
      this.showStageResultPopup(res)
    } catch (e) {
      // Mock通过
      this.showStageResultPopup({
        score: 90,
        passed: true,
        correctCount: 20,
        errors: [],
      })
    } finally {
      this.setData({ submitting: false })
    }
  },

  // ========== 通用：结果弹窗 ==========

  /**
   * 展示关卡结果
   */
  showStageResultPopup(result) {
    this.setData({
      showStageResult: true,
      stageResult: {
        score: result.score || 0,
        passed: (result.score || 0) >= 60,
        correctCount: result.correctCount || 0,
        errors: result.errors || [],
      },
    })
  },

  /**
   * 结果弹窗 - 下一步
   */
  goNextStage() {
    const passed = this.data.stageResult.passed
    const stage = this.data.currentStage

    this.setData({ showStageResult: false })

    if (!passed) {
      // 未通过，重新挑战当前关
      this.loadStageData(stage)
      return
    }

    if (stage < 3) {
      // 进入下一关
      const nextStage = stage + 1
      this.setData({
        currentStage: nextStage,
        stageLabel: this.data.stageLabels[nextStage - 1],
      })
      this.loadStageData(nextStage)
    } else {
      // 三关完成，查看结果
      wx.redirectTo({
        url: `/pages/recite-result/recite-result?poemId=${this.data.poemId}&title=${encodeURIComponent(this.data.poemTitle)}`
      })
    }
  },
})
