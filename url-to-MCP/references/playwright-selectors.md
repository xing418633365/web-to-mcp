# Playwright 选择器最佳实践

## 选择器优先级（从高到低）

1. **data-testid** — 最稳定，推荐
   ```python
   await page.click('[data-testid="submit-btn"]')
   ```

2. **id 选择器** — 简洁但可能动态生成
   ```python
   await page.click('#submit-btn')
   ```

3. **aria-label / role** — 语义化，可访问性好
   ```python
   await page.click('[aria-label="提交"]')
   await page.get_by_role("button", name="提交")
   ```

4. **text 选择器** — 适合按钮和链接
   ```python
   await page.get_by_text("提交").click()
   await page.click('text=提交')
   ```

5. **CSS 选择器** — 通用但脆弱
   ```python
   await page.click('button.btn-primary')
   await page.click('form input[name="username"]')
   ```

6. **XPath** — 最后手段
   ```python
   await page.click('//button[contains(text(), "提交")]')
   ```

## 常见场景的选择器策略

### 表单

```python
# 输入框 — 优先用 name 属性
await page.fill('input[name="username"]', "value")

# 下拉框
await page.select_option('select[name="category"]', "value")

# 复选框
await page.check('input[type="checkbox"][name="agree"]')

# 单选框
await page.check('input[type="radio"][value="option1"]')

# 提交按钮
await page.click('button[type="submit"]')
# 或
await page.click('text=提交')
```

### 数据表格

```python
# 获取表头
headers = await page.query_selector_all("table thead th")
header_texts = [await h.inner_text() for h in headers]

# 获取数据行
rows = await page.query_selector_all("table tbody tr")
for row in rows:
    cells = await row.query_selector_all("td")
    row_data = [await cell.inner_text() for cell in cells]
```

### 分页

```python
# 下一页按钮
next_btn = await page.query_selector('a.next, button.next, [aria-label="Next"]')
if next_btn:
    await next_btn.click()
    await page.wait_for_load_state("networkidle")
```

### 弹窗/对话框

```python
# 等待弹窗出现
await page.wait_for_selector(".modal, .dialog", state="visible")

# 点击确认
await page.click('.modal button.confirm, .dialog button:has-text("确认")')
```

## 反爬策略

### 避免被检测为自动化

```python
# 1. 自定义 User-Agent
context = await browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
)

# 2. 添加启动参数
browser = await pw.chromium.launch(
    args=["--disable-blink-features=AutomationControlControlled"]
)

# 3. 模拟人类行为（随机延迟）
import random
await page.wait_for_timeout(random.randint(1000, 3000))

# 4. 隐藏 webdriver 标志
await page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
""")
```

### 处理验证码

- 简单图片验证码 → 可尝试 OCR（pytesseract）
- 滑块验证码 → 需模拟拖动轨迹
- reCAPTCHA/hCaptcha → 建议人工介入或第三方服务
- 如果验证码频繁出现，建议在工具中提示用户手动处理

## 超时策略

```python
# 导航超时
await page.goto(url, timeout=30000)

# 等待元素超时
element = await page.wait_for_selector(selector, timeout=10000)

# 全局默认超时
browser = await pw.chromium.launch()
context = await browser.new_context()
context.set_default_timeout(15000)      # 15秒
context.set_default_navigation_timeout(30000)  # 30秒
```
