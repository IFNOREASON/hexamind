from app.services.parsers import BaseParser


class DocxParser(BaseParser):
    async def parse(self, file_path: str | None = None, url: str | None = None) -> str:
        if not file_path:
            raise ValueError("file_path is required for DOCX parsing")
        from docx import Document

        doc = Document(file_path)
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)

    @staticmethod
    def supported_extensions() -> set[str]:
        return {"docx"}
