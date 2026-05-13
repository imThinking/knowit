"""HTML/PDF export service using Kami design system

Based on Kami by @tw93: https://github.com/tw93/Kami
Uses the same fonts, colors, and layout system.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime
import shutil
import tempfile


class KamiExporter:
    """HTML/PDF exporter using Kami design system"""

    def __init__(self):
        """Initialize Kami exporter"""
        self.template_path = Path(__file__).parent / "kami_template.html"

    def generate_html(
        self,
        title: str,
        content: str,
        author: Optional[str] = None,
        url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        output_path: Optional[str] = None,
        clean: bool = False,
    ) -> str:
        """
        Generate HTML file using Kami template

        Args:
            title: Document title
            content: HTML content (body content only, not full HTML)
            author: Optional author name
            url: Optional source URL
            created_at: Optional creation date
            output_path: Output file path
            clean: Whether to clean HTML content

        Returns:
            Path to generated HTML file
        """
        # Clean content if requested
        if clean:
            from .html_cleaner import clean_html
            content = clean_html(content, source_type="wechat" if "mp.weixin.qq.com" in (url or "") else "webpage")

        # Read template
        template = self.template_path.read_text(encoding="utf-8")

        # Prepare replacements
        date_str = created_at.strftime("%Y-%m-%d %H:%M") if created_at else datetime.now().strftime("%Y-%m-%d %H:%M")
        author_str = author or "Unknown"

        # Fill template
        html = template.replace("{{title}}", title)
        html = html.replace("{{content}}", content)
        html = html.replace("{{author}}", author_str)
        html = html.replace("{{url}}", url or "")
        html = html.replace("{{date}}", date_str)

        # Write to file
        if output_path is None:
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            output_path = f"{safe_title[:50]}.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def generate_html_simple(
        self,
        title: str,
        content: str,
        author: Optional[str] = None,
        url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        output_path: Optional[str] = None,
        clean: bool = False,
    ) -> str:
        """
        Generate HTML file without cover page (simpler format)

        Args:
            title: Document title
            content: HTML content
            author: Optional author name
            url: Optional source URL
            created_at: Optional creation date
            output_path: Output file path
            clean: Whether to clean HTML content

        Returns:
            Path to generated HTML file
        """
        # Clean content if requested
        if clean:
            from .html_cleaner import clean_html
            content = clean_html(content, source_type="wechat" if "mp.weixin.qq.com" in (url or "") else "webpage")

        date_str = created_at.strftime("%Y-%m-%d") if created_at else datetime.now().strftime("%Y-%m-%d")

        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{self._get_kami_css()}
</style>
</head>
<body>
<div class="simple-document">
  <header>
    <h1>{title}</h1>
    <div class="metadata">
      {f'<p class="meta"><strong>Author</strong> {author}</p>' if author else ''}
      {f'<p class="meta"><strong>Source</strong> <a href="{url}">{url}</a></p>' if url else ''}
      <p class="meta"><strong>Saved</strong> {date_str}</p>
    </div>
  </header>
  <main class="content">
    {content}
  </main>
</div>
</body>
</html>"""

        if output_path is None:
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            output_path = f"{safe_title[:50]}.html"

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

        return output_path

    def generate_pdf(
        self,
        title: str,
        content: str,
        author: Optional[str] = None,
        url: Optional[str] = None,
        created_at: Optional[datetime] = None,
        output_path: Optional[str] = None,
        clean: bool = False,
        font_dir: Optional[str] = None,
    ) -> str:
        """
        Generate PDF file using WeasyPrint

        Args:
            title: Document title
            content: HTML content
            author: Optional author name
            url: Optional source URL
            created_at: Optional creation date
            output_path: Output PDF path
            clean: Whether to clean HTML content
            font_dir: Optional font directory path

        Returns:
            Path to generated PDF file
        """
        try:
            from weasyprint import HTML
        except ImportError:
            raise ImportError(
                "WeasyPrint is required for PDF generation. "
                "Run: pip install weasyprint"
            )
        except OSError as e:
            if "libgobject" in str(e).lower():
                raise OSError(
                    "WeasyPrint cannot find system libraries. "
                    "On Windows, this should work automatically. "
                    "On macOS with Homebrew, run: brew install pango gdk-pixbuf cairo"
                )
            raise

        # Clean content if requested
        if clean:
            from .html_cleaner import clean_html
            content = clean_html(content, source_type="wechat" if "mp.weixin.qq.com" in (url or "") else "webpage")

        # Generate HTML
        date_str = created_at.strftime("%Y-%m-%d") if created_at else datetime.now().strftime("%Y-%m-%d")
        author_str = author or "Unknown"

        # Read template
        template = self.template_path.read_text(encoding="utf-8")

        # Fill template
        html = template.replace("{{title}}", title)
        html = html.replace("{{content}}", content)
        html = html.replace("{{author}}", author_str)
        html = html.replace("{{url}}", url or "")
        html = html.replace("{{date}}", date_str)

        # Determine output path
        if output_path is None:
            safe_title = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in title)
            output_path = f"{safe_title[:50]}.pdf"

        # Create temp directory with fonts
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "document.html"
            html_path.write_text(html, encoding="utf-8")

            # Copy fonts for local rendering if font_dir provided
            if font_dir and Path(font_dir).exists():
                fonts_tmp = Path(tmpdir) / "fonts"
                fonts_tmp.mkdir()
                for font_file in Path(font_dir).glob("*.ttf"):
                    shutil.copy(font_file, fonts_tmp)

            # Generate PDF
            HTML(str(html_path)).write_pdf(output_path)

        return output_path

    def _get_kami_css(self) -> str:
        """Get Kami CSS styles for simple document"""
        return """
        @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&display=swap');

        @page {
            size: A4;
            margin: 20mm 22mm 22mm 22mm;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        :root {
            --parchment: #f5f4ed;
            --ivory: #faf9f5;
            --near-black: #141413;
            --dark-warm: #3d3d3a;
            --olive: #504e49;
            --stone: #6b6a64;
            --brand: #1B365D;
            --border: #e8e6dc;
            --border-soft: #e5e3d8;
            --serif: "TsangerJinKai02", "Source Han Serif SC", "Noto Serif CJK SC",
                      "Songti SC", "STSong", "FangSong", "FangSong_GB18030", Georgia, serif;
        }

        html, body {
            background: var(--parchment);
            color: var(--near-black);
        }

        @media screen {
            body {
                max-width: 210mm;
                margin: 0 auto;
                padding: 20mm 22mm;
                background: var(--parchment);
            }
        }

        body {
            font-family: var(--serif);
            font-size: 10.5pt;
            line-height: 1.55;
            letter-spacing: 0.3pt;
        }

        .simple-document {
            padding: 0;
        }

        header {
            margin-bottom: 2em;
            padding-bottom: 1em;
            border-bottom: 2pt solid var(--brand);
        }

        h1 {
            font-size: 22pt;
            font-weight: 500;
            line-height: 1.2;
            margin: 0 0 10pt 0;
            border-left: 2.5pt solid var(--brand);
            border-radius: 1.5pt;
            padding-left: 8pt;
            color: var(--near-black);
        }

        .metadata {
            font-size: 9pt;
            color: var(--stone);
            margin-top: 1em;
        }

        .meta {
            margin: 0.3em 0;
        }

        .meta strong {
            color: var(--dark-warm);
            font-weight: 500;
        }

        .meta a {
            color: var(--brand);
            text-decoration: none;
        }

        .meta a:hover {
            text-decoration: underline;
        }

        .content h2 {
            font-size: 16pt;
            font-weight: 500;
            line-height: 1.25;
            margin: 24pt 0 6pt 0;
            color: var(--near-black);
        }

        .content h3 {
            font-size: 13pt;
            font-weight: 500;
            line-height: 1.3;
            margin: 18pt 0 4pt 0;
            color: var(--dark-warm);
        }

        .content p {
            margin: 0 0 10pt 0;
            line-height: 1.55;
            color: var(--near-black);
        }

        .content strong {
            font-weight: 500;
        }

        .content a {
            color: var(--brand);
            text-decoration: none;
        }

        .content a:hover {
            text-decoration: underline;
        }

        .content code {
            font-family: "JetBrains Mono", "SF Mono", Consolas, "Courier New",
                         "TsangerJinKai02", "Source Han Serif SC", "Songti SC", monospace;
            font-size: 9pt;
            background: var(--ivory);
            padding: 1pt 4pt;
            border-radius: 2pt;
            color: var(--dark-warm);
        }

        .content pre {
            font-family: "JetBrains Mono", "SF Mono", Consolas, "Courier New",
                         "TsangerJinKai02", "Source Han Serif SC", "Songti SC", monospace;
            font-size: 9pt;
            line-height: 1.5;
            background: var(--ivory);
            border: 0.5pt solid var(--border-soft);
            padding: 10pt 14pt;
            margin: 10pt 0;
            white-space: pre-wrap;
            word-break: break-word;
            color: var(--near-black);
        }

        .content pre code {
            background: transparent;
            padding: 0;
        }

        .content blockquote {
            border-left: 2pt solid var(--brand);
            margin: 12pt 0;
            padding: 4pt 0 4pt 16pt;
            color: var(--olive);
            line-height: 1.55;
        }

        .content ul, .content ol {
            margin: 6pt 0 10pt 0;
            padding-left: 20pt;
            line-height: 1.55;
        }

        .content ul li::marker {
            color: var(--brand);
        }

        .content ol li::marker {
            color: var(--brand);
            font-weight: 500;
        }

        .content figure {
            margin: 14pt 0;
        }

        .content img {
            max-width: 100%;
            border-radius: 4pt;
        }

        .content figcaption {
            font-size: 9pt;
            color: var(--stone);
            margin-top: 6pt;
            text-align: center;
        }

        .content table {
            width: 100%;
            border-collapse: collapse;
            font-size: 9.5pt;
            margin: 12pt 0;
        }

        .content table th {
            text-align: left;
            font-weight: 500;
            color: var(--dark-warm);
            padding: 6pt 8pt;
            border-bottom: 1pt solid var(--border);
        }

        .content table td {
            padding: 5pt 8pt;
            border-bottom: 0.3pt solid var(--border-soft);
            vertical-align: top;
        }

        @media print {
            body {
                padding: 0;
            }
        }
        """


# Global exporter instance
html_exporter = KamiExporter()
