"""
QnA Management Tools for ADK Agents
=====================================
Provides tools for saving and retrieving QnA pairs in shared session state.
Enables data flow between QnA generator and translator agents.
"""

import json
import re


def save_qna_pairs(qna_json: str, language: str) -> str:
    """Save generated or translated QnA pairs for a specific language.

    Use this tool after generating English QnA pairs or after translating
    QnA pairs to Hindi or Marathi. The pairs must be in valid JSON format.

    Args:
        qna_json: A JSON string containing an array of objects, each with
                  'question' and 'answer' keys. Example:
                  '[{"question": "What is AI?", "answer": "AI is..."}]'
        language: The language of these QnA pairs. Must be exactly one of:
                  'english', 'hindi', or 'marathi' (case-insensitive).

    Returns:
        A confirmation message with the count of pairs saved, or an error
        message if the input is invalid.
    """
    language = language.lower().strip()
    valid_languages = ("english", "hindi", "marathi")
    if language not in valid_languages:
        return (
            f"Error: Invalid language '{language}'. "
            f"Must be one of: {', '.join(valid_languages)}"
        )

    try:
        cleaned = _clean_json_response(qna_json)
        pairs = json.loads(cleaned)

        if not isinstance(pairs, list):
            # Handle wrapped formats like {"qna": [...]}
            if isinstance(pairs, dict):
                for key in ["qna", "qna_pairs", "pairs", "data"]:
                    if key in pairs and isinstance(pairs[key], list):
                        pairs = pairs[key]
                        break
                else:
                    return "Error: JSON must be an array of QnA objects."
            else:
                return "Error: JSON must be an array of QnA objects."

        # Normalize keys to lowercase
        normalized = []
        for pair in pairs:
            q = pair.get("question", pair.get("Question", "")).strip()
            a = pair.get("answer", pair.get("Answer", "")).strip()
            if q and a:
                normalized.append({"question": q, "answer": a})

        if not normalized:
            return "Error: No valid QnA pairs found. Each object needs 'question' and 'answer' keys."

        # Return the validated JSON for the agent to pass via output_key
        result_json = json.dumps(normalized, ensure_ascii=False, indent=2)
        return (
            f"SUCCESS: Validated and saved {len(normalized)} {language.title()} QnA pairs.\n"
            f"SAVED_QNA_JSON:\n{result_json}"
        )

    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON format — {str(e)}. Please output valid JSON."


def get_english_qna(english_qna_data: str) -> str:
    """Parse and return English QnA pairs that need to be translated.

    Use this tool to retrieve the English QnA pairs for translation.
    Pass the English QnA JSON data that was generated in the previous step.

    Args:
        english_qna_data: The JSON string of English QnA pairs from the
                         previous agent's output.

    Returns:
        The validated JSON string of English QnA pairs ready for translation.
    """
    try:
        cleaned = _clean_json_response(english_qna_data)
        # Try to extract just the JSON array from the text
        # The input might contain "SUCCESS: ..." prefix from save_qna_pairs
        json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)

        pairs = json.loads(cleaned)
        if isinstance(pairs, list) and len(pairs) > 0:
            return json.dumps(pairs, ensure_ascii=False, indent=2)
        return "Error: Could not parse English QnA pairs."
    except (json.JSONDecodeError, Exception) as e:
        return f"Error parsing English QnA: {str(e)}. Raw input: {english_qna_data[:500]}"


def _clean_json_response(text: str) -> str:
    """Clean LLM response to extract valid JSON."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()
