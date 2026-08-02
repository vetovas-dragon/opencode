# 在线问诊教学系统

面向医疗教学场景的在线问诊教学系统：医生、医学生、患者三方联动，内置汉语—彝语双向语音互转，融合教学实训、在线问诊、健康档案、数据督导评估于一体。

## 技术栈

- 后端：Python 3.12 + FastAPI + SQLAlchemy + Celery + Redis
- 前端：Vue3 + TypeScript + Vite + Element Plus（PC）/ Vant（移动）
- 数据：MySQL 8 / Redis / Elasticsearch / MinIO
- 部署：Docker Compose

## 目录结构

```
my-project/
├── PRD.md            # 产品需求文档（V1.1）
├── backend/          # FastAPI 后端
├── frontend/         # Vue3 前端
├── deploy/           # 部署编排（docker-compose / nginx）
└── docs/             # 设计文档（数据库设计等）
```

## 快速启动

```bash
# 1. 复制环境变量
cp backend/.env.example backend/.env

# 2. 构建并启动全部服务（MySQL/Redis/MinIO/后端/前端）
docker compose -f deploy/docker-compose.yml up -d --build

# 3. 访问
#    前端：http://localhost:8080
#    后端接口文档：http://localhost:8000/docs
```

## 本地开发

```bash
# 后端（需要本地 MySQL/Redis，或仅启动 compose 中基础组件）
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 初始化管理员账号（幂等）
cd backend && PYTHONPATH=. python scripts/seed_admin.py

# 前端
cd frontend
npm install
npm run dev
```

### 默认管理员账号

| 角色 | 账号 | 密码 |
| --- | --- | --- |
| 管理员 | 13900000000 | admin123456 |

管理员端地址：`/admin`（身份审核、全局概览）。医生/医学生注册后须管理员审核通过方可登录；患者注册即时生效。

详见 `docs/db-design.md` 与 PRD.md。
