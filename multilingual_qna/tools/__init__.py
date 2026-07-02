"""
ADK Tools for Multilingual QnA Generation System.

This package contains tool functions that ADK agents use to:
- Parse documents (PDF, DOCX, TXT)
- Manage QnA pairs in session state
- Generate styled Excel output files
"""

from .document_tools import parse_document, get_document_text
from .qna_tools import save_qna_pairs, get_english_qna
from .excel_tools import compile_excel_report

__all__ = [
    "parse_document",
    "get_document_text",
    "save_qna_pairs",
    "get_english_qna",
    "compile_excel_report",
]
