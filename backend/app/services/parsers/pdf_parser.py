from app.services.parsers import BaseParser


class PdfParser(BaseParser):
    async def parse(self, file_path: str | None = None, url: str | None = None) -> str:
        if not file_path:
            raise ValueError("file_path is required for PDF parsing")
        from pypdf import PdfReader

        reader = PdfReader(file_path)
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        return "\n\n".join(pages)

    @staticmethod
    def supported_extensions() -> set[str]:
        return {"pdf"}
