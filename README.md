# Claude Code History Cleaner

Web 端 Claude Code 项目历史清理工具，可视化空间占用，批量清理闲置项目。

## 功能

**概览仪表盘**
- 项目数量、总磁盘占用、配置大小、闲置项目数（>10 天未活跃）
- 自动健康分析：配置过大、闲置过多、微型项目过多、项目数过多

**项目历史管理**
- 浏览、搜索、排序（按路径 / 最近启动 / 大小）
- 比例条形图直观对比各项目空间占用
- 批量操作：全选、取消全选、选中最大 10 个、删除选中
- 保存后同步清理 `~/.claude/projects/` 磁盘目录

## 快速开始

无需安装，直接使用 npx（从 GitHub 拉取运行）：

```bash
npx github:minimallism/claude-code-history-cleaner
```

或克隆后本地启动：

```bash
git clone https://github.com/minimallism/claude-code-history-cleaner.git
cd claude-code-history-cleaner
python3 server.py
```

浏览器打开 `http://localhost:8765`。

## 依赖

仅使用 Python 标准库，无需安装第三方包。

- Python 3.10+

## 配置文件路径

| 类型 | 路径 |
|------|------|
| Claude Code | `~/.claude.json` |

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` | 返回管理界面 |
| GET | `/api/config` | 获取配置文件内容及项目磁盘占用 |
| POST | `/api/save` | 保存配置并清理已删除项目的磁盘数据 |

## 项目结构

```
claude-code-history-cleaner/
├── package.json   # npm 包配置（CLI 入口）
├── bin/
│   └── cli.js     # Node.js CLI 启动器
├── server.py      # Python HTTP 后端（标准库）
├── index.html     # 单页前端界面（零依赖）
└── README.md
```

## 发布到 npm

如果你需要自行发布：

```bash
# 1. 登录 npm（首次）
npm login

# 2. 发布
npm publish --access public

# 3. 发布后用户即可一行启动（npm 方式）
npx claude-code-history-cleaner
```

未发布 npm 时，也可直接从 GitHub 启动：

```bash
npx github:minimallism/claude-code-history-cleaner
```

## 安全说明

- 直接读写本地 Claude 配置文件（`~/.claude.json`）
- 删除项目历史记录时同步清理 `~/.claude/projects/` 对应目录
- 仅监听本地 `localhost`，不对外暴露

## License

MIT
