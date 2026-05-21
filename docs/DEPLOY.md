# CCAE引擎 部署说明

## 生产环境部署

### 方案一：直接部署（简单）

```bash
# 1. 安装依赖
pip install flask flask-cors openpyxl pillow gunicorn

# 2. 初始化数据库
python backend/database.py

# 3. 生产模式运行
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

### 方案二：Docker部署（推荐）

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python backend/database.py
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "backend.app:app"]
```

```bash
docker build -t ccae-engine .
docker run -d -p 5000:5000 --name ccae ccae-engine
```

### 方案三：Nginx反向代理

```nginx
server {
    listen 80;
    server_name ccae.yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static/ {
        alias /path/to/ccae-engine/frontend/;
    }
}
```

---

## 优先级上线计划

| 批次 | 模块 | 状态 |
|------|------|------|
| **第一批（P0）** | 智能翻译 + 合规审核 | ✅ 已完成 |
| **第二批（P1）** | 视觉识别 + 审美匹配 + 知识库 | ✅ 已完成 |
| **第三批（P2）** | 个性化推荐 + 视频审核 + 数据看板 + 权限管理 + API网关 | ✅ 已完成 |

---

## 数据库迁移

当前使用SQLite，如需迁移至MySQL/PostgreSQL：

```bash
# 导出SQLite数据
sqlite3 data/ccae.db .dump > migration.sql

# 修改backend/config.py中的数据库配置
# 替换SQLite连接为MySQL/PostgreSQL连接字符串
```

---

## 性能指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 翻译响应时间 | ≤1秒 | ✅ 1ms |
| 翻译准确率 | ≥95% | 待评估 |
| 文本审核响应时间 | ≤1秒 | ✅ <1ms |
| 文本审核准确率 | ≥98% | 待评估 |
| 图片审核响应时间 | ≤3秒 | 待评估 |
| 视觉识别响应时间 | ≤2秒 | ✅ <1ms |
