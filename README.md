# 每日背诗 - 微信小程序

> 基于日期/节日智能推荐的古诗词鉴赏与背诵工具

## 项目简介

「每日背诗」是一款微信小程序，帮助用户通过科学的艾宾浩斯记忆曲线进行古诗词背诵。每日根据日期、节日、节气和课本进度智能推荐一首诗词，提供三种背诵检查模式（补阙填词、排序归位、语音背诵），让背诗变得有趣且高效。

## 功能特性

- 📅 **智能推荐**：根据日期、节日、节气、课本进度每日推荐一首诗词
- 🎯 **三关背诵**：补阙填词 / 排序归位 / 语音背诵，多维度检验背诵效果
- 📊 **艾宾浩斯复习**：基于记忆曲线自动调度复习，科学抗遗忘
- 🎨 **AI 场景联想**：腾讯混元大模型生成场景图和联想文字，增强记忆
- 📝 **临帖临摹**：复习队列诗词支持临帖模式，眼手心合一
- 📚 **完整诗词库**：365首经典诗词，覆盖人教版1-9年级课本

## 技术架构

| 层级 | 技术栈 |
|------|--------|
| 前端 | 微信小程序原生开发（JS/WXML/WXSS） |
| 后端 | Python 3.13 + FastAPI + SQLAlchemy(async) |
| 数据库 | PostgreSQL 15+（腾讯云 TDSQL-C） |
| 缓存 | Redis 7+（腾讯云 Redis） |
| AI | 腾讯混元大模型 + 腾讯云 ASR 语音识别 |
| 部署 | 腾讯云 SCF Serverless + GitHub Actions CI/CD |

## 项目结构

```
daily-poem-miniapp/
├── backend/              # 后端 FastAPI 服务
│   ├── app/
│   │   ├── api/        # API 路由
│   │   ├── models/     # SQLAlchemy 模型
│   │   ├── schemas/    # Pydantic Schema
│   │   ├── services/   # 业务逻辑
│   │   └── core/      # 配置/安全/工具
│   ├── alembic/        # 数据库迁移
│   └── tests/          # 单元测试
├── miniprogram/         # 微信小程序前端
│   ├── pages/          # 页面
│   ├── components/     # 组件
│   └── utils/         # 工具函数
├── docs/                # 项目文档
│   ├── prd.md         # 产品需求文档 v3.3
│   ├── architecture.md # 系统架构设计 v1.2
│   ├── schedule.md     # 开发排期 v1.2
│   ├── scene-usecases.md  # 场景用例 148个
│   └── testing-plan.md    # 测试计划 v1.0
├── data/                # 数据文件
│   └── output/
│       ├── poems-all.json      # 365首诗词数据
│       ├── textbook_catalog.json  # 人教版课本目录
│       └── calendar_365.json     # 365天日历映射
└── scripts/              # 数据处理脚本
```

## 文档索引

| 文档 | 说明 |
|------|------|
| [PRD](docs/prd.md) | 产品需求文档，39个功能点，P0(26)/P1(13) |
| [架构设计](docs/architecture.md) | 系统架构，含Mermaid时序图/ER图 |
| [开发排期](docs/schedule.md) | WBS任务分解，6阶段18工作日(AI效能) |
| [场景用例](docs/scene-usecases.md) | 148个场景用例，P0(86)/P1(45)/P2(17) |
| [测试计划](docs/testing-plan.md) | 研发自测体系 + 自动化测试计划 |

## 快速启动

### 后端（本地开发）

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 前端（微信开发者工具）

1. 下载 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 导入 `miniprogram/` 目录
3. 在 `project.config.json` 中填入你的 AppID
4. 编译运行

## 小程序信息

| 项目 | 信息 |
|------|------|
| 小程序名称 | 每日背诗（审核中） |
| AppID | wxcb715f5de1dee100 |
| 主体 | 个人 |
| 服务端地域 | 广州 |

## 开发进度

- [x] PRD v3.3
- [x] 架构设计 v1.2
- [x] 开发排期 v1.2
- [x] 场景用例文档（148个）
- [x] 测试计划 v1.0
- [x] 诗词数据（365首）
- [x] 课本目录数据（133首）
- [x] 日历映射数据（365天）
- [ ] 阶段0：前置准备（进行中）
- [ ] 阶段1-6：开发实施

## 贡献

本项目由刘宁（[@huanxian88-git](https://github.com/huanxian88-git)）独立开发，作为北理工MEM学习实践项目。

## License

[MIT License](LICENSE)
