"""
Simple in-memory session store.
In production swap this for a Redis/Supabase-backed store.
"""

from typing import Dict, Any
import threading

_lock = threading.Lock()
_store: Dict[str, Dict[str, Any]] = {}


def set_session(session_id: str, data: Dict[str, Any]):
    with _lock:
        _store[session_id] = data


def get_session(session_id: str) -> Dict[str, Any]:
    with _lock:
        session = _store.get(session_id)
    if not session:
        raise KeyError(f"Session '{session_id}' not found. Please process a video or PDF first.")
    return session


def update_session(session_id: str, **kwargs):
    with _lock:
        if session_id not in _store:
            _store[session_id] = {}
        _store[session_id].update(kwargs)


def list_sessions():
    with _lock:
        return list(_store.keys())
