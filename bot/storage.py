import json
import logging
import secrets
from pathlib import Path

log = logging.getLogger(__name__)

DATA_DIR = Path("/usr/src/app/data")
FAMILIES_DIR = DATA_DIR / "families"
USERS_DIR = DATA_DIR / "users"
PENDING_LINKS: dict[str, str] = {}  # code -> user_id


def _user_dir(user_id: str) -> Path:
    d = USERS_DIR / user_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def _user_meta_path(user_id: str) -> Path:
    return _user_dir(user_id) / "meta.json"


def _get_user_meta(user_id: str) -> dict:
    path = _user_meta_path(user_id)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def _save_user_meta(user_id: str, meta: dict) -> None:
    _user_meta_path(user_id).write_text(json.dumps(meta, indent=2))


# --- Family (shared storage between partners) ---


def get_family_id(user_id: str) -> str:
    """Get family ID for a user, creating one if needed."""
    meta = _get_user_meta(user_id)
    if "family_id" in meta:
        return meta["family_id"]
    # Create a new family for this user
    family_id = user_id
    meta["family_id"] = family_id
    _save_user_meta(user_id, meta)
    return family_id


def _family_dir(user_id: str) -> Path:
    family_id = get_family_id(user_id)
    d = FAMILIES_DIR / family_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_link_code(user_id: str) -> str:
    """Generate a 6-char code for partner linking."""
    # Ensure this user has a family
    get_family_id(user_id)
    code = secrets.token_hex(3).upper()  # 6 hex chars
    PENDING_LINKS[code] = user_id
    return code


def link_partner(code: str, partner_id: str) -> str:
    """Link a partner using a code."""
    if code not in PENDING_LINKS:
        return "Invalid or expired code. Ask your partner to send /link again."

    original_user_id = PENDING_LINKS.pop(code)

    if original_user_id == partner_id:
        return "You can't link with yourself!"

    # Get the original user's family
    family_id = get_family_id(original_user_id)

    # Point the partner to the same family
    meta = _get_user_meta(partner_id)
    meta["family_id"] = family_id
    meta["partner_id"] = original_user_id
    _save_user_meta(partner_id, meta)

    # Update original user's meta too
    orig_meta = _get_user_meta(original_user_id)
    orig_meta["partner_id"] = partner_id
    _save_user_meta(original_user_id, orig_meta)

    return "Linked! You now share memories and documents with your partner."


def get_partner_id(user_id: str) -> str | None:
    meta = _get_user_meta(user_id)
    return meta.get("partner_id")


# --- Memories (shared per family) ---


def _memories_path(user_id: str) -> Path:
    return _family_dir(user_id) / "memories.json"


def load_memories(user_id: str) -> dict[str, str]:
    path = _memories_path(user_id)
    if path.exists():
        return json.loads(path.read_text())
    return {}


def save_memory(user_id: str, key: str, value: str) -> str:
    memories = load_memories(user_id)
    memories[key.lower().strip()] = value
    _memories_path(user_id).write_text(json.dumps(memories, indent=2))
    return f"Saved: {key} = {value}"


def delete_memory(user_id: str, key: str) -> str:
    memories = load_memories(user_id)
    key = key.lower().strip()
    if key in memories:
        del memories[key]
        _memories_path(user_id).write_text(json.dumps(memories, indent=2))
        return f"Forgot: {key}"
    return f"No memory found for: {key}"


# --- Documents (shared per family) ---


def _docs_dir(user_id: str) -> Path:
    d = _family_dir(user_id) / "documents"
    d.mkdir(parents=True, exist_ok=True)
    return d


def save_document(user_id: str, filename: str, content: bytes) -> str:
    path = _docs_dir(user_id) / filename
    path.write_bytes(content)
    return f"Saved document: {filename}"


def list_documents(user_id: str) -> list[str]:
    return [f.name for f in _docs_dir(user_id).iterdir() if f.is_file()]


def read_document(user_id: str, filename: str) -> str:
    path = _docs_dir(user_id) / filename
    if not path.exists():
        return f"Document not found: {filename}"
    try:
        return path.read_text()
    except UnicodeDecodeError:
        return f"Cannot read binary file: {filename}. Only text documents are supported."


# --- Conversation history (per user, NOT shared) ---


def _history_path(user_id: str) -> Path:
    return _user_dir(user_id) / "history.json"


def load_history(user_id: str) -> list[dict]:
    path = _history_path(user_id)
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_history(user_id: str, history: list[dict]) -> None:
    _history_path(user_id).write_text(json.dumps(history))
