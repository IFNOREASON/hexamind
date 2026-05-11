from pathlib import Path

from app.services.parsers import BaseParser


class TxtParser(BaseParser):
    async def parse(self, file_path: str | None = None, url: str | None = None) -> str:
        if not file_path:
            raise ValueError("file_path is required for TXT parsing")
        return Path(file_path).read_text(encoding="utf-8", errors="ignore")

    @staticmethod
    def supported_extensions() -> set[str]:
        return {"txt", "md", "csv"}
