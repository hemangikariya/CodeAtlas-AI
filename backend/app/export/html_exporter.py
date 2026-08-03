import re
from backend.app.export.markdown_exporter import MarkdownExporter


class HTMLExporter:
    """
    Exports a structured artifact into a beautifully styled HTML file.
    Uses regex transformations to provide markdown-to-HTML formatting.
    """

    @staticmethod
    def export(artifact: dict) -> str:
        md = MarkdownExporter.export(artifact)

        # Apply simple HTML tags substitutions
        html = md

        # Convert blockquotes
        html = re.sub(r"^> (.*?)$", r"<blockquote>\1</blockquote>", html, flags=re.MULTILINE)

        # Convert bold markers
        html = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html)

        # Convert lists items
        html = re.sub(r"^- (.*?)$", r"<li>\1</li>", html, flags=re.MULTILINE)

        # Convert headers
        html = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html, flags=re.MULTILINE)
        html = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html, flags=re.MULTILINE)
        html = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html, flags=re.MULTILINE)

        # Convert code blocks
        html = re.sub(r"```(\w*)\n(.*?)\n```", r"<pre><code>\2</code></pre>", html, flags=re.DOTALL)

        # Segment paragraphs
        lines = html.split("\n")
        formatted_lines = []
        for line in lines:
            line_s = line.strip()
            if not line_s:
                continue
            if line_s.startswith("<h") or line_s.startswith("<pre") or line_s.startswith("</pre") or line_s.startswith("<block") or line_s.startswith("</block") or line_s.startswith("<li") or line_s.startswith("<hr"):
                formatted_lines.append(line)
            else:
                formatted_lines.append(f"<p>{line}</p>")

        body = "\n".join(formatted_lines)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{artifact.get('title', 'CodeAtlas AI Artifact')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #334155;
            background-color: #f8fafc;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }}
        h1 {{
            font-size: 2.25rem;
            color: #0f172a;
            border-bottom: 2px solid #e2e8f0;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        h2 {{
            font-size: 1.5rem;
            color: #1e293b;
            margin-top: 30px;
            margin-bottom: 15px;
        }}
        p {{
            margin-bottom: 1.25rem;
        }}
        blockquote {{
            border-left: 4px solid #3b82f6;
            padding: 10px 20px;
            margin: 20px 0;
            background-color: #eff6ff;
            color: #1e40af;
            font-style: italic;
        }}
        pre {{
            background-color: #0f172a;
            color: #f8fafc;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            margin: 20px 0;
        }}
        code {{
            font-family: Consolas, Monaco, "Andale Mono", monospace;
            font-size: 0.9em;
        }}
        li {{
            margin-bottom: 8px;
        }}
        hr {{
            border: 0;
            border-top: 1px solid #e2e8f0;
            margin: 40px 0;
        }}
    </style>
</head>
<body>
    {body}
</body>
</html>
"""
