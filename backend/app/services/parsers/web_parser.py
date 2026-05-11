import httpx
from bs4 import BeautifulSoup

from app.services.parsers import BaseParser


class WebParser(BaseParser):
    async def parse(self, file_path: str | None = None, url: str | None = None) -> str:
        if not url:
            raise ValueError("url is required for web parsing")

        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script/style tags
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n".join(lines)
