r"""Standalone connectivity check for the configured OpenAI-compatible deployment.

Run from the project root with:
    .\backend\venv\Scripts\python.exe .\backend\tests\test_api_connectivity.py
"""

import sys
from pathlib import Path

from dotenv import dotenv_values
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    OpenAI,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
REQUIRED_SETTINGS = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL")
PROMPT = "Explain DBMS in two sentences."


def redact(text: str, secret: str) -> str:
    return text.replace(secret, "[REDACTED]") if secret else text


def report_status(statuses: dict[str, bool]) -> None:
    print(f"Project .env found: {'yes' if ENV_FILE.is_file() else 'no'}")
    for name in REQUIRED_SETTINGS:
        print(f"{name} loaded and non-empty: {'yes' if statuses.get(name) else 'no'}")


def main() -> int:
    if not ENV_FILE.is_file():
        report_status({})
        print(f"Configuration error: project-root .env was not found at {PROJECT_ROOT}.")
        return 2

    file_values = dotenv_values(ENV_FILE)
    config = {
        name: str(file_values.get(name) or "").strip()
        for name in REQUIRED_SETTINGS
    }
    statuses = {name: bool(config.get(name)) for name in REQUIRED_SETTINGS}
    report_status(statuses)

    missing = [name for name, present in statuses.items() if not present]
    if missing:
        print("Configuration error: fill the missing setting(s) in the project-root .env.")
        return 2

    api_key = config["OPENAI_API_KEY"]
    client = OpenAI(
        api_key=api_key,
        base_url=config["OPENAI_BASE_URL"],
        timeout=30.0,
        max_retries=0,
    )
    try:
        response = client.responses.create(
            model=config["OPENAI_MODEL"],
            input=PROMPT,
        )
        answer = redact(response.output_text or "", api_key)
        if not answer:
            print("Request succeeded, but the Responses API returned no text output.")
            return 1
        print("Request succeeded.")
        print("API response:")
        print(answer)
        return 0
    except AuthenticationError as exc:
        print(f"Authentication error: {redact(str(exc), api_key)}")
    except APITimeoutError as exc:
        print(f"Request timed out: {redact(str(exc), api_key)}")
    except NotFoundError as exc:
        message = redact(str(exc), api_key)
        error_text = message.casefold()
        if "deployment" in error_text or "model" in error_text:
            print(f"Deployment error (HTTP 404): {message}")
        else:
            print(f"Invalid endpoint or resource path (HTTP 404): {message}")
    except BadRequestError as exc:
        message = redact(str(exc), api_key)
        error_text = message.casefold()
        if "deployment" in error_text or "model" in error_text:
            print(f"Deployment error (HTTP 400): {message}")
        else:
            print(f"Invalid request (HTTP 400): {message}")
    except APIConnectionError as exc:
        print(f"Connection failure: {redact(str(exc), api_key)}")
    except APIStatusError as exc:
        message = redact(str(exc), api_key)
        if exc.status_code in (400, 404) and (
            "deployment" in message.casefold() or "model" in message.casefold()
        ):
            print(f"Deployment error (HTTP {exc.status_code}): {message}")
        elif exc.status_code in (404, 405):
            print(f"Invalid endpoint or resource path (HTTP {exc.status_code}): {message}")
        else:
            print(f"API request failed (HTTP {exc.status_code}): {message}")
    except Exception as exc:
        print(f"Unexpected connectivity-test failure: {redact(str(exc), api_key)}")
    finally:
        client.close()
    print("Request failed.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
