import json
import logging

import anthropic

from bot.prompt import SYSTEM_PROMPT
from bot.storage import (
    delete_memory,
    list_documents,
    load_history,
    load_memories,
    read_document,
    save_history,
    save_memory,
)
from bot.search import web_search
from bot.tools import TOOLS

log = logging.getLogger(__name__)

MAX_HISTORY = 50  # keep last N message pairs
MAX_TOOL_ROUNDS = 5


def _serialize_content(content) -> list[dict] | str:
    """Convert Anthropic SDK content blocks to JSON-serializable dicts."""
    if isinstance(content, str):
        return content
    return [block.to_dict() if hasattr(block, "to_dict") else block for block in content]


async def _execute_tool(user_id: str, name: str, input: dict) -> str:
    match name:
        case "read_memories":
            memories = load_memories(user_id)
            if not memories:
                return "No memories saved yet."
            return json.dumps(memories, indent=2)
        case "save_memory":
            return save_memory(user_id, input["key"], input["value"])
        case "delete_memory":
            return delete_memory(user_id, input["key"])
        case "list_documents":
            docs = list_documents(user_id)
            if not docs:
                return "No documents uploaded yet."
            return "\n".join(docs)
        case "read_document":
            return read_document(user_id, input["filename"])
        case "web_search":
            return await web_search(input["query"])
        case _:
            return f"Unknown tool: {name}"


async def respond(user_id: str, message: str) -> str:
    client = anthropic.AsyncAnthropic()
    history = load_history(user_id)

    history.append({"role": "user", "content": message})

    # Trim to keep context manageable
    if len(history) > MAX_HISTORY * 2:
        history = history[-(MAX_HISTORY * 2) :]

    # Agentic loop: let Claude call tools until it produces a text response
    for _ in range(MAX_TOOL_ROUNDS):
        response = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
            tools=TOOLS,
        )

        if response.stop_reason == "tool_use":
            # Append assistant's response (contains tool_use blocks)
            history.append({"role": "assistant", "content": _serialize_content(response.content)})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    log.info("Tool call: %s(%s)", block.name, json.dumps(block.input))
                    result = await _execute_tool(user_id, block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )

            history.append({"role": "user", "content": tool_results})
            continue

        # Done — extract text response
        assistant_text = ""
        for block in response.content:
            if hasattr(block, "text"):
                assistant_text += block.text

        history.append({"role": "assistant", "content": assistant_text})
        save_history(user_id, history)
        return assistant_text

    # Fallback if we hit max rounds
    return "Sorry, I got a bit lost in thought there. Can you try again?"
