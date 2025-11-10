# Bing Wallpaper Action - 项目开发文档

## 项目概述

Bing Wallpaper Action 是一个自动抓取 Bing 每日壁纸并提供多种访问方式的项目。该项目通过 GitHub Actions 自动化抓取来自不同地区的 Bing 壁纸，包括中文、英文、日文等 9 种语言/地区版本，并将数据存储在 JSON 文件中，同时生成包含所有壁纸的 README.md 文件。

## 项目架构

### 核心组件

1. **主抓取模块** (`main.py`) - 负责从 Bing API 获取壁纸数据
2. **批量处理模块** (`ALL.py`) - 根据命令行参数处理不同地区数据
3. **Redis 同步模块** (`post_to_redis.py`) - 将壁纸数据同步到 Redis 数据库
4. **README 生成器** (`make_readme.py`) - 生成包含所有壁纸的 README 文件
5. **API 接口** (`api/index.py`) - Vercel 部署的跳转 API

### 数据存储结构

```
data/
├── {region}_all.json        # 所有壁纸数据（完整历史）
├── {region}_update.json     # 最新壁纸数据
├── {region}_temp.json       # 临时文件（新增壁纸）
├── {region}_daily_log/      # 每日日志文件
├── template_all.json        # 完整数据模板
└── template_update.json     # 更新数据模板
```

其中 region 包括:
- `zh-CN` - 中文（中国）
- `en-US` - 英语（美国）
- `ja-JP` - 日语（日本）
- `de-DE` - 德语（德国）
- `en-CA` - 英语（加拿大）
- `en-GB` - 英语（英国）
- `en-IN` - 英语（印度）
- `fr-FR` - 法语（法国）
- `it-IT` - 意大利语（意大利）

## 工作流程

### 1. 自动化抓取流程

项目使用 GitHub Actions 每天 00:30 UTC 执行抓取任务：

1. 依次处理每个地区（zh-CN, en-US, ja-JP, de-DE, en-CA, en-GB, en-IN, fr-FR, it-IT）
2. 对每个地区：
   - 检查数据文件是否存在，不存在则创建
   - 调用 `main.py` 抓取最新壁纸
   - 调用 `post_to_redis.py` 同步到 Redis
3. 执行 `make_readme.py` 生成最新的 README.md
4. 提交所有变更到主分支

### 2. 数据处理逻辑

- 检查 Bing API 的 `HPImageArchive` 数据
- 比较 `startdate` 避免重复抓取
- 将新增壁纸追加到 `_all.json` 文件
- 更新 `_update.json` 为最新数据
- 记录到每日日志

## 关键功能模块

### main.py - 主抓取模块

```python
def main(run_type):
    # 从 Bing API 获取壁纸数据
    data = requests.get(f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=8&mkt={run_type}").json()
    
    # 保存每日日志到 data/{run_type}_daily_log/
    # 更新 {run_type}_all.json（历史数据）
    # 更新 {run_type}_update.json（最新数据）
```

### ALL.py - 批量处理模块

- 接收命令行参数作为地区代码
- 初始化必要的数据文件和目录
- 调用 main 和 post_to_redis 模块
- 3秒延迟后继续处理下一个地区

### make_readme.py - README 生成器

- 读取所有地区的壁纸数据
- 按日期对齐不同地区数据
- 生成 3x3 表格格式的 README.md
- 包含可下载的 4K 图片链接

### post_to_redis.py - Redis 同步模块

- 读取临时数据文件
- 将壁纸 URL 添加到 Redis 集合中
- 用于 API 服务的数据源

## 依赖管理

### Python 依赖 (`requirements.txt`)

- `redis~=4.1.4` - Redis 数据库连接
- `requests~=2.25.1` - HTTP 请求
- `PyMySQL~=1.0.2` - MySQL 数据库支持（未在主要代码中使用）

### 外部服务

- **Redis** - Upstash Redis 服务 (apn1-destined-giraffe-32369.upstash.io)
- **Vercel** - API 服务部署平台
- **GitHub Actions** - 自动化任务执行环境

## API 接口

### API 功能

`api/index.py` 实现了基于 Vercel 的 307 重定向服务：

- 从 Redis 随机获取一张壁纸 URL
- 执行 307 临时重定向到真实图片地址
- 支持 CORS 和缓存控制

### 部署配置

- 使用 Vercel 平台部署
- 环境变量需要设置 PASSWORD（Redis 密码）
- 返回 307 重定向响应

## 开发实践

### 代码约定

- 使用 UTF-8 编码
- 变量和函数命名使用英文
- 时间格式统一为 `"%Y-%m-%d %H:%M:%S"`
- 错误日志中包含时间戳

### 数据格式

- JSON 数据包含 `title`, `copyright`, `enddate`, `url`, `urlbase` 等字段
- 所有数据文件使用 UTF-8 编码
- 日期格式使用 YYYYMMDD 或 YYYY-MM-DD

### 项目配置

- GitHub Actions 每日 00:30 UTC 执行
- 支持手动触发和仓库事件触发
- 使用 GitHub Token 进行提交授权

## 部署说明

### GitHub Actions 配置

在 `.github/workflows/main.yaml` 中定义：

- 每日定时执行抓取任务
- 依次处理 9 个地区的壁纸数据
- 生成 README.md 文件
- 自动提交变更到 main 分支

### 环境变量

需要在 GitHub Secrets 中设置：

- `PASSWORD` - Redis 密码
- `MY_GIT_TOKEN` - GitHub 令牌

### Vercel 部署

- 自动部署 `api/index.py` 为 HTTP 服务
- 需要配置相同的 Redis 密码环境变量

## 维护指南

### 数据备份

- 项目数据以 JSON 格式保存在仓库中
- 每日抓取数据也会保存在 `daily_log` 文件夹中

### 故障排查

- 检查 GitHub Actions 运行日志
- 验证 Redis 连接和密码
- 确认 Bing API 可用性

### 扩展性

- 轻松添加新的地区支持
- 可扩展到其他图片源
- API 可以添加更多功能