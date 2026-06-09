"""Verify Ollama is running and required models are available."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.llm.factory import check_ollama_health, get_chat_llm
from langchain_core.messages import HumanMessage


def main():
    health = check_ollama_health()
    print("Ollama health check")
    print(f"  Reachable: {health['ollama_reachable']}")
    print(f"  Installed models: {health['models']}")
    print(f"  Required: {health['required']}")

    if health["missing"]:
        print("\nMISSING models — pull them with:")
        for m in health["missing"]:
            print(f"  ollama pull {m}")
        sys.exit(1)

    print("\nWarming up chat model...")
    try:
        llm = get_chat_llm()
        r = llm.invoke([HumanMessage(content="Say OK")])
        print(f"  Chat model OK: {str(r.content)[:50]}")
    except Exception as e:
        print(f"  Chat model FAILED: {e}")
        sys.exit(1)

    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
