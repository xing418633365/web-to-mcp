---
name: url-to-mcp
description: 根据用户提供的网站 URL，自动分析网站结构，生成基于 Playwright 的 MCP Server 代码（Python/TypeScript 自动选型）+ mcp.json 配置，安装依赖并启动 stdio 模式。触发词：生成MCP、创建MCP Server、URL转MCP、网站自动化MCP、Playwright MCP。
description_zh: URL转MCP服务器生成器
description_en: URL-to-MCP server generator
disable: false
agent_created: true
---

# url-to-mcp

根据网站 URL 自动生成 Playwright MCP Server，一键配置并启动。

## When to use

用户提出以下需求时触发：
- "帮我给 XX 网站生成一个 MCP Server"
- "我想在 WorkBuddy 里自动化操作 XX 网站"
- "把 XX 网站的操作封装成 MCP"
- "创建一个能操作 XX 网站的 MCP"
- 提供一个 URL 并要求生成 MCP Server
- 任何涉及"网站 + MCP/自动化/Playwright"的组合需求

## Overview

本 skill 将：
1. 用 Playwright 访问目标网站，自动分析页面结构（表单、按钮、链接、数据列表等）
2. 基于分析结果，生成专用于该网站的 MCP Server 代码
3. 生成 mcp.json 配置项
4. 安装依赖并启动 stdio 模式
5. 验证 MCP Server 可正常工作

## Steps

### Step 1: 收集信息

向用户确认：
- **目标 URL**（必须）
- **网站用途简述**（可选，帮助生成更精准的工具函数）
- **需要的操作类型**（可选，默认：查询+表单填写+数据提取+截图）
- **语言偏好**（可选，默认自动选择：优先 Python，若环境不支持则选 TypeScript）

如果用户只提供了 URL，其余参数按默认值处理，不要反复追问。

### Step 2: 环境检测与语言选型

运行以下命令检测环境：

```bash
# 检测 Python
/Users/wangyichen/.workbuddy/binaries/python/versions/3.13.12/bin/python3 --version

# 检测 Node
/Users/wangyichen/.workbuddy/binaries/node/versions/20.18.0/bin/node --version

# 检测 pip (venv)
ls /Users/wangyichen/.workbuddy/binaries/python/envs/default/bin/pip
```

**语言选择规则**：
- Python venv 存在且可用 → 选 Python（FastMCP + Playwright）
- Python 不可用但 Node 可用 → 选 TypeScript（@modelcontextprotocol/sdk + Playwright）
- 都可用 → 优先 Python（FastMCP 开发效率更高）

### Step 3: 分析目标网站

使用 Playwright MCP 或 agent-browser skill 访问目标 URL，分析：

1. **页面标题和用途**
2. **表单元素**：input、textarea、select、button（记录 name/id/placeholder）
3. **可点击操作**：按钮、链接（记录文本和 href）
4. **数据列表/表格**：识别可提取的数据结构
5. **登录需求**：是否需要登录
6. **多页面结构**：是否有导航菜单、子页面

分析方式：
- 优先使用已连接的 Playwright MCP 工具（如果可用）
- 否则使用 agent-browser skill
- 如果以上都不可用，使用 WebFetch 抓取页面 HTML 分析

将分析结果记录为 JSON 格式，供后续代码生成使用。分析结构示例：

```json
{
  "url": "https://example.com",
  "title": "Example Site",
  "forms": [
    {"id": "search-form", "fields": [{"name": "q", "type": "text", "placeholder": "Search..."}], "submit": "Search"}
  ],
  "actions": [
    {"type": "button", "text": "Submit", "selector": "#submit-btn"},
    {"type": "link", "text": "Next Page", "href": "/page/2"}
  ],
  "data_tables": [
    {"selector": "table.data-table", "columns": ["Name", "Date", "Status"]}
  ],
  "requires_login": false
}
```

### Step 4: 生成 MCP Server 代码

#### Python 模板

生成文件：`~/.workbuddy/mcp-servers/{server-name}/main.py`

使用 @templates/python-server.py 模板，替换以下占位符：
- `{{SERVER_NAME}}`: 基于域名生成的标识符（如 example_com）
- `{{SITE_URL}}`: 目标网站 URL
- `{{SITE_DESCRIPTION}}`: 网站用途描述
- `{{TOOLS}}`: 基于网站分析生成的工具函数列表

**工具函数生成规则**：
- 每个表单 → 生成一个 `fill_and_submit_{form_name}` 工具
- 每个数据列表/表格 → 生成一个 `extract_{table_name}` 工具
- 网站截图 → 生成 `take_screenshot` 工具
- 页面导航 → 生成 `navigate_to_{page}` 工具
- 如果需要登录 → 生成 `login` 工具
- 通用 → 生成 `execute_custom_action` 工具（接收自定义 selector + action）

每个工具函数必须：
- 有清晰的 docstring（AI 靠这个决定何时调用）
- 参数有类型标注和描述
- 使用 Playwright 的 headless 模式
- 包含错误处理和超时设置
- 操作完成后自动关闭浏览器

#### TypeScript 模板

生成文件：`~/.workbuddy/mcp-servers/{server-name}/src/index.ts`

使用 @templates/typescript-server.ts 模板，替换相同的占位符。

同时生成：
- `package.json`
- `tsconfig.json`

### Step 5: 生成 mcp.json 配置

读取现有 `~/.workbuddy/mcp.json`，**保留已有配置**，追加新条目。

Python 配置模板：
```json
{
  "{{SERVER_NAME}}": {
    "command": "/Users/wangyichen/.workbuddy/binaries/python/envs/default/bin/python3",
    "args": ["~/.workbuddy/mcp-servers/{{SERVER_NAME}}/main.py"],
    "env": {}
  }
}
```

TypeScript 配置模板：
```json
{
  "{{SERVER_NAME}}": {
    "command": "/Users/wangyichen/.workbuddy/binaries/node/versions/20.18.0/bin/node",
    "args": ["~/.workbuddy/mcp-servers/{{SERVER_NAME}}/dist/index.js"],
    "env": {}
  }
}
```

⚠️ 路径中的 `~` 需要展开为 `/Users/wangyichen`。

### Step 6: 安装依赖

**Python**:
```bash
/Users/wangyichen/.workbuddy/binaries/python/envs/default/bin/pip install mcp playwright
/Users/wangyichen/.workbuddy/binaries/python/envs/default/bin/playwright install chromium
```

**TypeScript**:
```bash
cd ~/.workbuddy/mcp-servers/{{SERVER_NAME}}
npm install @modelcontextprotocol/sdk playwright zod
npx tsc
npx playwright install chromium
```

### Step 7: 验证

1. 尝试启动 MCP Server（仅验证能否正常启动，不需要完整功能测试）
2. Python: `echo '{"jsonrpc":"2.0","method":"initialize","params":...}' | /path/to/python3 main.py`
3. 检查 stderr 输出是否有错误
4. 告知用户：需在 WorkBuddy 连接器管理页面点击「信任」新 MCP 服务

### Step 8: 输出结果

向用户展示：
1. 生成的 MCP Server 代码路径
2. mcp.json 配置内容
3. 可用的工具函数列表及说明
4. 后续操作：去连接器管理页面点击「信任」

## Pitfalls

- **mcp.json 必须保留已有配置**：读取 → 追加 → 写回，绝不能覆盖其他 MCP 服务
- **路径必须展开 `~`**：mcp.json 中 `command` 和 `args` 不支持 `~`，必须用绝对路径
- **Playwright 首次安装需下载浏览器**：`playwright install chromium` 可能耗时较长，用 run_in_background 执行
- **网站可能需要登录**：如果检测到登录页面，生成的工具必须包含 login 方法，但不要硬编码用户密码
- **动态加载页面**：部分 SPA 页面需要 `wait_for_load_state("networkidle")` 后才能抓取元素
- **反爬机制**：部分网站会检测 Playwright，需要在 launch 时添加 `--disable-blink-features=AutomationControlled` 等参数
- **headless vs headed**：默认 headless，如需调试可在 env 中设置 `HEADED=1`
- **Python venv 路径固定**：始终使用 `/Users/wangyichen/.workbuddy/binaries/python/envs/default/bin/python3` 和对应的 pip
- **Node 路径固定**：始终使用 `/Users/wangyichen/.workbuddy/binaries/node/versions/20.18.0/bin/node`
- **npm install 必须在隔离目录**：在 `~/.workbuddy/mcp-servers/{server-name}/` 下执行，不要污染全局环境

## Verification

验证清单：
- [ ] MCP Server 代码文件已生成且语法正确
- [ ] mcp.json 已更新且保留了原有配置
- [ ] 依赖已安装（mcp + playwright + chromium）
- [ ] Server 可以启动（stdio 模式无报错）
- [ ] 生成的工具函数 docstring 清晰，AI 可正确识别
- [ ] 已告知用户需在连接器管理页面「信任」新服务

## References

- @references/python-fastmcp-api.md — Python FastMCP API 参考
- @references/typescript-mcp-sdk-api.md — TypeScript MCP SDK API 参考
- @references/playwright-selectors.md — Playwright 选择器最佳实践
