"""
Multi-Agent Pipeline Definition
=================================
Defines the ADK agent hierarchy for the Multilingual QnA Generation System.

Architecture:
    SequentialAgent: multilingual_qna_pipeline
    ├── LlmAgent: document_parser        (Tools: parse_document)
    ├── LlmAgent: qna_generator          (Tools: save_qna_pairs)
    ├── LlmAgent: hindi_translator       (Tools: save_qna_pairs)
    ├── LlmAgent: marathi_translator     (Tools: save_qna_pairs)
    └── LlmAgent: excel_compiler         (Tools: compile_excel_report)
"""

# ─── Automatic Rate Limit Retry Monkey-Patch for LiteLLM/Groq ────────
import asyncio
import re
from google.adk.models.lite_llm import LiteLlm

original_generate_content_async = LiteLlm.generate_content_async

async def patched_generate_content_async(self, llm_request, stream=False):
    max_retries = 6
    base_delay = 5.0
    
    for attempt in range(max_retries):
        try:
            async for response in original_generate_content_async(self, llm_request, stream=stream):
                yield response
            return
        except Exception as e:
            err_name = type(e).__name__
            err_msg = str(e)
            
            # Catch any rate limit or 429 error from any library (litellm, openai, groq, etc.)
            is_rate_limit = (
                "ratelimit" in err_name.lower() or 
                "rate_limit" in err_name.lower() or 
                "rate limit" in err_msg.lower() or
                "429" in err_msg
            )
            
            if is_rate_limit:
                wait_time = base_delay * (1.5 ** attempt)
                # Parse wait duration from error message if available
                # E.g. "Please try again in 16.969999999s"
                time_match = re.search(r'(?:try again in|retry after|wait|in\s+)([\d\.]+)\s*s', err_msg, re.IGNORECASE)
                if time_match:
                    try:
                        wait_time = float(time_match.group(1)) + 1.5
                    except ValueError:
                        pass
                
                print(f"\n⚠️ Groq Rate Limit Hit. Waiting {wait_time:.2f}s before retry (Attempt {attempt+1}/{max_retries})...\n")
                
                try:
                    import streamlit as st
                    st.warning(f"⏳ **Rate limit hit on Groq**. Automatically waiting {wait_time:.1f}s to retry (Attempt {attempt+1}/{max_retries})...")
                except Exception:
                    pass
                    
                await asyncio.sleep(wait_time)
            else:
                # Not a rate limit error, raise immediately
                raise e
            
    # Final fallback attempt
    async for response in original_generate_content_async(self, llm_request, stream=stream):
        yield response

LiteLlm.generate_content_async = patched_generate_content_async
# ──────────────────────────────────────────────────────────────────────



from google.adk.agents import LlmAgent, SequentialAgent

from .tools.document_tools import parse_document, get_document_text
from .tools.qna_tools import save_qna_pairs, get_english_qna
from .tools.excel_tools import compile_excel_report
from .prompts import (
    DOCUMENT_PARSER_INSTRUCTION,
    QNA_GENERATOR_INSTRUCTION,
    HINDI_TRANSLATOR_INSTRUCTION,
    MARATHI_TRANSLATOR_INSTRUCTION,
    EXCEL_COMPILER_INSTRUCTION,
)


# ─── Default Configuration ───────────────────────────────────────────
DEFAULT_MODEL = "gemini-2.0-flash"
DEFAULT_NUM_PAIRS = 10
DEFAULT_OUTPUT_PATH = "QnA.xlsx"


def create_pipeline(
    model: str = DEFAULT_MODEL,
    num_pairs: int = DEFAULT_NUM_PAIRS,
    output_path: str = DEFAULT_OUTPUT_PATH,
) -> SequentialAgent:
    """Create the multi-agent QnA generation pipeline.

    Args:
        model: Gemini model name to use for all agents.
        num_pairs: Number of QnA pairs to generate.
        output_path: Path for the output Excel file.

    Returns:
        A SequentialAgent representing the full pipeline.
    """

    # ── Agent 1: Document Parser ──────────────────────────────────
    document_parser = LlmAgent(
        name="document_parser",
        model=model,
        instruction=DOCUMENT_PARSER_INSTRUCTION,
        description="Parses PDF, DOCX, and TXT documents to extract text content.",
        tools=[parse_document],
        output_key="parsed_document_output",
    )

    # ── Agent 2: QnA Generator ────────────────────────────────────
    qna_generator = LlmAgent(
        name="qna_generator",
        model=model,
        instruction=QNA_GENERATOR_INSTRUCTION.format(num_pairs=num_pairs),
        description="Generates English QnA pairs from document text.",
        tools=[get_document_text, save_qna_pairs],
        output_key="english_qna_output",
    )

    # ── Agent 3: Hindi Translator ─────────────────────────────────
    hindi_translator = LlmAgent(
        name="hindi_translator",
        model=model,
        instruction=HINDI_TRANSLATOR_INSTRUCTION,
        description="Translates English QnA pairs to Hindi.",
        tools=[save_qna_pairs],
        output_key="hindi_qna_output",
    )

    # ── Agent 4: Marathi Translator ───────────────────────────────
    marathi_translator = LlmAgent(
        name="marathi_translator",
        model=model,
        instruction=MARATHI_TRANSLATOR_INSTRUCTION,
        description="Translates English QnA pairs to Marathi.",
        tools=[save_qna_pairs],
        output_key="marathi_qna_output",
    )

    # ── Agent 5: Excel Compiler ───────────────────────────────────
    excel_compiler = LlmAgent(
        name="excel_compiler",
        model=model,
        instruction=EXCEL_COMPILER_INSTRUCTION.format(output_path=output_path),
        description="Compiles all QnA pairs into a styled Excel file.",
        tools=[compile_excel_report],
        output_key="excel_output_summary",
    )

    # ── Root Pipeline: Sequential Execution ───────────────────────
    pipeline = SequentialAgent(
        name="multilingual_qna_pipeline",
        description=(
            "End-to-end pipeline for generating multilingual QnA pairs. "
            "Parses a document, generates English QnA, translates to "
            "Hindi and Marathi, and outputs a styled Excel file."
        ),
        sub_agents=[
            document_parser,
            qna_generator,
            hindi_translator,
            marathi_translator,
            excel_compiler,
        ],
    )

    return pipeline


# ── Default root_agent for ADK CLI (`adk run` / `adk web`) ──────────
root_agent = create_pipeline()


# ─── Mock LLM for Offline / Demo Mode ────────────────────────────────
import json
import re
from typing import AsyncGenerator
from google.genai import types
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.adk.models.registry import LLMRegistry


class MockLlm(BaseLlm):
    """Mock LLM to run the multi-agent pipeline in offline/demo mode."""

    @classmethod
    def supported_models(cls) -> list[str]:
        return ["mock-model"]

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        sys_inst = llm_request.config.system_instruction or ""
        history = llm_request.contents

        last_msg = history[-1] if history else None
        last_part = last_msg.parts[-1] if last_msg and last_msg.parts else None

        # 📄 AGENT 1: Document Parser
        if "Document Parsing Specialist" in sys_inst:
            if last_part and hasattr(last_part, 'function_response') and last_part.function_response:
                fr = last_part.function_response
                res = fr.response.get("result", "") if hasattr(fr, "response") and isinstance(fr.response, dict) else str(fr.response)
                yield LlmResponse(
                    content=types.Content(role="model", parts=[types.Part.from_text(text=res)]),
                    partial=False
                )
            else:
                user_text = ""
                for msg in history:
                    if msg.role == 'user':
                        for part in msg.parts:
                            if part.text:
                                user_text += part.text + " "
                
                path_match = re.search(r'(?:at|file|path):\s*([^\s\n]+)', user_text, re.IGNORECASE)
                file_path = path_match.group(1) if path_match else "sample_files/sample.txt"
                file_path = file_path.strip('"').strip("'")
                
                yield LlmResponse(
                    content=types.Content(role="model", 
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="parse_document",
                                    args={"file_path": file_path}
                                )
                            )
                        ]
                    ),
                    partial=False
                )

        # 🧠 AGENT 2: QnA Generator
        elif "Expert Question-Answer Pair Generator" in sys_inst:
            if last_part and hasattr(last_part, 'function_response') and last_part.function_response and last_part.function_response.name == "save_qna_pairs":
                qna_json = ""
                for msg in reversed(history):
                    if msg.role == 'model':
                        for part in msg.parts:
                            if part.function_call and part.function_call.name == "save_qna_pairs":
                                qna_json = part.function_call.args.get("qna_json", "")
                                break
                    if qna_json:
                        break
                yield LlmResponse(
                    content=types.Content(role="model", parts=[types.Part.from_text(text=qna_json)]),
                    partial=False
                )
            elif last_part and hasattr(last_part, 'function_response') and last_part.function_response and last_part.function_response.name == "get_document_text":
                fr = last_part.function_response
                doc_text = fr.response.get("result", "") if hasattr(fr, "response") and isinstance(fr.response, dict) else str(fr.response)
                
                mock_pairs = _generate_mock_english_pairs(doc_text)
                qna_json = json.dumps(mock_pairs, ensure_ascii=False, indent=2)
                
                yield LlmResponse(
                    content=types.Content(role="model", 
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="save_qna_pairs",
                                    args={"qna_json": qna_json, "language": "english"}
                                )
                            )
                        ]
                    ),
                    partial=False
                )
            else:
                file_path = _find_file_path_in_history(history)
                yield LlmResponse(
                    content=types.Content(role="model", 
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="get_document_text",
                                    args={"file_path": file_path}
                                )
                            )
                        ]
                    ),
                    partial=False
                )

        # 🇮🇳 AGENT 3 & 4: Hindi & Marathi Translators
        elif "Translator" in sys_inst:
            is_hindi = "Hindi" in sys_inst
            lang = "hindi" if is_hindi else "marathi"
            
            if last_part and hasattr(last_part, 'function_response') and last_part.function_response and last_part.function_response.name == "save_qna_pairs":
                # Turn 2: final response
                qna_json = ""
                for msg in reversed(history):
                    if msg.role == 'model':
                        for part in msg.parts:
                            if part.function_call and part.function_call.name == "save_qna_pairs":
                                qna_json = part.function_call.args.get("qna_json", "")
                                break
                    if qna_json:
                        break
                yield LlmResponse(
                    content=types.Content(role="model", parts=[types.Part.from_text(text=qna_json)]),
                    partial=False
                )
            else:
                # Turn 1: translate and call save_qna_pairs directly
                english_json = _find_qna_json_in_history(history, "english")
                try:
                    en_pairs = json.loads(english_json)
                except Exception:
                    en_pairs = []
                
                translated_pairs = _translate_pairs(en_pairs, lang)
                trans_json = json.dumps(translated_pairs, ensure_ascii=False, indent=2)
                
                yield LlmResponse(
                    content=types.Content(role="model", 
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="save_qna_pairs",
                                    args={"qna_json": trans_json, "language": lang}
                                )
                            )
                        ]
                    ),
                    partial=False
                )

        # 📊 AGENT 5: Excel Compiler
        elif "Excel Report Compiler" in sys_inst:
            if last_part and hasattr(last_part, 'function_response') and last_part.function_response and last_part.function_response.name == "compile_excel_report":
                fr = last_part.function_response
                res = fr.response.get("result", "") if hasattr(fr, "response") and isinstance(fr.response, dict) else str(fr.response)
                yield LlmResponse(
                    content=types.Content(role="model", parts=[types.Part.from_text(text=res)]),
                    partial=False
                )
            else:
                english_json = _find_qna_json_in_history(history, "english")
                hindi_json = _find_qna_json_in_history(history, "hindi")
                marathi_json = _find_qna_json_in_history(history, "marathi")
                
                out_path_match = re.search(r'compile_excel_report.*?output_path:\s*([^\s\n]+)', sys_inst, re.IGNORECASE)
                out_path = out_path_match.group(1) if out_path_match else "QnA.xlsx"
                out_path = out_path.strip('"').strip("'")
                
                yield LlmResponse(
                    content=types.Content(role="model", 
                        parts=[
                            types.Part(
                                function_call=types.FunctionCall(
                                    name="compile_excel_report",
                                    args={
                                        "english_qna_json": english_json,
                                        "hindi_qna_json": hindi_json,
                                        "marathi_qna_json": marathi_json,
                                        "output_path": out_path
                                    }
                                )
                            )
                        ]
                    ),
                    partial=False
                )

        else:
            yield LlmResponse(
                content=types.Content(role="model", parts=[types.Part.from_text(text="I am the mock coordinator. How can I help you?")]),
                partial=False
            )


def _find_file_path_in_history(history) -> str:
    for msg in history:
        for part in msg.parts:
            if part.function_call and part.function_call.name == "parse_document":
                return part.function_call.args.get("file_path", "sample_files/sample.txt")
    return "sample_files/sample.txt"


def _find_qna_json_in_history(history, lang: str) -> str:
    lang = lang.lower()
    import re
    
    # 1. Search for JSON array in text strings (robust to agent context conversions)
    for msg in reversed(history):
        for part in msg.parts:
            text = part.text or ""
            if not text:
                continue
            
            if ("save_qna_pairs" in text or lang in text.lower()) and "[" in text:
                json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                    
    # 2. Look for raw FunctionCall args in model history (if not converted)
    for msg in reversed(history):
        for part in msg.parts:
            if part.function_call and part.function_call.name == "save_qna_pairs":
                args = part.function_call.args
                if args and args.get("language", "").lower() == lang:
                    return args.get("qna_json", "")
                    
    # 3. Fallback: find any text block with a JSON array
    for msg in reversed(history):
        for part in msg.parts:
            text = part.text or ""
            if "[" in text and "{" in text:
                json_match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
                if json_match:
                    return json_match.group(0)
                    
    return "[]"


def _generate_mock_english_pairs(doc_text: str) -> list[dict]:
    if "Dartmouth Conference" in doc_text or "Artificial Intelligence" in doc_text:
        return [
            {
                "question": "When was the field of Artificial Intelligence formally founded, and who organized it?",
                "answer": "The field of Artificial Intelligence was formally founded in 1956 at the Dartmouth Conference. It was organized by John McCarthy, Marvin Minsky, Nathaniel Rochester, and Claude Shannon."
            },
            {
                "question": "What is the difference between Narrow AI and General AI?",
                "answer": "Narrow AI (or Weak AI) is designed to perform specific tasks such as virtual assistants or recommendation systems. General AI (or Strong AI) is a theoretical form of AI possessing human-like cognitive abilities to understand and learn across different domains, which has not yet been achieved."
            },
            {
                "question": "What are the three main types of machine learning?",
                "answer": "The three main types of machine learning are supervised learning (learning from labeled data), unsupervised learning (discovering patterns in unlabeled data), and reinforcement learning (learning via interaction with rewards or penalties)."
            }
        ]
    
    lines = [l.strip() for l in doc_text.split('\n') if len(l.strip()) > 40]
    pairs = []
    for i, line in enumerate(lines[:3]):
        words = line.split()
        concept = " ".join(words[:3]) if len(words) >= 3 else "the document content"
        pairs.append({
            "question": f"What key details are described regarding '{concept}' in the document?",
            "answer": f"According to the document, the following details are provided: {line}"
        })
    if not pairs:
        pairs = [
            {
                "question": "What is the primary topic of the uploaded document?",
                "answer": "The uploaded document contains plain text information that the system has successfully parsed."
            }
        ]
    return pairs


def _translate_pairs(pairs: list[dict], language: str) -> list[dict]:
    translated = []
    
    predefined_hi = {
        "When was the field of Artificial Intelligence formally founded, and who organized it?": 
            ("आर्टिफिशियल इंटेलिजेंस (AI) क्षेत्र की औपचारिक स्थापना कब हुई थी और इसका आयोजन किसने किया था?", 
             "आर्टिफिशियल इंटेलिजेंस क्षेत्र की औपचारिक स्थापना 1956 में डार्टमाउथ सम्मेलन में की गई थी। इसका आयोजन जॉन मैकार्थी, मार्विन मिन्स्की, नथानिएल रोचेस्टर और क्लाउड शैनन द्वारा किया गया था।"),
        "What is the difference between Narrow AI and General AI?":
            ("नैरो एआई (Narrow AI) और जनरल एआई (General AI) में क्या अंतर है?",
             "नैरो एआई किसी विशेष कार्य को करने के लिए डिज़ाइन किया गया है जैसे वर्चुअल असिस्टेंट। जनरल एआई एआई का एक सैद्धांतिक रूप है जिसमें विभिन्न क्षेत्रों में सीखने और समझने की मानव-स्तर की संज्ञानात्मक क्षमताएं होती हैं, जिसे अभी तक प्राप्त नहीं किया गया है।"),
        "What are the three main types of machine learning?":
            ("मशीन लर्निंग के तीन मुख्य प्रकार कौन से हैं?",
             "मशीन लर्निंग के तीन मुख्य प्रकार हैं: सुपरवाइज़्ड लर्निंग (लlabeled डेटा से सीखना), अनसुपरवाइज़्ड लर्निंग (unlabeled डेटा में पैटर्न खोजना), और रीइन्फोर्समेंट लर्निंग (पुरस्कार या दंड के माध्यम से सीखना)।")
    }
    
    predefined_mr = {
        "When was the field of Artificial Intelligence formally founded, and who organized it?": 
            ("कृत्रिम बुद्धिमत्ता (AI) क्षेत्राची अधिकृतपणे स्थापना केव्हा झाली आणि त्याचे आयोजन कोणी केले?", 
             "कृत्रिम बुद्धिमत्ता क्षेत्राची अधिकृतपणे स्थापना 1956 मध्ये डार्टमाउथ परिषदेत झाली. याचे आयोजन जॉन मॅककार्थी, मार्विन मिन्स्की, नथानिएल रोचेस्टर आणि क्लॉड शॅनन यांनी केले होते."),
        "What is the difference between Narrow AI and General AI?":
            ("नॅरो एआय (Narrow AI) आणि जनरल एआय (General AI) मधील फरक काय आहे?",
             "नॅरो एआय विशिष्ट कामे करण्यासाठी डिझाइन केलेले आहे जसे की व्हर्च्युअल असिस्टंट. जनरल एआय हे एआयचे एक सैद्धांतिक रूप आहे ज्यामध्ये मानवासारखी संज्ञानात्मक क्षमता असते, जी अद्याप प्राप्त झालेली नाही."),
        "What are the three main types of machine learning?":
            ("मशीन लर्निंगचे तीन मुख्य प्रकार कोणते आहेत?",
             "मशीन लर्निंगचे तीन मुख्य प्रकार आहेत: सुपरव्हाइझ्ड लर्निंग (लेबल केलेल्या डेटावरून शिकणे), अनसुपरव्हाइझ्ड लर्निंग (लेबल नसलेल्या डेटामधील पॅटर्न शोधणे), आणि रीइन्फोर्समेंट लर्निंग (बक्षीस किंवा दंडाद्वारे शिकणे).")
    }
    
    for p in pairs:
        q = p.get("question", "")
        a = p.get("answer", "")
        
        if language == "hindi":
            if q in predefined_hi:
                t_q, t_a = predefined_hi[q]
            else:
                t_q = f"दस्तावेज़ के अनुसार: {q} का अनुवाद क्या है?"
                t_a = f"अनुवादित उत्तर: {a}"
        else:  # marathi
            if q in predefined_mr:
                t_q, t_a = predefined_mr[q]
            else:
                t_q = f"दस्तऐवजानुसार: {q} चे भाषांतर काय आहे?"
                t_a = f"भाषांतरित उत्तर: {a}"
                
        translated.append({"question": t_q, "answer": t_a})
        
    return translated


# ── Register MockLlm in LLMRegistry ───────────────────────────────
LLMRegistry._register("mock-model", MockLlm)

