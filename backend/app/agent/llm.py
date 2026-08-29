import contextvars
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Generator

from langchain_groq import ChatGroq

from app.agent.schemas import CodeChangePlan
from app.config import settings


# Tracks LLM token usage across calls made inside a `track_tokens` block.
# The counter is a mutable object on purpose: LangGraph runs each node in
# a copied context, so reassigning a ContextVar inside a node would be
# invisible to the caller. Mutating a shared object's attribute is not.
class _TokenCounter:
    def __init__(self) -> None:
        self.total = 0


_token_counter: contextvars.ContextVar[_TokenCounter | None] = contextvars.ContextVar(
    "agent_token_counter",
    default=None,
)


@dataclass
class TokenUsage:
    """Mutable accumulator for LLM token usage."""

    total: int = field(default=0)


@contextmanager
def track_tokens(usage: TokenUsage) -> Generator[None, None, None]:
    """
    Accumulate the tokens consumed by all LLM calls in this block.

    Usage:
        usage = TokenUsage()
        with track_tokens(usage):
            graph.invoke(state)
        print(usage.total)
    """

    token = _token_counter.set(_TokenCounter())

    try:
        yield
    finally:
        counter = _token_counter.get()

        if counter is not None:
            usage.total = counter.total

        _token_counter.reset(token)


def _record_usage(response) -> None:
    """Add the response's token count to the current tracking context."""

    metadata = getattr(response, "usage_metadata", None)

    if not metadata:
        return

    total = metadata.get("total_tokens", 0)

    if total:
        counter = _token_counter.get()

        if counter is not None:
            counter.total += int(total)


def create_llm() -> ChatGroq:
    """
    Create the Groq chat model used by the coding agent.
    """

    return ChatGroq(
        model=settings.groq_model, temperature=0, api_key=settings.groq_api_key
    )


def ask_llm(prompt: str) -> str:
    """
    Send a prompt to the LLM and return its text response.
    """

    llm = create_llm()

    response = llm.invoke(prompt)

    _record_usage(response)

    return response.content


def create_structured_llm():
    """
    Create an LLM configured to return structured code changes.
    """

    llm = create_llm()

    return llm.with_structured_output(CodeChangePlan)


def generate_code_change_plan(
    prompt: str,
    max_retries: int = 3,
) -> CodeChangePlan:
    """
    Ask the LLM for a validated code change plan.

    Structured-output calls occasionally fail (the model answers with
    prose instead of calling the tool, or returns a plan that does not
    match the schema). Retry with an explicit instruction instead of
    crashing the whole run.
    """

    llm = create_structured_llm()

    retry_hint = (
        "\n\nIMPORTANT: You MUST call the CodeChangePlan tool with a valid "
        "JSON plan. Do not answer with prose or a markdown plan instead of "
        "the tool call. Only include files that actually need changes; "
        "never include a file with empty content."
    )

    last_error: Exception | None = None

    for attempt in range(max_retries):
        if attempt > 0:
            prompt = f"{prompt}{retry_hint}"

        try:
            response = llm.invoke(prompt)

            _record_usage(response)

            return response
        except Exception as exc:  # noqa: BLE001 - retry on any provider error
            last_error = exc

    if last_error is not None:
        raise last_error

    raise RuntimeError("generate_code_change_plan failed without an error")
