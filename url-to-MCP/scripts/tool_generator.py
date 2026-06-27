#!/usr/bin/env python3
"""
Tool function generator for url-to-mcp skill.
Given a site analysis JSON, generates Python or TypeScript tool functions.
"""

import json
import sys
import re


def sanitize_name(name: str) -> str:
    """Convert a string to a valid Python/TypeScript identifier."""
    name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    if name and name[0].isdigit():
        name = f"field_{name}"
    return name.lower()


def server_name_from_url(url: str) -> str:
    """Generate a server name from URL."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path
    domain = re.sub(r'^www\.', '', domain)
    name = re.sub(r'[^a-zA-Z0-9]', '_', domain)
    name = re.sub(r'_+', '_', name).strip('_')
    return name.lower()


def generate_python_tools(analysis: dict) -> str:
    """Generate Python FastMCP tool functions from site analysis."""
    tools = []
    site_url = analysis.get("url", "")
    server_name = server_name_from_url(site_url)

    # Login tool if needed
    if analysis.get("requires_login"):
        tools.append(f'''
@mcp.tool()
async def login(username: str, password: str) -> str:
    """Log in to {site_url}. Required before performing other operations.

    Args:
        username: Login username or email.
        password: Login password.

    Returns:
        Login result message.
    """
    pw, browser, page = None, None, None
    try:
        pw, browser, page = await _create_browser()
        await page.goto(SITE_URL, wait_until="networkidle", timeout=30000)
        # Auto-detect login form - try common selectors
        username_selectors = ['input[name="username"]', 'input[name="email"]', 'input[type="email"]', 'input[id="username"]']
        password_selectors = ['input[name="password"]', 'input[type="password"]', 'input[id="password"]']
        submit_selectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Login")', 'button:has-text("登录")', 'button:has-text("Sign in")']

        for sel in username_selectors:
            el = await page.query_selector(sel)
            if el:
                await el.fill(username)
                break

        for sel in password_selectors:
            el = await page.query_selector(sel)
            if el:
                await el.fill(password)
                break

        for sel in submit_selectors:
            el = await page.query_selector(sel)
            if el:
                await el.click()
                break

        await page.wait_for_load_state("networkidle")
        await _cleanup(pw, browser)
        return "Login completed. Page title: " + await page.title()
    except Exception as e:
        if browser:
            await _cleanup(pw, browser)
        return f"Login error: {{str(e)}}"
''')

    # Form tools
    for form in analysis.get("forms", []):
        form_id = sanitize_name(form.get("id", form.get("name", "form")))
        fields_desc = ", ".join([f'"{f.get("name", "")}"' for f in form.get("fields", [])])

        # Build parameters
        params = []
        field_assignments = []
        for field in form.get("fields", []):
            fname = sanitize_name(field.get("name", field.get("id", "field")))
            ftype = "str" if field.get("type", "text") != "number" else "float"
            fdesc = field.get("placeholder", field.get("name", fname))
            params.append(f'{fname}: {ftype} = ""')
            selector = field.get("id") and f"#{{field.get('id')}}" or f'input[name="{{field.get("name", fname)}}"]'
            field_assignments.append(f'        el = await page.query_selector(\'{selector}\')\n        if el: await el.fill(str({fname}))')

        params_str = ", ".join(params)
        fields_list = ", ".join([sanitize_name(f.get("name", f.get("id", "field"))) for f in form.get("fields", [])])

        tools.append(f'''
@mcp.tool()
async def fill_{form_id}({params_str}) -> str:
    """Fill and submit the {form_id} form on {site_url}. Fields: {fields_desc}

    Args:
        {chr(10).join([f"{sanitize_name(f.get('name', f.get('id', 'field')))}: {f.get('placeholder', f.get('name', ''))}" for f in form.get("fields", [])])}

    Returns:
        Form submission result.
    """
    pw, browser, page = None, None, None
    try:
        pw, browser, page = await _create_browser()
        await page.goto(SITE_URL, wait_until="networkidle", timeout=30000)
{chr(10).join(field_assignments)}
        submit = await page.query_selector('button[type="submit"], input[type="submit"]')
        if submit:
            await submit.click()
        await page.wait_for_load_state("networkidle")
        title = await page.title()
        await _cleanup(pw, browser)
        return f"Form submitted. Page: {{title}}"
    except Exception as e:
        if browser:
            await _cleanup(pw, browser)
        return f"Form error: {{str(e)}}"
''')

    # Data extraction tools
    for table in analysis.get("data_tables", []):
        table_name = sanitize_name(table.get("selector", "data"))
        columns = table.get("columns", [])

        tools.append(f'''
@mcp.tool()
async def extract_{table_name}(max_rows: int = 50) -> str:
    """Extract data from the {table_name} table on {site_url}. Columns: {", ".join(columns)}

    Args:
        max_rows: Maximum number of rows to extract. Defaults to 50.

    Returns:
        JSON string of extracted table data.
    """
    pw, browser, page = None, None, None
    try:
        pw, browser, page = await _create_browser()
        await page.goto(SITE_URL, wait_until="networkidle", timeout=30000)
        rows = await page.query_selector_all("{table.get('selector', 'table')} tbody tr")
        data = []
        for row in rows[:max_rows]:
            cells = await row.query_selector_all("td")
            row_data = [await cell.inner_text() for cell in cells]
            data.append(row_data)
        await _cleanup(pw, browser)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        if browser:
            await _cleanup(pw, browser)
        return f"Extraction error: {{str(e)}}"
''')

    # Navigation tools
    for action in analysis.get("actions", []):
        if action.get("type") == "link" and action.get("text"):
            link_name = sanitize_name(action.get("text", "page"))
            href = action.get("href", "")
            if href and not href.startswith("http"):
                href = f"{{SITE_URL.rstrip('/')}}{{href}}" if href.startswith("/") else href

            tools.append(f'''
@mcp.tool()
async def navigate_to_{link_name}() -> str:
    """Navigate to the '{action.get("text")}' page on {site_url}.

    Returns:
        Page title and content summary.
    """
    pw, browser, page = None, None, None
    try:
        pw, browser, page = await _create_browser()
        await page.goto("{href or SITE_URL}", wait_until="networkidle", timeout=30000)
        title = await page.title()
        content = await page.inner_text("body")
        summary = content[:500] + "..." if len(content) > 500 else content
        await _cleanup(pw, browser)
        return f"Title: {{title}}\\n\\n{{summary}}"
    except Exception as e:
        if browser:
            await _cleanup(pw, browser)
        return f"Navigation error: {{str(e)}}"
''')

    return "\n".join(tools)


def generate_typescript_tools(analysis: dict) -> str:
    """Generate TypeScript MCP tool registrations from site analysis."""
    tools = []
    site_url = analysis.get("url", "")

    # Login tool if needed
    if analysis.get("requires_login"):
        tools.append('''
server.tool(
  "login",
  "Log in to ''' + site_url + '''. Required before other operations.",
  {
    username: z.string().describe("Login username or email"),
    password: z.string().describe("Login password"),
  },
  async ({ username, password }) => {
    let browser: Browser | null = null;
    try {
      const { browser: b, page } = await createBrowser();
      browser = b;
      await page.goto(SITE_URL, { waitUntil: "networkidle", timeout: 30000 });

      const usernameSelectors = ['input[name="username"]', 'input[name="email"]', 'input[type="email"]'];
      const passwordSelectors = ['input[name="password"]', 'input[type="password"]'];
      const submitSelectors = ['button[type="submit"]', 'input[type="submit"]', 'button:has-text("Login")'];

      for (const sel of usernameSelectors) {
        const el = await page.$(sel);
        if (el) { await el.fill(username); break; }
      }
      for (const sel of passwordSelectors) {
        const el = await page.$(sel);
        if (el) { await el.fill(password); break; }
      }
      for (const sel of submitSelectors) {
        const el = await page.$(sel);
        if (el) { await el.click(); break; }
      }

      await page.waitForLoadState("networkidle");
      const title = await page.title();
      await browser.close();
      return { content: [{ type: "text", text: `Login completed. Page: ${title}` }] };
    } catch (error: any) {
      if (browser) await browser.close();
      return { content: [{ type: "text", text: `Login error: ${error.message}` }], isError: true };
    }
  }
);
''')

    # Data extraction tools
    for table in analysis.get("data_tables", []):
        table_name = sanitize_name(table.get("selector", "data"))
        columns = table.get("columns", [])
        tools.append('''
server.tool(
  "extract_''' + table_name + '''",
  "Extract data from the ''' + table_name + ''' table. Columns: ''' + ", ".join(columns) + '''",
  {
    max_rows: z.number().optional().default(50).describe("Maximum rows to extract"),
  },
  async ({ max_rows }) => {
    let browser: Browser | null = null;
    try {
      const { browser: b, page } = await createBrowser();
      browser = b;
      await page.goto(SITE_URL, { waitUntil: "networkidle", timeout: 30000 });
      const rows = await page.$$eval("''' + table.get("selector", "table") + ''' tbody tr", (trs, limit) =>
        trs.slice(0, limit).map((tr) =>
          Array.from(tr.querySelectorAll("td")).map((td) => td.textContent?.trim() || "")
        ),
        max_rows || 50
      );
      await browser.close();
      return { content: [{ type: "text", text: JSON.stringify(rows) }] };
    } catch (error: any) {
      if (browser) await browser.close();
      return { content: [{ type: "text", text: `Error: ${error.message}` }], isError: true };
    }
  }
);
''')

    return "\n".join(tools)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python tool_generator.py <analysis.json> <python|typescript>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        analysis = json.load(f)

    lang = sys.argv[2].lower()
    if lang == "python":
        print(generate_python_tools(analysis))
    elif lang in ["typescript", "ts"]:
        print(generate_typescript_tools(analysis))
    else:
        print(f"Unsupported language: {lang}", file=sys.stderr)
        sys.exit(1)
