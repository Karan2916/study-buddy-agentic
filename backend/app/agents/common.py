from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import get_llm


def ask_agent(
    system_prompt: str, user_prompt: str, *, temperature: float | None = None
) -> str:
    llm = get_llm()
    if temperature is not None:
        llm = llm.bind(temperature=temperature)
    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    if not isinstance(response.content, str):
        raise RuntimeError("The configured model returned an unsupported response format.")
    return response.content.strip()


def invoke_structured(schema: Any, system_prompt: str, user_prompt: str) -> Any:
    llm = get_llm().with_structured_output(schema)
    return llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
