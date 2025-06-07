import os
import uuid
import base64
import logfire
import nest_asyncio
from datetime import datetime
from dotenv import load_dotenv


def configure_langfuse(service_name: str, send_to_logfire: bool = False):
    """
    Configure Langfuse tracing for OpenAI Agents.
    Reads LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST from env,
    sets OTEL exporter variables, and instruments OpenAI agents via logfire.
    """
    # Load environment variables from .env
    load_dotenv()

    # Apply nested asyncio patch
    nest_asyncio.apply()

    session_id = f"{service_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"

    # Read Langfuse credentials
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    host = os.getenv("LANGFUSE_HOST")
    if not all([public_key, secret_key, host]):
        print("Langfuse env vars missing; skipping Langfuse configuration.")
        return

    # Build basic auth header
    auth = base64.b64encode(f"{public_key}:{secret_key}".encode()).decode()
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{host}/api/public/otel"
    os.environ["OTEL_EXPORTER_OTLP_HEADERS"] = f"Authorization=Basic {auth}"

    # Configure and instrument
    logfire.configure(service_name=service_name, send_to_logfire=send_to_logfire)
    logfire.instrument_openai_agents()
    print(f"Langfuse configured for {service_name}")
