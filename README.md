# AI 掼蛋训练

一个面向掼蛋规则学习与决策复盘的全栈训练项目。项目包含完整牌型识别、出牌校验、三种规则 AI、行为追踪、人格评分、LLM Provider、FastAPI 接口、SQLite 持久化，以及支持安装和离线启动的 UniApp PWA 前端。

项目仅用于智力运动训练，不包含赌博、金币、充值或用户系统。

## 技术栈

- 后端：Python 3.9+、FastAPI、Pydantic
- 游戏引擎：纯 Python 规则算法
- 数据库：SQLite、SQLAlchemy
- 前端：UniApp、Vue 3、uView Plus
- 状态管理：Pinia
- HTTP：Axios（通过 `uni.request` 适配 H5 和小程序）
- LLM：Provider 模式，支持 OpenAI、通义、豆包和无网络 Mock

## 目录结构

```text
ai-guandan-training/
├── backend/
│   ├── app/
│   │   ├── api/                 # FastAPI Router、Pydantic 模型、统一异常
│   │   ├── database/            # SQLAlchemy 模型、CRUD、数据库初始化
│   │   ├── engine/              # 游戏规则、AI、行为追踪、人格评分
│   │   ├── llm/                 # Prompt 与 LLM Provider
│   │   └── main.py              # FastAPI 主入口
│   ├── tests/                   # Python 单元测试
│   ├── main.py                  # backend.main 兼容入口
│   └── requirements.txt
├── frontend/
│   ├── services/                # Axios 请求封装
│   ├── components/              # 公共 UI 组件
│   ├── pages/                   # 七个 UniApp 页面
│   ├── store/                   # Pinia 状态
│   ├── styles/                  # 绿色棋牌主题
│   ├── static/                  # PWA 清单、Service Worker、图标、404
│   ├── App.vue
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── main.js
│   ├── manifest.json
│   ├── pages.json
│   └── package.json
├── docker-compose.yml           # 前后端容器编排
├── .env.example                 # Docker 与 LLM 环境变量模板
└── README.md
```

## 快速开始

### 1. 克隆项目

```bash
git clone <repository-url>
cd ai-guandan-training
```

### 2. 启动后端

建议使用虚拟环境：

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload
```

Windows PowerShell 激活方式：

```powershell
.venv\Scripts\Activate.ps1
```

后端默认地址：`http://127.0.0.1:8000`

- Swagger：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`
- 健康检查：`http://127.0.0.1:8000/health`

也可以在仓库根目录使用兼容入口：

```bash
uvicorn backend.main:app --reload
```

### 3. 启动前端

新开终端：

```bash
cd frontend
npm install
npm run dev:h5
```

开发环境默认通过 Vite 的 `/api` 代理自动连接 `http://127.0.0.1:8000`。如需修改，在 `frontend/.env.local` 中覆盖：

```dotenv
VITE_API_BASE_URL=/api
VITE_API_PROXY_TARGET=http://127.0.0.1:8000
```

常用前端命令：

```bash
npm run dev:h5             # H5 开发模式
npm run build:h5           # H5 生产构建
npm run dev:mp-weixin      # 微信小程序开发构建
npm run build:mp-weixin    # 微信小程序生产构建
```

微信小程序构建产物位于 `frontend/dist/build/mp-weixin`，使用微信开发者工具导入即可。

## PWA 与浏览器访问

H5 生产构建包含：

- Web App Manifest
- 192 / 512 PNG 应用图标
- Service Worker 应用壳缓存
- 启动 Loading
- History 路由和 404 页面
- 手机、平板和桌面响应式布局

开发环境可直接访问：

```text
http://localhost:5173/
http://localhost:5173/pages/training/index
http://localhost:5173/pages/game/index
http://localhost:5173/pages/recommend/index
http://localhost:5173/pages/settlement/index
http://localhost:5173/pages/report/index
http://localhost:5173/pages/history/index
```

Service Worker 仅在生产构建中注册，避免开发缓存干扰热更新。PWA 安装要求使用 HTTPS；`localhost` 在浏览器中视为安全来源。

## H5 生产部署

### 构建

```bash
cd frontend
npm install
npm run build:h5
```

产物目录：

```text
frontend/dist/build/h5
```

### Nginx 部署

将 H5 产物复制到站点目录，并使用 `frontend/nginx.conf`。关键配置是：

```nginx
location / {
    try_files $uri $uri/ /index.html;
}

location /api/ {
    proxy_pass http://127.0.0.1:8000/;
}
```

`try_files` 用于支持 History 路由直接刷新，`/api` 自动反向代理到 FastAPI。

生产环境请配置 HTTPS，否则浏览器不会启用 PWA 安装和离线能力。

### Vercel 部署

前端配置文件为 `frontend/vercel.json`。

1. 在 Vercel 导入仓库。
2. 将 Root Directory 设置为 `frontend`。
3. Build Command 使用 `npm run build:h5`。
4. Output Directory 使用 `dist/build/h5`。
5. 设置生产环境变量：

```dotenv
VITE_API_BASE_URL=https://你的后端域名
VITE_API_TIMEOUT=10000
VITE_PUBLIC_BASE=/
```

6. 部署。`vercel.json` 已配置 History 路由回退、Manifest 类型和 Service Worker 禁止强缓存。

Vercel 只托管前端，FastAPI 需要部署到可公开访问的 Docker 主机或其他 Python 容器平台。

### Netlify 部署

前端配置文件为 `frontend/netlify.toml`。

1. 在 Netlify 导入仓库。
2. Base directory 设置为 `frontend`。
3. Build command 使用 `npm run build:h5`。
4. Publish directory 使用 `dist/build/h5`。
5. 设置生产环境变量：

```dotenv
VITE_API_BASE_URL=https://你的后端域名
VITE_API_TIMEOUT=10000
VITE_PUBLIC_BASE=/
```

6. 部署。`netlify.toml` 和 `_redirects` 已配置 SPA 路由回退。

## Android APK 打包

推荐使用 HBuilderX 云打包：

1. 安装 HBuilderX，并登录 DCloud 账号。
2. 使用 HBuilderX 打开 `frontend` 目录。
3. 在 `frontend/manifest.json` 中设置正式的 UniApp AppID。
4. 打开“发行” → “原生 App-云打包”。
5. 选择 Android，填写应用包名、版本号和签名证书。
6. 首次测试可使用 DCloud 公共测试证书；正式发布必须使用自己的 Android 签名证书。
7. 选择 APK 或 AAB，提交云打包并下载产物。

如使用本地 Android 原生打包，请从 DCloud 下载对应版本的 App 离线 SDK，将 UniApp 构建资源放入原生工程，并使用 Android Studio 生成签名 APK/AAB。当前项目不包含签名文件，避免敏感证书进入仓库。

## Docker 部署

仓库包含可选的前后端 Docker 配置：

```bash
cp .env.example .env
docker compose up
```

启动后访问：

```text
http://localhost/
```

Nginx 会将 `/api` 转发到 FastAPI；SQLite 文件保存在 Docker 命名卷 `game-data` 中。

默认端口：

```text
Frontend: http://localhost/
Backend:  http://localhost:8000/
Swagger:  http://localhost:8000/docs
```

需要后台运行时：

```bash
docker compose up -d
```

停止容器：

```bash
docker compose down
```

停止并删除 SQLite 数据卷：

```bash
docker compose down -v
```

## 页面流程

```text
首页 → 开始训练 → 牌桌 → AI 推荐 → 结算 → AI 报告
  └──────────────────────────────→ 历史记录
```

后端未启动时，前端会进入离线演示模式，页面流程仍可浏览；真实出牌、推荐和历史数据需要启动后端。

## API 说明

所有业务接口返回 JSON。错误响应格式统一为：

```json
{
  "success": false,
  "error": {
    "code": 400,
    "message": "错误说明",
    "details": null
  }
}
```

### `POST /start_game`

开始一局游戏。

```json
{
  "player_names": ["你", "AI-1", "AI-2", "AI-3"]
}
```

响应包含游戏状态和当前行动玩家的 `current_hand`。

### `POST /play`

按当前手牌数组下标出牌，下标不能重复。

```json
{
  "card_indices": [0, 1]
}
```

### `POST /pass`

当前玩家过牌。拥有首出主动权时不能过牌。无需请求体。

### `POST /recommend`

获取当前玩家的规则 AI 推荐，不执行出牌。

```json
{
  "strategy": "balanced"
}
```

`strategy` 可选：`aggressive`、`balanced`、`conservative`。

### `GET /history`

返回当前内存牌局的日志与回合历史。

### `GET /health`

返回：

```json
{ "status": "ok" }
```

## 数据库说明

数据库使用 SQLite，文件路径为：

```text
backend/game.db
```

首次启动 FastAPI 时会自动创建数据库和数据表，无需手动迁移。建表操作幂等，不会覆盖已有数据。

数据表：

- `game_record`：牌局开始、结束、胜者和状态
- `behavior_log`：每一步行为、思考时间、PASS、炸弹、队友协作等
- `personality_score`：攻击、均衡和保守方向的持久化评分

手动初始化：

```bash
cd backend
python3 -m app.database.init_db
```

数据库 CRUD 位于 `backend/app/database/sqlite.py`。项目不包含用户表或用户系统。

## LLM 配置

LLM Provider 不是启动项目的必需条件。未配置 Key 时可以直接使用 `MockProvider`。

真实 Provider 从环境变量读取配置，源码不保存 API Key：

```bash
# OpenAI
export OPENAI_API_KEY=""
export OPENAI_MODEL=""

# 通义百炼
export DASHSCOPE_API_KEY=""
export TONGYI_MODEL=""

# 火山方舟 / 豆包
export ARK_API_KEY=""
export DOUBAO_MODEL=""
```

也可以在构造 Provider 时显式传入 `api_key`、`model` 和 `endpoint`。

统一调用方式：

```python
from app.llm.provider import MockProvider

provider = MockProvider()
result = provider.analyze(
    game={"phase": "finished"},
    behavior_scores={
        "attack": 60,
        "cooperation": 70,
        "risk": 50,
        "hesitation": 40,
        "emotion": 80,
    },
    personality="均衡稳健型",
)
```

所有 Provider 统一返回：

```json
{
  "summary": "牌局总结",
  "mistake": "主要问题",
  "personality": "人格分析",
  "suggestion": "改进建议"
}
```

Prompt 全部位于 `backend/app/llm/prompt.py`。

## 测试与检查

运行后端全部测试：

```bash
python3 -m unittest discover -s backend/tests -p "test_*.py" -v
```

检查 Python 编译：

```bash
python3 -m compileall -q backend
```

检查前端生产构建：

```bash
cd frontend
npm run build:h5
npm run build:mp-weixin
```

## 运行注意事项

- FastAPI 当前保存单个内存牌局，重启服务后当前局状态会清空。
- SQLite 行为记录和人格评分不会随服务重启丢失。
- H5 本地开发默认允许 `localhost` / `127.0.0.1` 的 5173、5174 端口跨域访问。
- 如需额外前端来源，可设置逗号分隔的 `CORS_ORIGINS` 环境变量。
- 环境变量模板位于 `frontend/.env.example`；开发和生产默认值分别位于 `.env.development`、`.env.production`。
- PWA 更新后如需立即刷新离线缓存，可在浏览器开发者工具的 Application → Service Workers 中执行 Update。
- 生产环境请通过环境变量管理所有 API Key，不要提交 `.env`、`game.db`、`node_modules` 或 `dist`。
