import base64
import os
import shutil
import tempfile
from pathlib import Path

from markdown_pdf import MarkdownPdf, Section
from pylatex import Command, Document, NoEscape, Package, escape_latex


class LaTeXPDFGenerator:
    def __init__(self, base_dir: Path, logo_relative_path: str | None = None) -> None:
        self.logo_path: Path = base_dir / logo_relative_path

    def _build_document(self, title: str, text: str) -> Document:
        doc = Document(documentclass="article", document_options=["12pt", "a4paper"])
        # Packages
        doc.packages.append(Package("inputenc", options=["utf8"]))
        doc.packages.append(Package("fontenc", options=["T1"]))
        doc.packages.append(Package("graphicx"))
        doc.packages.append(Package("geometry", options=["margin=1in"]))
        doc.packages.append(Package("fancyhdr"))
        doc.packages.append(Package("lastpage"))
        doc.packages.append(Package("setspace"))
        doc.packages.append(Package("newtxtext"))
        doc.packages.append(Package("newtxmath"))

        # Header and footer
        doc.preamble.append(NoEscape(r"\pagestyle{fancy}"))
        doc.preamble.append(NoEscape(r"\fancyhf{}"))
        doc.preamble.append(NoEscape(r"\setlength{\headheight}{40pt}"))
        doc.preamble.append(NoEscape(r"\addtolength{\topmargin}{-10pt}"))

        if self.logo_path and self.logo_path.exists():
            # Do not escape file paths for graphicx; escaping hyphens breaks paths
            logo_tex_path = self.logo_path.as_posix()
            doc.preamble.append(NoEscape(r"\fancyhead[L]{\includegraphics[height=1.2cm]{" + logo_tex_path + r"}}"))
        else:
            doc.preamble.append(NoEscape(r"\fancyhead[L]{\textbf{OpenGrant}}"))
        doc.preamble.append(NoEscape(r"\fancyhead[R]{\today}"))

        doc.preamble.append(NoEscape(r"\fancyfoot[C]{\thepage\ of \pageref{LastPage}}"))

        # Line spacing
        doc.preamble.append(NoEscape(r"\setstretch{1.2}"))

        # Title style
        doc.preamble.append(NoEscape(r"\makeatletter"))
        doc.preamble.append(
            NoEscape(r"\renewcommand{\maketitle}{\begin{center}{\Large\bfseries \@title \par}\end{center}}")
        )
        doc.preamble.append(NoEscape(r"\makeatother"))

        # Title
        doc.preamble.append(Command("title", NoEscape(escape_latex(title or ""))))

        # Body
        doc.append(NoEscape(r"\maketitle"))
        paragraphs = (text or "").replace("\r\n", "\n").split("\n\n")
        for idx, para in enumerate(paragraphs):
            if para.strip() == "":
                continue
            doc.append(NoEscape(escape_latex(para)))
            if idx < len(paragraphs) - 1:
                doc.append(NoEscape("\n\n"))

        return doc

    def generate(self, title: str, text: str, output_path: str) -> None:
        if not shutil.which("latexmk"):
            raise RuntimeError(
                "The 'latexmk' compiler was found in PATH. Install a TeX distribution and ensure it is in PATH"
            )

        try:
            doc = self._build_document(title=title, text=text)
            with tempfile.TemporaryDirectory() as tmpdir:
                out_base = os.path.join(tmpdir, "document")
                doc.generate_pdf(out_base, clean_tex=True, silent=True, compiler="latexmk", compiler_args=["-pdf"])
                shutil.copyfile(out_base + ".pdf", output_path)
        except Exception as exc:
            raise RuntimeError(f"LaTeX PDF generation failed: {exc}") from exc


class MarkdownPDFGenerator:
    def __init__(self, base_dir: Path, logo_relative_path: str | None = None) -> None:
        self.logo_path: Path = base_dir / logo_relative_path

    def generate(self, title: str, text: str, output_path: str) -> None:
        try:
            normalized_title = title or ""
            normalized_text = text or ""

            # Build markdown with inline header (logo/date) and title
            normalized_text = normalized_text.replace("\r\n", "\n")
            parts: list[str] = []

            # Build a two-column header (logo left, date right) on the same line
            if self.logo_path and self.logo_path.exists():
                with open(self.logo_path, "rb") as logo_file:
                    encoded_logo = base64.b64encode(logo_file.read()).decode("ascii")
                left_html = f'<img class="logo" alt="OpenGrant" src="data:image/png;base64,{encoded_logo}" />'
            else:
                left_html = '<strong class="brand">OpenGrant</strong>'

            header_html = f'<div class="og-header">' f'<span class="og-left">{left_html}</span>' f"</div>"
            parts.append(header_html)
            parts.append("")  # blank line

            if normalized_title:
                parts.append(f"# {normalized_title}")
                parts.append("")

            parts.append(normalized_text)
            markdown_full = "\n".join(parts)

            # Minimal CSS compatible with MuPDF (avoid @page margin boxes)
            user_css = """
.og-header { width: 100%; margin-bottom: 8px; display: flex; align-items: center; }
.og-left { text-align: left; }
.brand { font-weight: 700; font-size: 28px; line-height: 1; display: block; }
.logo { height: 48px; display: block; }
h1 { text-align: center; }
p { text-align: justify; }
body { line-height: 1.2; }
"""

            pdf = MarkdownPdf()
            pdf.add_section(Section(markdown_full), user_css=user_css)
            pdf.save(output_path)
        except Exception as exc:
            raise RuntimeError(f"Markdown PDF generation failed: {exc}") from exc
