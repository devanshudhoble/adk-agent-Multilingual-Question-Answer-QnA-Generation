"""
Multilingual QnA Generation System — ADK Agent Package
========================================================
A multi-agent pipeline built with Google ADK (Agent Development Kit)
that generates Question-Answer pairs from documents in English, Hindi, and Marathi.

Usage with ADK CLI:
    adk run multilingual_qna
    adk web

Usage programmatically:
    from multilingual_qna.agent import create_pipeline
    pipeline = create_pipeline(num_pairs=10, output_path="QnA.xlsx")
"""

from .agent import root_agent, create_pipeline

__all__ = ["root_agent", "create_pipeline"]
