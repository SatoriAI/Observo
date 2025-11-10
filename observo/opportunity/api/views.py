from base64 import b64encode
from pathlib import Path

from django.conf import settings
from django.http import Http404, HttpResponse
from django.utils.text import slugify
from django.views.decorators.http import require_http_methods
from jinja2 import Template
from markdown_it import MarkdownIt
from weasyprint import HTML

from opportunity.models import Opportunity

_HTML_TEMPLATE = Template(
    r"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{{ doc_title }}</title>
    <style>
@page {
  size: A4;
  margin: 2.5cm 2cm 2.5cm 2cm;
  @top-left   { content: element(header-left); }
  @top-right  { content: element(header-right); }
  @top-center { content: ""; border-bottom: 1px solid #E5E7EB; padding-bottom: 8px; }
  @bottom-center {
    content: "{{ footer_text }}";
    font-size: 10pt; color: #000;
  }
}

@font-face {
  font-family: "Times New Roman";
  src: url("{{ font_url }}") format("truetype");
  font-weight: 400;
  font-style: normal;
}
@font-face {
  font-family: "Times New Roman";
  src: url("{{ font_url }}") format("truetype");
  font-weight: 700;
  font-style: normal;
}
@font-face {
  font-family: "Times New Roman";
  src: url("{{ font_url }}") format("truetype");
  font-weight: 400;
  font-style: italic;
}
@font-face {
  font-family: "Times New Roman";
  src: url("{{ font_url }}") format("truetype");
  font-weight: 700;
  font-style: italic;
}

.page-header-left  { position: running(header-left); }
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
h3.doc-title { text-align: center; }

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
    /* Marketing CTA */
    .cta-section { margin-top: 1.2em; padding-top: 0.6em; border-top: 1px solid #E5E7EB; }
    .cta-section h2 { font-size: 14pt; }
    .cta-section p { margin: 0.5em 0; }
    .cta-section ul { margin: 0.6em 0 0.6em 1.4em; }
    .cta-actions { text-align: center; }
    a.cta-button {
      display: inline-block;
      background: #1a73e8;
      color: #fff;
      text-decoration: none;
      padding: 10px 16px;
      border-radius: 6px;
      font-weight: bold;
    }
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
"""
)


def _file_to_data_uri(path: Path) -> str:
    mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
    data = b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def _ensure_title_in_markdown(title: str, md: str) -> str:
    stripped = md.lstrip()
    if stripped.startswith("#"):
        return md
    return (f'<h3 class="doc-title">{title}</h3>\n\n{md}') if title else md


@require_http_methods(["GET"])
def opportunity_summary_pdf(request, pk):
    # Look up the opportunity by UUID primary key
    try:
        opportunity = Opportunity.objects.get(pk=pk)
    except Opportunity.DoesNotExist:
        raise Http404("Opportunity not found.")

    # Prepare content
    title = opportunity.title or "Opportunity"
    summary_text = (opportunity.summary or "").strip() or "No summary available."

    md = MarkdownIt("commonmark").enable("table").enable("strikethrough")
    markdown_text = _ensure_title_in_markdown(title, summary_text)
    html_body = md.render(markdown_text)

    # Append marketing offer and Calendly CTA
    calendly_link = "https://calendly.com/opengrant/federal-grant-consult"
    marketing_html = f"""
<section class="cta-section">
  <h2>How we can help as OpenGrant</h2>
  <p>We help entrepreneurs win R&amp;D grants ($250K–$1.4M) at 3 times the industry success rate.</p>
  <p>Here’s how we can support you:</p>
  <ul>
    <li>Identify the right grant opportunities for your project.</li>
    <li>Write and submit your project white paper (10 pages of R&amp;D plans).</li>
    <li>Prepare and submit the full proposal (50–60 pages) and handle all compliance requirements.</li>
    <li>Provide a designated grant expert to guide you through the entire process, including resubmissions.</li>
  </ul>
  <p>Pricing: a one‑time retainer of $1,049 and a 3% success fee (paid only if we win).</p>
  <p class="cta-actions"><a href="{calendly_link}" class="cta-button">Schedule Your Free Consultation</a></p>
</section>
"""
    html_body = f"{html_body}\n{marketing_html}"

    # Header: OpenGrant logo on the left, identifier on the right
    logo_path = settings.BASE_DIR / "data" / "OpenGrant.png"
    logo_data_uri = _file_to_data_uri(logo_path) if logo_path.exists() else ""
    header_right_text = opportunity.identifier

    # Footer: placeholder contact info (as requested)
    footer_text = "OpenGrant Inc."

    # Absolute font URI to avoid resource resolution issues (ensures embedding)
    tnr_path = (settings.BASE_DIR / "data" / "fonts" / "TimesNewRoman.ttf").resolve()
    font_url = tnr_path.as_uri() if tnr_path.exists() else ""

    html_full = _HTML_TEMPLATE.render(
        html=html_body,
        logo_data_uri=logo_data_uri,
        header_right_text=header_right_text,
        footer_text=footer_text,
        doc_title=title,
        font_url=font_url,
    )

    # Generate PDF
    base_url = logo_path.parent.as_uri() if logo_data_uri else settings.BASE_DIR.resolve().as_uri()
    pdf_bytes = HTML(string=html_full, base_url=base_url).write_pdf()

    # Prepare response for download
    filename_part = slugify(opportunity.identifier or title) or "opportunity"
    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="[Summary] {filename_part.upper()}.pdf"'
    response["Access-Control-Expose-Headers"] = "Content-Disposition"
    return response
