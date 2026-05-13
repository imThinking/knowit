"""Dynamic web scraping service using Playwright for JavaScript-heavy sites

Based on clip-to-kami implementation for WeChat article scraping.
"""

from typing import Optional
import re


def scrape_wechat_article(url: str, timeout: int = 30000):
    """
    Scrape WeChat article using Playwright.

    This follows the clip-to-kami approach:
    1. Use Playwright with networkidle wait for WeChat
    2. Extract content using JavaScript evaluation
    3. Handle WeChat-specific selectors and retry logic

    Args:
        url: WeChat article URL (mp.weixin.qq.com)
        timeout: Timeout in milliseconds

    Returns:
        dict with keys: title, author, date, html, source
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        raise ImportError("Playwright is required for WeChat articles. Run: pip install playwright && playwright install chromium")

    timeout_ms = timeout

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
            locale="zh-CN",
        )

        page = context.new_page()

        try:
            # WeChat requires networkidle for lazy-loading images
            page.goto(url, wait_until="networkidle", timeout=timeout_ms)

            # Retry once on timeout - WeChat can be slow
            for attempt in range(2):
                try:
                    page.wait_for_selector("#js_content", timeout=15000 if attempt == 0 else 25000)
                    break
                except Exception:
                    if attempt == 0:
                        print("WeChat content not loaded, retrying...")
                        page.reload(wait_until="networkidle")
                    else:
                        raise

            # Extract content using JavaScript (like clip-to-kami)
            content_html = page.evaluate('() => document.querySelector("#js_content")?.innerHTML || ""')
            title = page.evaluate('''() =>
                (document.querySelector("#activity-name") || document.querySelector("#activity_name"))?.textContent?.trim() || ""
            ''')
            author = page.evaluate('() => document.querySelector("#js_name")?.textContent?.trim() || ""')
            date = page.evaluate('() => document.querySelector("#publish_time")?.textContent?.trim() || ""')

            # Try to extract date from script tags if not found
            if not date:
                full_html = page.content()
                date = _extract_wechat_publish_time(full_html)

        finally:
            context.close()
            browser.close()

        return {
            "title": title,
            "author": author,
            "date": date,
            "html": content_html,
            "source": url,
        }


def _extract_wechat_publish_time(html: str) -> str:
    """Extract publish time from WeChat script tags (create_time JS variable)."""
    m = re.search(r"create_time\s*:\s*JsDecode\('([^']+)'\)", html)
    if not m:
        m = re.search(r"create_time\s*:\s*'(\d+)'", html)
    if m:
        try:
            from datetime import timezone, timedelta
            ts = int(m.group(1))
            if ts > 0:
                tz = timezone(timedelta(hours=8))
                from datetime import datetime
                return datetime.fromtimestamp(ts, tz).strftime("%Y-%m-%d")
        except ValueError:
            return m.group(1)
    return ""
