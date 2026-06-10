/**
 * 工具函数库
 */

/**
 * 日期格式化
 */
function formatDate(date, fmt = 'YYYY-MM-DD') {
  const d = date || new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const minutes = String(d.getMinutes()).padStart(2, '0')

  return fmt
    .replace('YYYY', year)
    .replace('MM', month)
    .replace('DD', day)
    .replace('HH', hours)
    .replace('mm', minutes)
}

/**
 * 防抖
 */
function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
      timer = null
    }, delay)
  }
}

/**
 * 节流
 */
function throttle(fn, interval = 300) {
  let lastTime = 0
  return function (...args) {
    const now = Date.now()
    if (now - lastTime >= interval) {
      lastTime = now
      fn.apply(this, args)
    }
  }
}

/**
 * 诗词难度显示（★）
 */
function difficultyStars(level) {
  return '★'.repeat(level || 1) + '☆'.repeat(5 - (level || 1))
}

/**
 * 音频录制管理器
 */
function createRecorder(options = {}) {
  const recorder = wx.getRecorderManager()
  recorder._options = {
    duration: 60000,      // 最长60秒
    sampleRate: 16000,    // 采样率（ASR要求）
    numberOfChannels: 1,  // 单声道
    encodeBitRate: 48000,
    format: 'mp3',
    ...options,
  }
  return recorder
}

/**
 * 获取今日日期字符串 YYYY-MM-DD
 */
function today() {
  return formatDate(new Date(), 'YYYY-MM-DD')
}

module.exports = {
  formatDate,
  debounce,
  throttle,
  difficultyStars,
  createRecorder,
  today,
}
