from langchain_groq import ChatGroq

from app.config import settings

def create_llm() -> ChatGroq:
    """
    Create the Groq chat model used by the coding agent.
    """

    return ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0,
        api_key=settings.groq_api_key
    )

def ask_llm(prompt: str) -> str:
    """
    Send a prompt to the LLM and return its text response.
    """

    llm = create_llm()

    response = llm.invoke(prompt)

    return response.content

