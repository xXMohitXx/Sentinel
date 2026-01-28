"""
Phylax Execution Context

Provides execution context management for grouping traces and tracking causality.

Design principles:
- No magic, no AST tricks, no thread hacking
- Uses Python's contextvars (thread-safe, async-safe)
- Optional usage - existing code works unchanged
"""

from contextvars import ContextVar
from uuid import uuid4
from contextlib import contextmanager
from typing import Optional, Generator


# Context variables for execution tracking
_execution_id: ContextVar[str] = ContextVar('phylax_execution_id')
_current_node_id: ContextVar[str] = ContextVar('phylax_current_node_id')
_node_stack: ContextVar[list] = ContextVar('phylax_node_stack', default=[])


@contextmanager
def execution() -> Generator[str, None, None]:
    """
    Create an execution context that groups traces.
    
    All traces created inside this context share the same execution_id.
    Parent-child relationships are tracked automatically.
    
    Usage:
        import phylax
        
        with phylax.execution() as exec_id:
            step_a()  # parent_node_id = None (root)
            step_b()  # parent_node_id = step_a.node_id
            
    Returns:
        The execution_id for this context
    """
    exec_id = str(uuid4())
    token = _execution_id.set(exec_id)
    stack_token = _node_stack.set([])
    
    try:
        yield exec_id
    finally:
        _execution_id.reset(token)
        _node_stack.reset(stack_token)


def get_execution_id() -> str:
    """
    Get the current execution_id.
    
    If no execution context exists, generates a new UUID.
    This ensures traces always have an execution_id.
    """
    try:
        return _execution_id.get()
    except LookupError:
        return str(uuid4())


def get_parent_node_id() -> Optional[str]:
    """
    Get the current node as parent for child calls.
    
    Returns None if:
    - No execution context exists
    - This is the first call in the context
    """
    try:
        stack = _node_stack.get()
        return stack[-1] if stack else None
    except LookupError:
        return None


def push_node(node_id: str) -> None:
    """
    Push a node onto the stack (called when entering a traced function).
    """
    try:
        stack = _node_stack.get()
        stack.append(node_id)
    except LookupError:
        # No context, no tracking needed
        pass


def pop_node() -> None:
    """
    Pop a node from the stack (called when exiting a traced function).
    """
    try:
        stack = _node_stack.get()
        if stack:
            stack.pop()
    except LookupError:
        pass


def in_execution_context() -> bool:
    """Check if we're inside an execution context."""
    try:
        _execution_id.get()
        return True
    except LookupError:
        return False
