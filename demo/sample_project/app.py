"""Sample AI application for ScanLLM demo scanning."""
import openai
from anthropic import Anthropic
from langchain_openai import ChatOpenAI


# LLM01: Prompt injection risk — user input in f-string
def chat(user_input: str):
    client = openai.OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": f"Help with: {user_input}"}],
        # LLM10: Missing max_tokens
    )
    return response.choices[0].message.content


# LLM06: Excessive agency
def run_agent():
    from crewai import Agent, Task, Crew
    agent = Agent(
        role="assistant",
        tools=[],  # Would flag if tools list is broad
        llm=ChatOpenAI(model="gpt-4o-mini"),
    )
    return agent


# LLM02: Hardcoded key (example - not a real key)
OPENAI_API_KEY = "sk-fake-demo-key-not-real-12345"
