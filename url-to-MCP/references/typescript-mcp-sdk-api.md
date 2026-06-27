# TypeScript MCP SDK API 参考

## 安装

```bash
npm install @modelcontextprotocol/sdk playwright zod
npx playwright install chromium
```

## 核心用法

### 初始化

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "server-name",
  version: "1.0.0",
  description: "Server description",
});
```

### 注册工具

```typescript
server.tool(
  "tool-name",           // 工具名称
  "工具描述 — AI 根据此描述决定何时调用",  // 描述
  {                       // Zod schema 定义参数
    param1: z.string().describe("参数1描述"),
    param2: z.number().optional().default(10).describe("参数2描述"),
  },
  async ({ param1, param2 }) => {  // 处理函数
    return {
      content: [{ type: "text", text: `Result: ${param1} ${param2}` }],
    };
  }
);
```

**关键规则**：
- 第二个参数（描述）是 AI 识别工具用途的依据
- 参数用 Zod schema 定义，必须加 `.describe()`
- 返回格式固定：`{ content: [{ type: "text", text: "..." }] }`
- 错误返回：加 `isError: true`

### 注册资源

```typescript
server.resource(
  "config",
  "config://app",
  async (uri) => ({
    contents: [{ uri: uri.href, text: "config data here" }],
  })
);
```

### 注册提示词

```typescript
server.prompt(
  "analyze",
  { data: z.string().describe("Data to analyze") },
  async ({ data }) => ({
    messages: [{ role: "user", content: { type: "text", text: `Analyze: ${data}` } }],
  })
);
```

### 启动服务器

```typescript
const transport = new StdioServerTransport();
await server.connect(transport);
```

## Playwright 常用操作

### 启动浏览器

```typescript
import { chromium, type Browser, type Page } from "playwright";

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({
  viewport: { width: 1280, height: 720 },
});
const page = await context.newPage();
```

### 页面导航

```typescript
await page.goto("https://example.com", {
  waitUntil: "networkidle",
  timeout: 30000,
});
```

### 元素操作

```typescript
const element = await page.waitForSelector("#submit-btn", { timeout: 10000 });
await element.click();
await element.fill("text");
await element.selectOption("value");
await element.check();
await element.hover();
```

### 获取内容

```typescript
const text = await page.innerText("body");
const href = await element.getAttribute("href");

// 表格数据
const rows = await page.$$eval("table tr", (trs) =>
  trs.map((tr) => {
    const cells = tr.querySelectorAll("td");
    return Array.from(cells).map((c) => c.textContent?.trim() || "");
  })
);
```

### 截图

```typescript
await page.screenshot({ path: "/tmp/screenshot.png", fullPage: false });
```

### 等待

```typescript
await page.waitForTimeout(2000);
await page.waitForLoadState("networkidle");
await page.waitForSelector(".result", { state: "visible" });
```

## 项目配置

### package.json

```json
{
  "name": "mcp-server-name",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.0",
    "playwright": "^1.49.0",
    "zod": "^3.24.0"
  },
  "devDependencies": {
    "typescript": "^5.7.0",
    "@types/node": "^22.0.0"
  }
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```
