# Claude Config Editor

基于 Web 的 Claude 配置文件编辑器，支持 Claude Code (CLI) 和 Claude Desktop 的 `.claude.json` 配置管理。

## 功能

- **概览** — 配置文件大小、项目数量、MCP 服务器数量、累计启动次数，自动诊断健康状态
- **项目历史** — 浏览、搜索、排序、批量选中/删除对话项目历史记录
- **MCP 服务器** — 添加/删除 MCP 服务器（Command + Args）
- **原始 JSON** — 语法高亮查看完整配置，支持复制到剪贴板
- **保存 & 备份** — 修改后保存回磁盘，自动创建备份，支持手动下载备份

## 快速开始

```bash
# 启动服务
python3 server.py

# 指定配置类型（可选）
python3 server.py code      # Claude Code (CLI)
python3 server.py desktop   # Claude Desktop
```

浏览器打开 `http://localhost:8765`。

## 依赖

仅使用 Python 标准库，无需安装第三方包。

- Python 3.10+

## 配置文件路径

| 类型 | 路径 |
|------|------|
| Claude Code (CLI) | `~/.claude.json` |
| macOS Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows Desktop | `%APPDATA%/Claude/claude_desktop_config.json` |
| Linux Desktop | `~/.config/Claude/claude_desktop_config.json` |

## 项目结构

```
claude-config-editor/
├── server.py      # Python HTTP 后端
├── index.html     # 单页前端界面
└── README.md
```

## 安全说明

- 直接读写本地 Claude 配置文件
- 保存时自动备份为 `.claude.json.backup`
- 删除项目历史记录时会同步清理 `~/.claude/projects/` 目录

## License

MIT
