SUMMARIZE_COMPANY_FROM_HTML = """You are given raw HTML content scraped from a company's website.
Ignore all navigation menus, repeated elements, formatting, or unrelated links.

Focus only on the main descriptive and informational parts of the content.
Summarize what this company or project is doing in 3–6 sentences focusing on anything that constitutes R&D activities
or can be the foundation for future R&D activities.

Focus on what niche this company operates in and what it focuses on in this niche.

The summary should be concise, clear, and written in plain English with only ASCII characters.
Do not include bullet points, markdown, HTML, or special characters — only plain text.

--------
Context:
{company}
"""
