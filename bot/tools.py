TOOLS = [
    {
        "name": "read_memories",
        "description": (
            "Read all saved core memories/facts about this user. Use this when the "
            "conversation touches on something that might have been stored — their "
            "hospital, OB name, due date, preferences, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "save_memory",
        "description": (
            "Save an important fact about this user for future reference. Use this "
            "when they share key details like their hospital, OB name, due date, "
            "birth preferences, medical conditions, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "Short label for the fact, e.g. 'hospital', 'ob_name', 'due_date'",
                },
                "value": {
                    "type": "string",
                    "description": "The fact to remember",
                },
            },
            "required": ["key", "value"],
        },
    },
    {
        "name": "delete_memory",
        "description": "Delete a previously saved memory/fact that is no longer accurate.",
        "input_schema": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string",
                    "description": "The label of the memory to delete",
                },
            },
            "required": ["key"],
        },
    },
    {
        "name": "list_documents",
        "description": (
            "List all documents this user has uploaded (birth plan, test results, etc). "
            "Use this to check what's available before reading a specific document."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "read_document",
        "description": (
            "Read the contents of an uploaded document. Use this when the user asks "
            "about their birth plan, uploaded notes, or when you need to reference "
            "something they've shared as a file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Name of the document to read",
                },
            },
            "required": ["filename"],
        },
    },
    {
        "name": "web_search",
        "description": (
            "Search the internet for current medical/pregnancy information. Use this "
            "when you need to verify a fact, look up recent guidelines, or find "
            "specific stats you're not confident about. Prefer this over guessing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query, e.g. 'third trimester back pain normal percentage'",
                },
            },
            "required": ["query"],
        },
    },
]
