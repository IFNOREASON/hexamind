from app.services.parsers import BaseParser
from app.services.parsers.pdf_parser import PdfParser
from app.services.parsers.docx_parser import DocxParser
from app.services.parsers.txt_parser import TxtParser
from app.services.parsers.web_parser import WebParser


_PARSERS: dict[str, BaseParser] = {}


def _init_parsers():
    for parser_cls in [PdfParser, DocxParser, TxtParser]:
        instance = parser_cls()
        for ext in parser_cls.supported_extensions():
            _PARSERS[ext] = instance


_init_parsers()
_web_parser = WebParser()


def get_parser(file_type: str, source_type: str) -> BaseParser | None:
    """Get the appropriate parser for a given file/source type."""
    if source_type == "link":
        return _web_parser
    return _PARSERS.get(file_type)
