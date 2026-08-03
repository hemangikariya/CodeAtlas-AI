class MarkdownExporter:
    """
    Exports a structured artifact payload into standard GitHub Flavored Markdown.
    """

    @staticmethod
    def export(artifact: dict) -> str:
        title = artifact.get("title", "CodeAtlas AI Generated Artifact")
        summary = artifact.get("summary", "")
        
        md = f"# {title}\n\n"
        if summary:
            md += f"> **Summary**: {summary}\n\n"

        sections = artifact.get("sections", [])
        for section in sections:
            heading = section.get("heading", "")
            content = section.get("content", "")
            if heading:
                md += f"## {heading}\n\n"
            if content:
                md += f"{content}\n\n"

        references = artifact.get("references", [])
        if references:
            md += "## References\n\n"
            for ref in references:
                md += f"- {ref}\n"
            md += "\n"

        md += "---\n"
        md += f"* **Generator**: {artifact.get('generator', 'Unknown')} (v{artifact.get('generator_version', '1.0')})\n"
        md += f"* **Prompt Version**: {artifact.get('prompt_version', '1.0')}\n"
        md += f"* **Artifact Version**: {artifact.get('artifact_version', '1.0')}\n"
        md += f"* **Knowledge Snapshot**: {artifact.get('knowledge_snapshot', 'None')}\n"
        md += f"* **Created At**: {artifact.get('created_at', '')}\n"

        return md
