# Python FastMCP API 参考

## 安装

```bash
pip install mcp playwright
playwright install chromium
```

## FastMCP 核心用法

### 初始化

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("server-name")
```

### 注册工具（@mcp.tool()）

```python
@mcp.tool()
def my_tool(param1: str, param2: int = 10) -> str:
    """工具描述 — AI 根据这段 docstring 决定何时调用此工具。

    Args:
        param1: 参数1的描述
        param2: 参数2的描述，默认10

    Returns:
        返回结果的描述
    """
    return f"Result: {param1} {param2}"
```

**关键规则**：
- docstring 是 AI 识别工具用途的唯一依据，必须清晰
- 参数必须有类型标注
- 可选参数用默认值
- 返回 str 类型

### 异步工具

```python
@mcp.tool()
async def async_tool(url: str) -> str:
    """异步工具示例"""
    # 适合 Playwright 等异步操作
    result = await some_async_operation(url)
    return result
```

### 注册资源（@mcp.resource()）

```python
@mcp.resource("config://app")
def get_config() -> str:
    """获取应用配置"""
    return "config data here"

@mcp.resource("user://{user_id}/profile")
def get_user_profile(user_id: str) -> str:
    """获取用户资料"""
    return f"Profile for {user_id}"
```

### 注册提示词（@mcp.prompt()）

```python
@mcp.prompt()
def analyze_prompt(data: str) -> str:
    """分析数据的提示词模板"""
    return f"Please analyze the following data:\n{data}"
```

### 启动服务器

```python
if __name__ == "__main__":
    mcp.run(transport="stdio")  # 标准输入输出模式
```

## Playwright 常用操作

### 启动浏览器

```python
from playwright.async_api import async_playwright

async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1280, "height": 720})
    page = await context.new_page()
```

### 页面导航

```python
await page.goto("https://example.com", wait_until="networkidle", timeout=30000)
```

wait_until 选项：
- `"load"` — load 事件触发
- `"domcontentloaded"` — DOM 解析完成
- `"networkidle"` — 网络空闲（推荐用于 SPA）
- `"commit"` — 收到响应头

### 元素操作

```python
# 等待元素出现
element = await page.wait_for_selector("#submit-btn", timeout=10000)

# 点击
await element.click()

# 填写输入框
await element.fill("text content")

# 下拉选择
await element.select_option("value")

# 勾选复选框
await element.check()

# 悬停
await element.hover()
```

### 获取内容

```python
# 获取页面全部可见文字
text = await page.inner_text("body")

# 获取元素文字
text = await element.inner_text()

# 获取元素属性
href = await element.get_attribute("href")

# 获取表格数据
rows = await page.query_selector_all("table tr")
for row in rows:
    cells = await row.query_selector_all("td")
    data = [await cell.inner_text() for cell in cells]
```

### 截图

```python
await page.screenshot(path="/tmp/screenshot.png", full_page=False)
```

### 等待

```python
# 等待固定时间
await page.wait_for_timeout(2000)

# 等待导航完成
await page.wait_for_load_state("networkidle")

# 等待特定元素
await page.wait_for_selector(".result", state="visible")
```

### 反检测

```python
browser = await pw.chromium.launch(
    headless=True,
    args=[
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
    ],
)
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) ...",
)
```
