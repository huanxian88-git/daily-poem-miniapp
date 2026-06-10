# 天天半首诗 · 阶段2 单元测试 Checklist

> 执行时间：2026-06-10 13:50 | 运行环境：Python 3.13.12 + SQLite 内存 + DEV_MODE
> 测试结果：**37/37 PASSED** ✅ | 耗时 4.07s

---

## 一、画像模块（test_profile.py）— 新增 13 条

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| P01 | `test_profile_get_defaults` | 登录后画像全部默认值（age_group=None, recite_rhythm=every_2_days, is_student=False…） | ✅ |
| P02 | `test_profile_get_unauthorized` | 未登录 GET /profile → 401 | ✅ |
| P03 | `test_profile_get_not_found` | 画像被删后 GET → 404 | ✅ |
| P04 | `test_profile_update_partial` | 部分更新（仅改 age_group），未传字段保持原值 | ✅ |
| P05 | `test_profile_update_all_fields` | 全字段更新（9 个字段全部写入验证） | ✅ |
| P06 | `test_profile_update_interests_empty` | interests 传空列表 → 清空为 [] | ✅ |
| P07 | `test_profile_update_textbook` | 课本绑定三字段（version/grade/semester）独立更新 | ✅ |
| P08 | `test_profile_update_is_student_toggle` | is_student 默 False→True→False 往返切换 | ✅ |
| P09 | `test_profile_update_custom_rhythm` | recite_rhythm=custom + custom_days=5 | ✅ |
| P10 | `test_profile_create_idempotent` | POST /profile 画像已存在时返回现有记录 | ✅ |
| P11 | `test_profile_interests_serialization` | interests 逗号存→列表出往返序列化 | ✅ |
| P12 | `test_profile_update_unauthorized` | 未登录 PUT /profile → 401 | ✅ |
| P13 | `test_profile_update_then_get` | PUT 更新后再 GET 验证数据持久化 | ✅ |

### 画像字段覆盖矩阵

| 字段 | 读(默认) | 写(全量) | 写(部分) | 边界值 | 序列化 |
|------|:--------:|:--------:|:--------:|:------:|:------:|
| age_group | P01 | P05 | P04 | — | — |
| level | P01 | P05 | — | — | — |
| interests | P01 | P05 | — | P06 | P11 |
| recite_rhythm | P01 | P05 | — | — | — |
| recite_rhythm_custom_days | P01 | P05 | — | P09 | — |
| textbook_version | P01 | P05 | — | P07 | — |
| textbook_grade | P01 | P05 | — | P07 | — |
| textbook_semester | P01 | P05 | — | P07 | — |
| is_student | P01 | P05 | — | P08 | — |

---

## 二、鉴权模块（test_auth.py）— 原有 24 条

### 登录 (3 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A01 | `test_login_success` | DEV_MODE mock 登录成功，返回双 token | ✅ |
| A02 | `test_login_missing_code` | 缺少 code → 422 | ✅ |
| A03 | `test_login_wx_api_failure` | 微信 API 失败 → 400 | ✅ |

### Token 刷新 (4 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A04 | `test_refresh_token` | 正常刷新 → 新 access_token | ✅ |
| A05 | `test_refresh_invalid_token` | 无效 refresh_token → 401 | ✅ |
| A06 | `test_refresh_empty_token` | 空 refresh_token → 401/422 | ✅ |
| A07 | `test_refresh_with_access_token` | access_token 不能用于刷新 → 401 | ✅ |

### 用户信息 (3 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A08 | `test_get_me_with_token` | 带 token 获取用户信息 | ✅ |
| A09 | `test_get_me_without_token` | 无 token → 401 | ✅ |
| A10 | `test_get_me_invalid_token` | 无效 token → 401 | ✅ |

### 安全模块 (2 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A11 | `test_security_decode_token` | JWT 签发与解码一致性 | ✅ |
| A12 | `test_security_invalid_token` | 解码无效 token → None | ✅ |

### 画像 (2 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A13 | `test_profile_get` | GET /profile 基础读取 | ✅ |
| A14 | `test_profile_update` | PUT /profile 基础更新 | ✅ |

### 诗词 (4 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A15 | `test_poems_list` | 分页列表（含种子数据） | ✅ |
| A16 | `test_poem_detail` | 详情（title/author/is_favorited） | ✅ |
| A17 | `test_poem_scene` | 场景（scene_type/scene_desc） | ✅ |
| A18 | `test_poems_search` | 搜索（search=李白） | ✅ |
| A19 | `test_poems_filter_difficulty` | 难度筛选（difficulty=1） | ✅ |

### 每日推荐 (2 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A20 | `test_daily_today` | 今日推荐（poem/reason/can_switch） | ✅ |
| A21 | `test_daily_switch` | 换一首（switch_count/轮换诗词） | ✅ |

### 珍藏 (2 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| A22 | `test_favorite_add_and_list` | 添加珍藏 + 列表查询 | ✅ |
| A23 | `test_favorite_remove` | 取消珍藏 | ✅ |

### 健康检查 (1 条)

| # | 用例 | 验证点 | 结果 |
|---|------|--------|:----:|
| H01 | `test_health_check` | /health 端点可用 | ✅ |

---

## 三、API 端点覆盖总览

| 模块 | 端点 | 方法 | 测试条数 | 覆盖 |
|------|------|------|:--------:|:----:|
| auth | /api/v1/auth/login | POST | 3 | ✅ |
| auth | /api/v1/auth/refresh | POST | 4 | ✅ |
| auth | /api/v1/auth/me | GET | 3 | ✅ |
| profile | /api/v1/profile | GET | 4 | ✅ |
| profile | /api/v1/profile | PUT | 8 | ✅ |
| profile | /api/v1/profile | POST | 1 | ✅ |
| poems | /api/v1/poems | GET | 3 | ✅ |
| poems | /api/v1/poems/{id} | GET | 1 | ✅ |
| poems | /api/v1/poems/{id}/scene | GET | 1 | ✅ |
| daily | /api/v1/daily/today | GET | 1 | ✅ |
| daily | /api/v1/daily/switch | POST | 1 | ✅ |
| favorites | /api/v1/favorites | GET | 1 | ✅ |
| favorites | /api/v1/favorites/{id} | POST | 1 | ✅ |
| favorites | /api/v1/favorites/{id} | DELETE | 1 | ✅ |
| health | /health | GET | 1 | ✅ |
| **合计** | **17 个端点** | — | **37** | **100%** |

---

## 四、待优化项（非阻塞）

| 优先级 | 项目 | 说明 |
|:------:|------|------|
| P2 | `datetime.utcnow()` 弃用警告 | 361 条 DeprecationWarning，建议统一改为 `datetime.now(datetime.UTC)` |
| P2 | pytest-asyncio loop scope 未配置 | 建议在 pyproject.toml 添加 `asyncio_default_fixture_loop_scope = "function"` |
| P3 | Pydantic V2 ConfigDict 弃用 | `class Config` → `model_config = ConfigDict(...)` |
