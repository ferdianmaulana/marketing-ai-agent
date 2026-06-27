import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from agent.tools import ALL_TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are a Marketing Analytics AI Agent for a travel tech company.
You have access to YouTube channel performance data stored in a database.

Your job is to help marketing and performance teams by:
- Analyzing channel and video performance metrics
- Identifying top-performing and underperforming content
- Comparing channels against competitors
- Providing actionable optimization recommendations

When answering:
1. Always use the available tools to fetch real data before drawing conclusions
2. Reference specific numbers from the data in your response
3. End every response with 1-3 concrete, actionable recommendations
4. Be concise but insightful — you are talking to a marketing professional

Available metrics: subscriber count, view count, like count, comment count,
engagement rate ((likes + comments) / views * 100), video duration, publish date.
"""


def build_agent() -> AgentExecutor:
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.3,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, ALL_TOOLS, prompt)

    return AgentExecutor(
        agent=agent,
        tools=ALL_TOOLS,
        verbose=True,          # shows tool calls in terminal — good for demo
        max_iterations=5,      # prevent infinite loops
        handle_parsing_errors=True,
    )


# Singleton — build once, reuse across requests
_agent_executor: AgentExecutor = None


def get_agent() -> AgentExecutor:
    global _agent_executor
    if _agent_executor is None:
        _agent_executor = build_agent()
    return _agent_executor


def run_agent(question: str, chat_history: list = None) -> dict:
    agent = get_agent()

    # Convert chat history to LangChain message format
    history = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))

    result = agent.invoke({
        "input": question,
        "chat_history": history,
    })

    return {
        "answer": result["output"],
        "tools_used": [
            action.tool
            for action in result.get("intermediate_steps", [])
            if hasattr(action, "tool")
        ] if result.get("intermediate_steps") else [],
    }


if __name__ == "__main__":
    # Quick test — run directly: python -m agent.agent
    print("Testing agent...")
    response = run_agent("What channels are being tracked?")
    print("\nAnswer:", response["answer"])
