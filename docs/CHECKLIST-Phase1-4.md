# 天天半首诗 — 阶段1~4 功能自测 Checklist

> 版本：v1.0  
> 日期：2026-06-10  
> 基于：Phase 3+4 提交 74c5883，79/79 单元测试通过  
> 体验前提：后端 `start-dev.bat` 启动成功 + 微信开发者工具打开 miniprogram/

---

## 一、当前可体验功能全景

### 后端 API（28个端点）

| 模块 | 端点 | 方法 | 功能 | 阶段 |
|------|------|------|------|------|
| **认证** | `/api/v1/auth/login` | POST | 微信登录（DEV_MODE mock） | 1 |
| | `/api/v1/auth/refresh` | POST | 刷新 Token | 1 |
| | `/api/v1/auth/me` | GET | 获取当前用户 | 1 |
| **诗词** | `/api/v1/poems/` | GET | 诗词列表（搜索/筛选） | 2 |
| | `/api/v1/poems/{id}` | GET | 诗词详情 | 2 |
| | `/api/v1/poems/{id}/scene` | GET | 诗词场景描述 | 2 |
| **每日推荐** | `/api/v1/daily/today` | GET | 今日推荐（规则引擎） | 3 |
| | `/api/v1/daily/switch` | POST | 换一首（≤5次/天） | 3 |
| | `/api/v1/daily/history` | GET | 历史推荐分页 | 3 |
| **用户画像** | `/api/v1/profile/` | GET | 获取画像 | 2 |
| | `/api/v1/profile/` | PUT | 更新画像 | 2 |
| | `/api/v1/profile/` | POST | 创建画像（幂等） | 2 |
| **珍藏** | `/api/v1/favorites/` | GET | 珍藏列表 | 2 |
| | `/api/v1/favorites/{poem_id}` | POST | 添加珍藏 | 2 |
| | `/api/v1/favorites/{poem_id}` | DELETE | 取消珍藏 | 2 |
| **背诵** | `/api/v1/recite/list` | GET | 在背列表 | 3 |
| | `/api/v1/recite/start` | POST | 开始背诵（含并发守卫） | 3 |
| | `/api/v1/recite/{id}/fill` | POST | 补阙填词检查 | 3 |
| | `/api/v1/recite/{id}/sort` | POST | 排序归位检查 | 3 |
| | `/api/v1/recite/{id}/voice` | POST | 语音背诵检查（mock） | 3 |
| | `/api/v1/recite/{id}/result` | GET | 背诵结果总览 | 3 |
| | `/api/v1/recite/{id}/abandon` | POST | 放弃背诵 | 3 |
| **复习** | `/api/v1/review/queue` | GET | 今日复习队列 | 3 |
| | `/api/v1/review/{poem_id}/done` | POST | 标记复习完成（SM-2） | 3 |
| | `/api/v1/review/stats` | GET | 复习统计摘要 | 3 |
| **统计** | `/api/v1/stats/summary` | GET | 学习统计摘要 | 3 |
| **健康** | `/health` | GET | 健康检查 | 1 |

### 前端页面（8个页面 + 3个Tab）

| 页面 | 路由 | 功能 | 阶段 |
|------|------|------|------|
| **首页** | pages/index/index | 每日推荐+双入口卡片+珍藏按钮 | 1→4升级 |
| **吟诵Tab** | pages/recite/recite | 在背列表+进度卡片 | 1→4升级 |
| **我的Tab** | pages/profile/profile | 用户卡+统计+设置 | 1→4升级 |
| **诗词详情** | pages/poem/poem | 正文+注释+译文+背景+珍藏 | 4 |
| **用户画像** | pages/onboarding/onboarding | 3步采集（年龄→级别→课本） | 4 |
| **背诵检查** | pages/recite-check/recite-check | 三关流程（填词→排序→语音） | 4 |
| **背诵结果** | pages/recite-result/recite-result | 正向框架评分+错题标记 | 4 |
| **复习** | pages/review/review | 复习队列+自评（简单/合适/困难） | 4 |

---

## 二、自测 Checklist — 后端 API

### M1: 认证模块（3端点 / 13条单元测试覆盖）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 1 | 健康检查 | GET /health | `{"status":"ok","version":"0.2.0"}` | ☐ |
| 2 | Mock登录 | POST /auth/login `{"code":"test_xxx"}` | 200, 返回 access_token + refresh_token + is_new_user=true | ☐ |
| 3 | 重复登录 | 同一 code 再次登录 | 200, is_new_user=false | ☐ |
| 4 | 无效Token | GET /auth/me 不带 Authorization | 401 | ☐ |
| 5 | 有效Token | GET /auth/me 带 Bearer token | 200, 返回 user_id/nickname | ☐ |
| 6 | Token刷新 | POST /auth/refresh 带 refresh_token | 200, 返回新 access_token | ☐ |
| 7 | 过期刷新Token | POST /auth/refresh 带无效token | 401 | ☐ |

### M2: 诗词模块（3端点）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 8 | 诗词列表 | GET /poems/ | 200, 返回分页列表含 title/author/dynasty/difficulty | ☐ |
| 9 | 搜索筛选 | GET /poems/?keyword=静夜&difficulty=1 | 200, 结果过滤正确 | ☐ |
| 10 | 诗词详情 | GET /poems/{id} | 200, 含 content_lines/annotation/translation/background/tags | ☐ |
| 11 | 不存在的诗词 | GET /poems/{不存在ID} | 404 | ☐ |
| 12 | 诗词场景 | GET /poems/{id}/scene | 200, 含 scene_type/scene_desc | ☐ |

### M3: 每日推荐模块（3端点 / 5条单元测试覆盖）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 13 | 今日推荐 | GET /daily/today (需登录) | 200, 含 poem详情 + reason + reason_type + can_switch | ☐ |
| 14 | 推荐理由类型 | 检查 reason_type 字段 | 为 festival/textbook/tag/random/manual 之一 | ☐ |
| 15 | 换一首 | POST /daily/switch | 200, 返回新诗词, switch_count+1 | ☐ |
| 16 | 换一首限制 | 连续换6次 | 第6次返回400 "今日换诗次数已达上限" | ☐ |
| 17 | 历史推荐 | GET /daily/history | 200, 含 items/total/page/page_size | ☐ |
| 18 | 历史分页 | GET /daily/history?page=1&page_size=5 | 200, page_size=5生效 | ☐ |

### M4: 用户画像模块（3端点 / 13条单元测试覆盖）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 19 | 获取默认画像 | GET /profile/ (登录后) | 200, age_group=null, is_student=false | ☐ |
| 20 | 更新画像 | PUT /profile/ `{"age_group":"adult","level":"beginner","interests":["思乡","月"]}` | 200, 字段更新成功 | ☐ |
| 21 | 部分更新 | PUT /profile/ `{"age_group":"student"}` | 200, 仅 age_group 变更，其余保留 | ☐ |
| 22 | 课本绑定 | PUT /profile/ `{"is_student":true,"textbook_version":"人教版","textbook_grade":"七年级","textbook_semester":"上"}` | 200, 三字段同时更新 | ☐ |
| 23 | 背诵节奏 | PUT /profile/ `{"recite_rhythm":"custom","recite_rhythm_custom_days":3}` | 200, 自定义节奏生效 | ☐ |
| 24 | 无权限访问 | GET /profile/ 不带Token | 401 | ☐ |

### M5: 珍藏模块（3端点）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 25 | 添加珍藏 | POST /favorites/{poem_id} | 200 或 201 | ☐ |
| 26 | 重复珍藏 | 再次 POST 同一 poem_id | 409 或幂等返回 | ☐ |
| 27 | 取消珍藏 | DELETE /favorites/{poem_id} | 200 或 204 | ☐ |
| 28 | 珍藏列表 | GET /favorites/ | 200, 含已珍藏诗词列表 | ☐ |
| 29 | 取消不存在的珍藏 | DELETE /favorites/{未珍藏ID} | 404 | ☐ |

### M6: 背诵模块（7端点 / 22条单元测试覆盖）⭐核心

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 30 | 开始背诵 | POST /recite/start `{"poem_id":"xxx"}` | 200, 返回 recitation_id + stage=fill | ☐ |
| 31 | 并发守卫-暖提醒 | 已有1首在背，再开1首 | 200, warm_reminder="你已有1首在背" | ☐ |
| 32 | 并发守卫-确认通过 | 暖提醒后带 confirmed=true | 200, 允许开始 | ☐ |
| 33 | 并发守卫-硬拦截 | 已有2首在背，再开1首(不确认) | 400, 拒绝开始 | ☐ |
| 34 | 重复背诵同一首 | 对已开始背诵的诗词再次 start | 400, 已在背诵中 | ☐ |
| 35 | 补阙填词-通过 | POST /recite/{id}/fill 正确答案 | 200, score≥60, passed=true | ☐ |
| 36 | 补阙填词-失败 | POST /recite/{id}/fill 全错 | 200, score<60, passed=false | ☐ |
| 37 | 补阙填词-部分 | POST /recite/{id}/fill 半对 | 200, 0<score<60, passed=false | ☐ |
| 38 | 排序归位-通过 | POST /recite/{id}/sort 正确顺序 | 200, score≥60, passed=true | ☐ |
| 39 | 排序归位-失败 | POST /recite/{id}/sort 错误顺序 | 200, score<60, passed=false | ☐ |
| 40 | 语音背诵-通过 | POST /recite/{id}/voice `{"recognized_text":"床前明月光，疑是地上霜。举头望明月，低头思故乡。"}` | 200, score≥60, passed=true | ☐ |
| 41 | 语音背诵-失败 | POST /recite/{id}/voice `{"recognized_text":"完全不对"}` | 200, score<60, passed=false | ☐ |
| 42 | 成诵判定 | 三关均≥60分 | GET /recite/{id}/result → is_mastered=true | ☐ |
| 43 | 部分通过 | 仅填词通过 | GET /recite/{id}/result → is_mastered=false | ☐ |
| 44 | 在背列表 | GET /recite/list | 200, 返回当前未放弃/未完成的背诵 | ☐ |
| 45 | 放弃背诵 | POST /recite/{id}/abandon | 204, 记录被删除 | ☐ |
| 46 | 无权限操作 | 对他人的背诵记录操作 | 403 或 404 | ☐ |

### M7: 复习模块（3端点 / 10条单元测试覆盖）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 47 | 空复习队列 | GET /review/queue (无到期) | 200, items=[] | ☐ |
| 48 | 有到期复习 | 背诵成诵后，将 ReviewSchedule 的 next_review_date 设为今天 | GET /review/queue 返回到期项 | ☐ |
| 49 | 队列排序 | 多首到期 | 按紧急程度排序（逾期越久越前） | ☐ |
| 50 | 复习-简单 | POST /review/{poem_id}/done `{"self_assessment":"easy"}` | 200, ease_factor+0.15, interval变大 | ☐ |
| 51 | 复习-一般 | POST /review/{poem_id}/done `{"self_assessment":"good"}` | 200, interval正常增长 | ☐ |
| 52 | 复习-困难 | POST /review/{poem_id}/done `{"self_assessment":"hard"}` | 200, ease_factor-0.2(最低1.3), interval*0.6 | ☐ |
| 53 | 复习后next_date更新 | 复习后查询 ReviewSchedule | next_review_date 已更新为未来日期 | ☐ |
| 54 | 复习统计 | GET /review/stats | 200, 含 total/mastered/reviewing/today_due | ☐ |
| 55 | 不存在的复习 | POST /review/{不存在的poem_id}/done | 400 | ☐ |

### M8: 统计模块（1端点 / 5条单元测试覆盖）

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 56 | 新用户统计 | GET /stats/summary (新用户) | total_recited=0, streak_days=0 | ☐ |
| 57 | 有数据统计 | 背诵几首后查询 | total_recited>0, total_mastered≥0 | ☐ |
| 58 | 连续天数 | 连续2天背诵 | streak_days=2 | ☐ |
| 59 | 今日背诵数 | 今天背了1首 | today_recited=1 | ☐ |
| 60 | 无权限 | 不带Token | 401 | ☐ |

---

## 三、自测 Checklist — 前端页面

### P1: 首页 (pages/index)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 61 | 页面加载 | 进入首页 | 显示每日推荐诗词卡片 | ☐ |
| 62 | 双入口卡片 | 查看"吟诵"和"临帖"入口 | 两个入口卡片可见，显示对应数量 | ☐ |
| 63 | 珍藏按钮 | 点击珍藏按钮 | 按钮变为已珍藏状态（琥珀色） | ☐ |
| 64 | 取消珍藏 | 再次点击珍藏按钮 | 恢复未珍藏状态 | ☐ |
| 65 | 课本卡片 | 用户画像 is_student=true | 显示课本进度卡片 | ☐ |
| 66 | 课本卡片隐藏 | 用户画像 is_student=false | 不显示课本卡片 | ☐ |
| 67 | 换一首 | 点击"换一首" | 推荐新诗词，计数+1 | ☐ |

### P2: 吟诵Tab (pages/recite)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 68 | 在背列表 | 进入吟诵Tab | 显示当前在背诗词进度卡片 | ☐ |
| 69 | 空状态 | 无在背诗词 | 显示空状态提示，引导去首页推荐 | ☐ |
| 70 | 点击开始 | 点击某首诗的"开始" | 跳转到背诵检查页 | ☐ |

### P3: 诗词详情页 (pages/poem)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 71 | 正文展示 | 从首页点击诗词进入 | 正文按行显示(content_lines wx:for) | ☐ |
| 72 | 注释展开 | 点击注释区域 | 注释内容展开/折叠 | ☐ |
| 73 | 译文展示 | 查看译文区域 | 译文内容可见 | ☐ |
| 74 | 背景展示 | 查看背景区域 | 创作背景内容可见 | ☐ |
| 75 | 珍藏切换 | 点击珍藏按钮 | 珍藏状态切换 | ☐ |

### P4: 用户画像采集页 (pages/onboarding)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 76 | 第1步-年龄 | 进入画像采集 | 显示年龄组选择 | ☐ |
| 77 | 第2步-级别兴趣 | 选择年龄后下一步 | 显示级别+兴趣标签选择 | ☐ |
| 78 | 第3步-课本 | 选择级别后下一步 | 显示课本版本/年级/学期选择 | ☐ |
| 79 | 跳过功能 | 点击跳过 | 直接保存默认画像，返回首页 | ☐ |
| 80 | 完成采集 | 3步全部选择完成 | 画像保存成功，跳转首页 | ☐ |

### P5: 背诵检查页 (pages/recite-check) ⭐核心交互

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 81 | 第一关-补阙填词 | 进入背诵检查 | 显示缺字填空界面 | ☐ |
| 82 | 填词提交 | 填写答案后提交 | 显示本关得分，≥60分可进下一关 | ☐ |
| 83 | 第二关-排序归位 | 通过第一关后 | 显示乱序行，点击交换排序 | ☐ |
| 84 | 排序提交 | 排好序后提交 | 显示本关得分 | ☐ |
| 85 | 第三关-语音背诵 | 通过第二关后 | 显示语音背诵界面（mock模式，输入文字） | ☐ |
| 86 | 语音提交 | 输入识别文本后提交 | 显示本关得分 | ☐ |
| 87 | 关卡未通过 | 任一关<60分 | 弹出鼓励提示，可重试 | ☐ |
| 88 | 三关全过 | 三关均≥60分 | 自动跳转到背诵结果页 | ☐ |

### P6: 背诵结果页 (pages/recite-result)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 89 | 成诵状态 | 三关全过进入 | 显示"成诵"状态，绿色主题 | ☐ |
| 90 | 鼓励状态 | 部分通过进入 | 显示"继续加油"鼓励文案 | ☐ |
| 91 | 正向框架评分 | 查看评分 | 显示"记对N字/N总字"，而非"错M字" | ☐ |
| 92 | 错题标记 | 查看错误字 | 琥珀色标记错误字，不显示红色× | ☐ |
| 93 | 返回首页 | 点击返回 | 回到首页，统计数据已更新 | ☐ |

### P7: 复习页 (pages/review)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 94 | 复习队列 | 进入复习页 | 显示今日到期复习列表 | ☐ |
| 95 | 紧急标记 | 查看逾期项 | 逾期项目有紧急标记 | ☐ |
| 96 | 自评-简单 | 复习后点"简单" | SM-2算法加大间隔 | ☐ |
| 97 | 自评-合适 | 复习后点"合适" | SM-2算法正常增长 | ☐ |
| 98 | 自评-困难 | 复习后点"困难" | SM-2算法缩短间隔 | ☐ |
| 99 | 空队列 | 无到期复习 | 显示"今日复习已完成"空状态 | ☐ |

### P8: 我的Tab (pages/profile)

| # | 测试项 | 操作 | 预期结果 | 通过 |
|---|--------|------|---------|------|
| 100 | 用户卡片 | 进入我的Tab | 显示头像+昵称（或默认头像） | ☐ |
| 101 | 统计摘要 | 查看统计区域 | 显示累计背诵/掌握/连续天数/今日 | ☐ |
| 102 | 画像入口 | 点击"画像" | 跳转到画像采集页 | ☐ |
| 103 | 节奏设置 | 点击"节奏" | 显示背诵节奏设置 | ☐ |
| 104 | 退出登录 | 点击退出 | 清除Token，回到登录态 | ☐ |

---

## 四、自动化单元测试对照表

> 79/79 全部通过 ✅

| 测试文件 | 用例数 | 覆盖模块 | 关键场景 |
|----------|--------|---------|---------|
| `test_health.py` | 1 | 健康检查 | /health 端点 |
| `test_auth.py` | 13 | 认证 | 登录/刷新/用户信息/401 |
| `test_profile.py` | 13 | 画像 | 默认值/全字段/部分/interests/课本/节奏/404 |
| `test_recite.py` | 22 | 背诵 | 并发守卫/三关检查/成诵/放弃/列表 |
| `test_review.py` | 10 | 复习 | 队列/SM-2(easy/good/hard)/统计 |
| `test_stats.py` | 5 | 统计 | 空/有数据/连续天数/今日 |
| `test_daily_v2.py` | 5 | 每日推荐 | 历史/分页/引擎/换诗限制 |
| `test_poems.py` | 5 | 诗词 | 列表/详情/搜索/筛选 |
| `test_favorites.py` | 5 | 珍藏 | 添加/取消/列表/404 |
| **合计** | **79** | — | — |

### 运行命令

```bash
cd C:\Users\ln\WorkBuddy\2026-06-10-dev\daily-poem-miniapp\backend

# 使用项目 venv
.venv\Scripts\python.exe -m pytest tests/ -v --tb=short

# 或使用 managed python
C:\Users\ln\.workbuddy\binaries\python\versions\3.13.12\python.exe -m pytest tests/ -v --tb=short
```

---

## 五、体验操作快速上手

### 1. 启动后端

```bash
cd C:\Users\ln\WorkBuddy\2026-06-10-dev\daily-poem-miniapp\backend
start-dev.bat
```

验证：浏览器访问 http://localhost:8000/docs 看到 Swagger UI

### 2. 启动前端

1. 打开微信开发者工具
2. 导入项目 `C:\Users\ln\WorkBuddy\2026-06-10-dev\daily-poem-miniapp\miniprogram`
3. AppID 使用测试号或填入你的 AppID
4. 编译运行

### 3. 快速验证核心流程

```
首页看推荐 → 点击进入诗词详情 → 点"开始背诵" → 
三关流程(填词→排序→语音) → 查看结果 → 
我的Tab看统计 → 临帖Tab看复习队列
```

---

## 六、已知限制（阶段5解决）

| 限制 | 说明 | 解决阶段 |
|------|------|---------|
| 语音识别为Mock | voice_check 直接接受文本参数，非真实ASR | T05-03 |
| AI场景图为占位 | scene_image_url 无真实图片生成 | T05-01 |
| 推荐理由为模板 | reason_type=festival/tag 等，但文案为固定模板 | T05-02 |
| 无分享卡片 | 前端Canvas分享功能未实现 | T05-05 |
| 无诗词库浏览 | 全量浏览+搜索页面未实现 | T05-06 |
| 无日历统计 | 背诵日历视图未实现 | T05-07 |
| Tabbar图标为占位 | 当前为1px占位图 | 待替换 |

---

*文档结束。齐活林（Qi）出品。*
