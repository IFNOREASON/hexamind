from abc import ABC, abstractmethod


class BaseParser(ABC):
    """Abstract base parser for extracting text from various source types."""

    @abstractmethod
    async def parse(self, file_path: str | None = None, url: str | None = None) -> str:
        """Extract plaintext content from a source.

        Args:
            file_path: Local file path (for document types)
            url: URL (for link types)

        Returns:
            Extracted plaintext content
        """

    @staticmethod
    def supported_extensions() -> set[str]:
        return set()
