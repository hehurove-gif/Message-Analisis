"""Parser de exportaciones TXT de WhatsApp (contrato v0.2). Punto de entrada: parse_file / parse_bytes / parse_text."""
from .config import ParsingConfig, load_config
from .importer import parse_bytes, parse_file, parse_text
from .results import CONTRACT_VERSION, ImportResult, Message

__all__ = ['parse_file', 'parse_bytes', 'parse_text', 'load_config', 'ParsingConfig', 'ImportResult', 'Message',
           'CONTRACT_VERSION']
