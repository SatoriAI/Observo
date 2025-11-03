from base64 import b64encode
from datetime import date
from pathlib import Path

from jinja2 import Template
from markdown_it import MarkdownIt
from weasyprint import HTML


class MarkdownPDFGenerator:
    _HTML_TEMPLATE = Template(r"""
    <!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8" />
      <title>{{ doc_title }}</title>
      <style>
@page {
  size: A4;
  margin: 2.5cm 2cm 2.5cm 2cm;     /* enough space for header */
  /* Pin content to page edges via margin boxes */
  @top-left { content: element(header-left); }
  @top-right { content: element(header-right); }
  /* Draw a subtle rule across the header width */
  @top-center { content: ""; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; }
  @bottom-center {
    content: "Page " counter(page) " of " counter(pages);
    font-size: 10pt; color: #000;
  }
}

/* Running elements to feed @page margin boxes */
.page-header-left { position: running(header-left); }
.page-header-right { position: running(header-right); text-align: right; white-space: nowrap; font-size: 10pt; color: #000; }

img.logo {
  height: 15mm;
  object-fit: contain;
}

        body {
          font-family: "Times New Roman", Times, serif;
          font-size: 11pt;
          line-height: 1.45;
        }

        h1, h2, h3 { page-break-after: avoid; margin-top: 0.5em; }
        h1 { font-size: 22pt; }
        h2 { font-size: 16pt; }
        h3 { font-size: 13pt; }

        p { margin: 0.6em 0; text-align: justify; text-justify: inter-word; hyphens: auto; }
        ul, ol { margin: 0.6em 0 0.6em 1.4em; }

        code, pre {
          font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
                       "Liberation Mono", "Courier New", monospace;
        }
        pre {
          white-space: pre-wrap;
          word-break: break-word;
          background: #f7f7f7;
          border: 1px solid #eee;
          border-radius: 6px;
          padding: 10px;
          font-size: 9.5pt;
          margin: 0.8em 0;
        }

        blockquote {
          border-left: 3px solid #ddd;
          padding-left: 10px;
          color: #555;
          margin: 0.6em 0;
        }

        img { max-width: 100%; page-break-inside: avoid; }
        table { border-collapse: collapse; width: 100%; margin: 0.6em 0; }
        th, td { border: 1px solid #e5e7eb; padding: 6px 8px; }
        th { background: #f3f4f6; text-align: left; }
      </style>
    </head>
    <body>
        <div class="page-header-left">
          {% if logo_data_uri %}
            <img class="logo" src="{{ logo_data_uri }}" alt="Logo">
          {% endif %}
        </div>
        <div class="page-header-right">{{ header_right_text }}</div>

      <main>
        {{ html|safe }}
      </main>

    </body>
    </html>
    """)

    def __init__(self, base_dir: Path, logo_relative_path: str | None = None) -> None:
        self.base_dir: Path = Path(base_dir)
        self.logo_path: Path | None = self.base_dir / logo_relative_path if logo_relative_path else None

    # ---------- public API ----------
    def generate(self, title: str, text: str, output_path: str, header_right_text: str | None = None) -> None:
        """
        Render the provided Markdown `text` into a PDF at `output_path`.
        A top-level H1 will be prepended using `title` if the Markdown doesn't start with a heading.

        Args:
            title: Document title (also used for HTML <title>).
            text: Markdown content (LLM result).
            output_path: Where to write the PDF (str or path-like).
        """
        markdown_text = self._ensure_title_in_markdown(title, text)

        md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
        html_body = md.render(markdown_text)

        html_full = self._HTML_TEMPLATE.render(
            html=html_body,
            logo_data_uri=self._file_to_data_uri(self.logo_path) if self.logo_path else "",
            header_right_text=header_right_text or self._pretty_date(date.today()),
            doc_title=title or "Document",
        )

        base_url = self.logo_path.parent.as_uri() if self.logo_path else self.base_dir.resolve().as_uri()
        HTML(string=html_full, base_url=base_url).write_pdf(str(output_path))

    # ---------- helpers ----------
    @staticmethod
    def _ensure_title_in_markdown(title: str, md: str) -> str:
        stripped = md.lstrip()
        if stripped.startswith("#"):
            return md
        if title:
            return f"## {title}\n\n{md}"
        return md

    @staticmethod
    def _ordinal(n: int) -> str:
        if 10 <= n % 100 <= 20:
            suffix = "th"
        else:
            suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suffix}"

    def _pretty_date(self, d: date) -> str:
        # e.g., "17th October 2025"
        return f"{self._ordinal(d.day)} {d.strftime('%B %Y')}"

    @staticmethod
    def _file_to_data_uri(path: Path) -> str:
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        data = b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"
