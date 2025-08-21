"""Diagnose AI Gateway/OpenAI connectivity and configuration.

This script attempts minimal model and embedding calls using the current
environment configuration and prints detailed diagnostics, including the
base_url used, required headers, and full error payloads.
"""

import os
import sys
import traceback
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings


def _normalize_openai_base_url(raw_url: Optional[str]) -> Optional[str]:
    """Normalize base URL to an OpenAI-compatible endpoint.

    Accepts values like:
    - https://ai-gateway.deere.com
    - https://ai-gateway.deere.com/openai
    - https://ai-gateway.deere.com/openai/v1

    Returns a URL ending with /openai/v1 (no trailing slash).
    """
    if not raw_url:
        return raw_url
    url = raw_url.rstrip("/")
    if url.endswith("/v1"):
        return url
    if url.endswith("/openai"):
        return f"{url}/v1"
    return f"{url}/openai/v1"


def _print_header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def diagnose_ai_gateway() -> None:
    # Import config lazily after dotenv so env is loaded
    from demo_agent.config import config
    from demo_agent.helpers import auth_helper

    print(f"USE_AI_GATEWAY={config.use_ai_gateway}")
    if config.use_ai_gateway:
        raw_base = config.ai_gateway.base_url
        norm_base = _normalize_openai_base_url(raw_base)
        print(f"AI_GATEWAY_BASE_URL (raw) = {raw_base}")
        print(f"AI_GATEWAY_BASE_URL (normalized) = {norm_base}")
        print(f"AI_GATEWAY_REGISTRATION_ID = {config.ai_gateway.registration_id}")

        _print_header("Obtaining OAuth access token")
        try:
            token = auth_helper.get_access_token(
                config.ai_gateway.issuer_url,
                config.ai_gateway.client_id,
                config.ai_gateway.client_secret,
            )
            if token:
                print("Token acquired (prefix):", token[:16] + "...")
            else:
                print("Failed to acquire token")
        except Exception as e:
            print("Token acquisition error:", repr(e))
            traceback.print_exc()
            return

        if not token:
            print("Cannot proceed without token.")
            return

        # Try model call with RAW base_url
        _print_header("ChatOpenAI call using RAW base_url")
        try:
            llm_raw = ChatOpenAI(
                model=config.ai_gateway.model,
                api_key=token,
                base_url=raw_base,
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
                },
                temperature=0.0,
            )
            print("Client base_url:", getattr(getattr(llm_raw, "client", None), "base_url", None))
            resp = llm_raw.invoke("Say 'pong' only.")
            print("RAW base_url response:", resp.content)
        except Exception as e:
            print("RAW base_url error:", repr(e))
            traceback.print_exc()

        # Try model call with NORMALIZED base_url
        _print_header("ChatOpenAI call using NORMALIZED base_url (/openai/v1)")
        try:
            llm_norm = ChatOpenAI(
                model=config.ai_gateway.model,
                api_key=token,
                base_url=norm_base,
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
                },
                temperature=0.0,
            )
            print("Client base_url:", getattr(getattr(llm_norm, "client", None), "base_url", None))
            resp = llm_norm.invoke("Say 'pong' only.")
            print("NORMALIZED base_url response:", resp.content)
        except Exception as e:
            print("NORMALIZED base_url error:", repr(e))
            traceback.print_exc()

        # Try listing models with NORMALIZED base_url
        _print_header("GET /models using NORMALIZED base_url")
        try:
            import requests

            url = f"{norm_base}/models"
            headers = {
                "Authorization": f"Bearer {token}",
                "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
            }
            print("Request:", url)
            r = requests.get(url, headers=headers, timeout=20)
            print("Status:", r.status_code)
            print("Body:", r.text[:1000])
        except Exception as e:
            print("Models list error:", repr(e))
            traceback.print_exc()

        # Try Responses API with NORMALIZED base_url
        _print_header("POST /responses using NORMALIZED base_url")
        try:
            import requests

            url = f"{norm_base}/responses"
            headers = {
                "Authorization": f"Bearer {token}",
                "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
                "Content-Type": "application/json",
            }
            payload = {
                "model": config.ai_gateway.model,
                "input": "Say 'pong' only.",
            }
            print("Request:", url)
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            print("Status:", r.status_code)
            print("Body:", r.text[:1000])
        except Exception as e:
            print("Responses API error:", repr(e))
            traceback.print_exc()

        # Try embeddings with NORMALIZED base_url
        _print_header("OpenAIEmbeddings using NORMALIZED base_url")
        try:
            embed = OpenAIEmbeddings(
                model="text-embedding-3-large",
                api_key=token,
                base_url=norm_base,
                default_headers={
                    "deere-ai-gateway-registration-id": config.ai_gateway.registration_id or "",
                },
            )
            vec = embed.embed_query("test")
            print("Embedding length:", len(vec))
        except Exception as e:
            print("Embeddings error:", repr(e))
            traceback.print_exc()

    else:
        _print_header("Direct OpenAI call (USE_AI_GATEWAY=False)")
        from demo_agent.config import config as cfg
        if not cfg.openai.api_key:
            print("OPENAI_API_KEY not set; skipping direct test")
            return
        try:
            llm = ChatOpenAI(model=cfg.openai.model, api_key=cfg.openai.api_key)
            resp = llm.invoke("Say 'pong' only.")
            print("OpenAI response:", resp.content)
        except Exception as e:
            print("OpenAI direct error:", repr(e))
            traceback.print_exc()


if __name__ == "__main__":
    # Ensure repo src is importable when run directly
    here = os.path.abspath(os.path.dirname(__file__))
    repo_src = os.path.abspath(os.path.join(here, "..", ".."))
    if repo_src not in sys.path:
        sys.path.insert(0, repo_src)

    load_dotenv()
    diagnose_ai_gateway()


