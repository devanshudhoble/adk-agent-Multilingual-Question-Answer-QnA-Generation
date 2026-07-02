"""
CLI Runner for Multilingual QnA ADK Pipeline
==============================================
Standalone command-line interface for running the ADK multi-agent pipeline
without Streamlit.

Usage:
    python run_cli.py --file sample_files/sample.txt
    python run_cli.py --file document.pdf --pairs 15 --output QnA.xlsx
    python run_cli.py --file report.docx --model gemini-2.5-flash
"""

import argparse
import asyncio
import os
import sys
import time

from dotenv import load_dotenv


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Generate multilingual QnA pairs from a document using ADK agents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cli.py --file sample_files/sample.txt
  python run_cli.py --file report.pdf --pairs 15
  python run_cli.py --file paper.docx --model gemini-2.5-flash --output results.xlsx
        """,
    )
    parser.add_argument(
        "--file", "-f",
        required=True,
        help="Path to the input document (.pdf, .docx, or .txt)",
    )
    parser.add_argument(
        "--output", "-o",
        default="QnA.xlsx",
        help="Output Excel file path (default: QnA.xlsx)",
    )
    parser.add_argument(
        "--pairs", "-n",
        type=int,
        default=10,
        help="Number of QnA pairs to generate (default: 10)",
    )
    parser.add_argument(
        "--model", "-m",
        default="gemini-2.0-flash",
        help="Gemini model name (default: gemini-2.0-flash)",
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="Google API key (overrides .env file)",
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.file):
        print(f"❌ Error: File not found: {args.file}")
        sys.exit(1)

    ext = os.path.splitext(args.file)[1].lower()
    if ext not in (".pdf", ".docx", ".txt"):
        print(f"❌ Error: Unsupported format '{ext}'. Use .pdf, .docx, or .txt")
        sys.exit(1)

    # Load API key
    load_dotenv()
    api_key = args.api_key or os.environ.get("GOOGLE_API_KEY", "")
    model = args.model

    if api_key == "DEMO_MODE" or not api_key:
        print("⚠️ Running in Mock/Demo mode using ADK MockLlm...")
        api_key = "MOCK_KEY"
        model = "mock-model"

    os.environ["GOOGLE_API_KEY"] = api_key

    # Import ADK components
    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from google.genai import types
        from multilingual_qna.agent import create_pipeline
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip install google-adk PyPDF2 python-docx openpyxl python-dotenv")
        sys.exit(1)

    # Create pipeline
    file_path = os.path.abspath(args.file)
    output_path = os.path.abspath(args.output)

    print("\n" + "=" * 60)
    print("🌐 Multilingual QnA Generator — ADK Agent Pipeline")
    print("=" * 60)
    print(f"📄 Input:    {file_path}")
    print(f"📊 Pairs:    {args.pairs}")
    print(f"🤖 Model:    {model}")
    print(f"📁 Output:   {output_path}")
    print("=" * 60 + "\n")

    pipeline = create_pipeline(
        model=model,
        num_pairs=args.pairs,
        output_path=output_path,
    )

    session_service = InMemorySessionService()
    runner = Runner(
        agent=pipeline,
        app_name="multilingual_qna_cli",
        session_service=session_service,
    )

    user_message = f"Process the document at: {file_path}"

    async def run_pipeline():
        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=user_message)],
        )

        print("🚀 Starting ADK pipeline...\n")
        start_time = time.time()

        # Create session first
        await session_service.create_session(
            app_name="multilingual_qna_cli",
            user_id="cli_user",
            session_id="cli_session",
        )

        async for event in runner.run_async(
            user_id="cli_user",
            session_id="cli_session",
            new_message=content,
        ):
            # Print agent activity
            if hasattr(event, 'content') and event.content:
                author = getattr(event, 'author', 'system')
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if getattr(part, 'text', None) is not None:
                            text_preview = part.text[:200].replace('\n', ' ')
                            print(f"  🤖 [{author}]: {text_preview}...")
                        elif getattr(part, 'function_call', None) is not None:
                            fc = part.function_call
                            print(f"  🔧 [{author}] calling tool: {fc.name}")
                        elif getattr(part, 'function_response', None) is not None:
                            fr = part.function_response
                            print(f"  ✅ [{author}] tool response: {fr.name}")

        elapsed = time.time() - start_time
        print(f"\n{'=' * 60}")
        print(f"✅ Pipeline completed in {elapsed:.1f}s")
        print(f"📁 Output saved to: {output_path}")
        print(f"{'=' * 60}\n")

    # Run
    asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
