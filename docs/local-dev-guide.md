# 天天半首诗 - 本地开发快速启动指南

## 前置条件

- Docker Desktop 已安装（https://www.docker.com/products/docker-desktop/）
- 腾讯云账号已开通（混元 API + ASR + COS）

---

## 第一步：开通腾讯云 COS（10分钟）

1. 打开 https://console.cloud.tencent.com/cos
2. 点 **「创建存储桶」**：
   - 名称：`daily-poem-images-1305326598`
   - 所属地域：**广州（ap-guangzhou）**
   - 访问权限：**私有读写**（推荐，通过签名 URL 访问）
3. 点 **「确定」**，等待创建完成
4. 记录桶名称，填入 `.env` 的 `COS_BUCKET` 字段

> 不建多个桶，所有 AI 场景图存在同一个桶，用路径前缀区分：`scenes/2026/06/xxx.png`

---

## 第二步：填写后端 `.env` 文件

```bash
# 进入项目目录
cd C:\Users\ln\WorkBuddy\2026-06-08-09-30-24\repo-temp\backend

# 复制模板
cr .env.example .env
```

然后编辑 `.env`，填入真实值：

| 字段 | 取值来源 | 示例 |
|------|---------|------|
| `WECHAT_APPSECRET` | 【微信公众平台】→【开发管理】→【开发设置】→ AppSecret | 需你自己查 |
| `DATABASE_URL` | 本地 Docker 不用改 / 云端再换 | — |
| `REDIS_URL` | 本地 Docker 不用改 / 云端再换 | — |
| `JWT_SECRET` | 本地随便填，生产必须换 | `openssl rand -hex 32` 生成 |
| `HUNYUAN_API_KEY` | 腾讯云控制台 → 混元 → API 密钥管理 | `sk-xxx...` |
| `TENCENT_SECRET_ID` | 腾讯云控制台 → 访问管理 → API 密钥管理 → SecretId | `AKID...` |
| `TENCENT_SECRET_KEY` | 同上 → SecretKey | — |
| `COS_BUCKET` | 第一步创建的桶名 | `daily-poem-images-1305326598` |

---

## 第三步：启动本地数据库（Docker）

```bash
# 进入项目根目录
cd C:\Users\ln\WorkBuddy\2026-06-08-09-30-24\repo-temp

# 启动 PostgreSQL + Redis（后台运行）
docker compose up -d postgres redis

# 等待 10 秒，检查是否启动成功
docker compose ps

# 查看日志（确认无报错）
docker compose logs -f postgres
```

预期输出：
```
NAME                  STATUS
daily-poem-pg         running (healthy)
daily-poem-redis      running (healthy)
```

---

## 第四步：初始化数据库

```bash
# 确保 Alembic 可用（先本地安装依赖）
cd C:\Users\ln\WorkBuddy\2026-06-08-09-30-24\repo-temp\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 执行数据库迁移
alembic upgrade head

# 导入首批诗词数据
python scripts/seed_poems.py
```

---

## 第五步：启动后端服务

```bash
# 方式 A：用 Docker（推荐，环境隔离）
cd C:\Users\ln\WorkBuddy\2026-06-08-09-30-24\repo-temp
docker compose up -d backend
docker compose logs -f backend   # 查看启动日志

# 方式 B：本地直接启动（方便调试）
cd C:\Users\ln\WorkBuddy\2026-06-08-09-30-24\repo-temp\backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后访问：http://localhost:8000/docs （Swagger UI）

---

## 常见问题

### Q：Docker 启动报错 `port already allocated`
A：修改 `docker-compose.yml` 中的端口映射，例如 `"5433:5432"`（PostgreSQL）和 `"6380:6379"`（Redis）

### Q：本地没有 Docker 怎么办？
A：直接安装原生 PostgreSQL 和 Redis：
- PostgreSQL：https://www.postgresql.org/download/windows/
- Redis（Windows 移植版）：https://github.com/microsoftarchive/redis/releases
- 然后 `.env` 中 `DATABASE_URL` 和 `REDIS_URL` 改为 `localhost` + 本地端口

### Q：不知道微信小程序 AppSecret？
A：登录 https://mp.weixin.qq.com → 开发管理 → 开发设置 → AppSecret → 生成 / 查看

---

## 下一步：开始写代码

环境就绪后，告诉我「**开始写代码**」，我会拉起工程师寇豆码，按架构文档的任务列表（T01-01 起）逐任务实现。
