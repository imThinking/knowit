"""HTML content cleaning service

Based on clip-to-kami implementation.
Cleans raw HTML into Kami-compatible content.
"""

import re
import html as html_module
from bs4 import BeautifulSoup, NavigableString


def clean_html(content_html: str, source_type: str = "wechat") -> str:
    """
    Clean raw HTML into Kami-compatible body content.

    PITFALL: Do NOT skip <section> elements just because they have no text.
    WeChat articles wrap images in <section> tags — skipping them removes
    all images from the output. Always recurse into children.

    PITFALL: WeChat images use data-src (original URL) and src (lazy-load placeholder).
    Prefer data-src. Skip SVG placeholder images entirely.
    """
    soup = BeautifulSoup(content_html, "html.parser")

    # Remove noise elements before processing
    for sel in ["script", "style", ".qr_code_pc", ".reward_area", ".rich_media_meta",
                ".rich_media_title", ".profile_container"]:
        for tag in soup.select(sel):
            tag.decompose()

    # Remove style and unnecessary data-* attributes, KEEP data-src for images
    for tag in soup.find_all(True):
        attrs_to_remove = [
            k for k in tag.attrs
            if k == "style"
            or (k.startswith("data-") and k != "data-src")
            or k in ["leaf", "nodeleaf", "type", "_width",
                     "data-report-img-idx", "data-fail",
                     "data-original-style", "data-index",
                     "data-aistatus", "data-imgfileid",
                     "data-ratio", "data-s", "data-w",
                     "class", "id"]  # Remove most classes and ids for cleaner output
        ]
        for attr in attrs_to_remove:
            del tag[attr]

    def process_element(elem):
        if isinstance(elem, NavigableString):
            text = str(elem)
            return html_module.escape(text) if text.strip() else ""

        # WeChat code block: extract code text, filter CSS counter noise
        if "code-snippet__fix" in (elem.get("class") or []):
            pre = elem.select_one("pre[data-lang]")
            lang = pre.get("data-lang", "") if pre else ""
            lines = []
            for code_tag in elem.find_all("code"):
                text = code_tag.get_text()
                if re.match(r"^[ce]?ounter\(line", text):
                    continue
                lines.append(text)
            code_text = "\n".join(lines) if lines else elem.get_text()
            escaped = html_module.escape(code_text)
            return f'<pre><code class="language-{html_module.escape(lang)}">{escaped}</code></pre>\n'

        if elem.name == "p":
            children = "".join(process_element(c) for c in elem.children).strip()
            return f"<p>{children}</p>\n" if children else ""

        # PITFALL: Never skip sections based on text content — they may contain only images
        elif elem.name == "section":
            return "".join(process_element(c) for c in elem.children)

        elif elem.name == "span":
            return "".join(process_element(c) for c in elem.children)

        elif elem.name == "strong":
            return f'<strong>{"".join(process_element(c) for c in elem.children)}</strong>'

        elif elem.name == "em":
            return f'<em>{"".join(process_element(c) for c in elem.children)}</em>'

        elif elem.name == "br":
            return "<br>"

        elif elem.name == "img":
            # PITFALL: Prefer data-src (original WeChat image) over src (lazy-loaded)
            src = elem.get("data-src", "") or elem.get("src", "")
            alt = elem.get("alt", "")
            # PITFALL: Skip SVG placeholder images used for lazy loading
            if src and not src.startswith("data:image/svg+xml"):
                return f'<figure><img src="{src}" alt="{html_module.escape(alt)}"><figcaption>{html_module.escape(alt)}</figcaption></figure>\n'
            return ""

        elif elem.name in ["ul", "ol"]:
            items = []
            for li in elem.find_all("li", recursive=False):
                item_text = "".join(process_element(c) for c in li.children).strip()
                if item_text:
                    items.append(f"<li>{item_text}</li>")
            if items:
                tag = "ol" if elem.name == "ol" else "ul"
                return f"<{tag}>\n" + "\n".join(items) + f"\n</{tag}>\n"
            return ""

        elif elem.name == "li":
            return "".join(process_element(c) for c in elem.children)

        elif elem.name == "a":
            href = elem.get("href", "")
            text = "".join(process_element(c) for c in elem.children)
            if href and text.strip():
                return f'<a href="{href}">{text}</a>'
            return text

        elif elem.name == "blockquote":
            text = "".join(process_element(c) for c in elem.children).strip()
            return f"<blockquote>\n{text}\n</blockquote>\n" if text else ""

        elif elem.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            text = "".join(process_element(c) for c in elem.children).strip()
            return f"<{elem.name}>{text}</{elem.name}>\n" if text else ""

        elif elem.name == "pre":
            text = elem.get_text()
            return f'<pre><code>{html_module.escape(text)}</code></pre>\n' if text.strip() else ""

        elif elem.name == "code":
            text = elem.get_text()
            return f'<code>{html_module.escape(text)}</code>'

        elif elem.name == "table":
            return str(elem)

        elif elem.name in ["figure", "figcaption"]:
            return "".join(process_element(c) for c in elem.children)

        else:
            return "".join(process_element(c) for c in elem.children)

    body_content = process_element(soup)
    body_content = re.sub(r"\n{3,}", "\n\n", body_content)
    return body_content
