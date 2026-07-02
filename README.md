# 🌐 Multilingual QnA Generator — ADK Agent System

> **An intelligent multi-agent system built with Google ADK (Agent Development Kit) that automatically generates Question-Answer pairs from documents in English, Hindi, and Marathi.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Google ADK](https://img.shields.io/badge/Google_ADK-Agent_Framework-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Gemini](https://img.shields.io/badge/Gemini_AI-2.0_Flash-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Streamlit](https://img.shields.io/badge/Streamlit-UI-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#-architecture)
- [Agent Pipeline](#-agent-pipeline)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Technology Stack](#-technology-stack)
- [Output Format](#-output-format)

---

## Overview

This system leverages **Google's Agent Development Kit (ADK)** to create a sophisticated multi-agent pipeline that:

1. **Parses** documents in PDF, DOCX, or TXT format
2. **Generates** intelligent, context-aware QnA pairs in English using Gemini AI
3. **Translates** the QnA pairs to Hindi (हिन्दी) and Marathi (मराठी)
4. **Exports** everything into a professionally styled Excel file with 3 language-specific sheets

### Why ADK?

Unlike traditional single-script approaches, this system uses **Google ADK's agent framework** to decompose the task into **5 specialized AI agents**, each with its own role, tools, and instructions — demonstrating production-grade agent orchestration patterns.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User / Streamlit UI                       │
│              Upload Document → Get QnA.xlsx                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│          SequentialAgent: multilingual_qna_pipeline          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📄 Agent 1: document_parser                         │   │
│  │    Tools: [parse_document]                           │   │
│  │    → Extracts text from PDF/DOCX/TXT                │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🧠 Agent 2: qna_generator                          │   │
│  │    Tools: [get_document_text, save_qna_pairs]       │   │
│  │    → Generates English QnA pairs via Gemini LLM     │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🇮🇳 Agent 3: hindi_translator                       │   │
│  │    Tools: [get_english_qna, save_qna_pairs]         │   │
│  │    → Translates QnA to Hindi (हिन्दी)               │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 🇮🇳 Agent 4: marathi_translator                     │   │
│  │    Tools: [get_english_qna, save_qna_pairs]         │   │
│  │    → Translates QnA to Marathi (मराठी)              │   │
│  └────────────────────┬────────────────────────────────┘   │
│                       ▼                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ 📊 Agent 5: excel_compiler                          │   │
│  │    Tools: [compile_excel_report]                     │   │
│  │    → Creates styled 3-sheet Excel workbook          │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Agent Pipeline

| # | Agent | Role | Tools | Model |
|---|-------|------|-------|-------|
| 1 | `document_parser` | Extracts text from uploaded documents | `parse_document` | gemini-2.0-flash |
| 2 | `qna_generator` | Generates English QnA pairs from content | `get_document_text`, `save_qna_pairs` | gemini-2.0-flash |
| 3 | `hindi_translator` | Translates QnA pairs to Hindi | `get_english_qna`, `save_qna_pairs` | gemini-2.0-flash |
| 4 | `marathi_translator` | Translates QnA pairs to Marathi | `get_english_qna`, `save_qna_pairs` | gemini-2.0-flash |
| 5 | `excel_compiler` | Creates styled Excel output | `compile_excel_report` | gemini-2.0-flash |

### ADK Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| **`LlmAgent`** | All 5 agents with dedicated roles, instructions, and tools |
| **`SequentialAgent`** | Root pipeline orchestrator for deterministic flow |
| **Tool Calling** | 6 custom tools with proper docstrings and type hints |
| **`output_key`** | Each agent persists output for downstream agents |
| **`Runner` + `SessionService`** | Custom Streamlit integration via `InMemorySessionService` |
| **Prompt Engineering** | Structured instruction prompts in `prompts.py` |

---

## ✨ Features

- 📄 **Multi-format Support**: PDF, DOCX, and TXT document processing
- 🤖 **ADK Multi-Agent Architecture**: 5 specialized agents with tool calling
- 🌍 **Trilingual Output**: English, Hindi (हिन्दी), Marathi (मराठी)
- 📊 **Styled Excel Export**: Color-coded sheets, frozen headers, alternating rows
- 🎨 **Premium Streamlit UI**: Gradient headers, dark sidebar, progress tracking
- ⚡ **Gemini AI Powered**: Uses Google's latest Gemini models for generation and translation
- 🖥️ **CLI Runner**: Run the pipeline from command line without UI
- 🔧 **ADK Compatible**: Works with `adk run` and `adk web` commands

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Google API Key from [AI Studio](https://aistudio.google.com/apikey)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/devanshudhoble/adk-agent-Multilingual-Question-Answer-QnA-Generation.git
cd adk-agent-Multilingual-Question-Answer-QnA-Generation

# 2. Create virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure API key
# Copy .env.example to .env and add your Google API key
copy .env.example .env
# Edit .env and set: GOOGLE_API_KEY=your_key_here
```

---

## 📖 Usage

### Option 1: Streamlit UI (Recommended)

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser. Upload a document, configure settings, and click **Generate**.

### Option 2: CLI Runner

```bash
# Basic usage
python run_cli.py --file sample_files/sample.txt

# With options
python run_cli.py --file document.pdf --pairs 15 --output QnA.xlsx --model gemini-2.0-flash
```

### Option 3: ADK CLI

```bash
# Interactive terminal
adk run multilingual_qna

# ADK Web UI
adk web
```

---

## 📁 Project Structure

```
adk-agent-Multilingual-QnA/
├── .env                              # API key (gitignored)
├── .env.example                      # API key template
├── .gitignore                        # Git ignore rules
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
│
├── app.py                            # 🎨 Streamlit UI (Premium interface)
├── run_cli.py                        # 🖥️ CLI runner script
│
├── multilingual_qna/                 # 🤖 ADK Agent Package
│   ├── __init__.py                   # Package exports (root_agent)
│   ├── agent.py                      # Multi-agent pipeline definition
│   ├── prompts.py                    # Agent instruction prompts
│   └── tools/                        # ADK Tool Functions
│       ├── __init__.py               # Tool exports
│       ├── document_tools.py         # PDF/DOCX/TXT parsing tools
│       ├── qna_tools.py              # QnA state management tools
│       └── excel_tools.py            # Excel output generation tool
│
└── sample_files/                     # Test documents
    └── sample.txt                    # AI overview document
```

---

## 🛠 Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Agent Framework** | Google ADK (`google-adk`) | Multi-agent orchestration with `SequentialAgent`, `LlmAgent` |
| **AI Model** | Google Gemini 2.0 Flash | QnA generation and translation via tool-calling agents |
| **UI Framework** | Streamlit | Premium web interface with custom CSS |
| **PDF Parsing** | PyPDF2 | Extract text from PDF documents |
| **DOCX Parsing** | python-docx | Extract text from Word documents |
| **Excel Output** | openpyxl | Styled Excel workbook with 3 language sheets |
| **API Client** | google-genai | Google AI API client library |

---

## 📊 Output Format

### Excel File: `QnA.xlsx`

| Sheet | Language | Tab Color |
|-------|----------|-----------|
| Sheet 1 | English | 🔵 Deep Blue (#1F4E79) |
| Sheet 2 | Hindi (हिन्दी) | 🟠 Warm Orange (#C55A11) |
| Sheet 3 | Marathi (मराठी) | 🟢 Forest Green (#548235) |

Each sheet contains:

| Questions | Answers |
|-----------|---------|
| What is Artificial Intelligence? | Artificial Intelligence is a branch of computer science... |
| Who proposed the Turing Test? | Alan Turing proposed the Turing Test in 1950... |

### Styling Features:
- ✅ Color-coded sheet tabs
- ✅ Frozen header rows
- ✅ Alternating row colors for readability
- ✅ Professional fonts (Calibri)
- ✅ Proper column widths and text wrapping

---

## 📝 License

This project is developed as an assignment demonstration. Feel free to use and modify.

---

<div align="center">

**Built with ❤️ using Google ADK + Gemini AI**

</div>
