"""
MCP Server for TODO List Management
====================================
A simple Model Context Protocol server that manages todos in a CSV file.

Tools provided:
- add_todo: Add a new todo
- get_todos: List all todos (optionally filter by status)
- update_todo: Update an existing todo
- delete_todo: Delete a todo
"""

import pandas as pd
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent / "data"
CSV_FILE = DATA_DIR / "todos.csv"
VALID_STATUSES = {"not_started", "in_progress", "completed"}

# =============================================================================
# INITIALIZE MCP SERVER
# =============================================================================

mcp = FastMCP("Todo List Server")

# =============================================================================
# CSV HELPER FUNCTIONS
# =============================================================================


def load_dataframe() -> pd.DataFrame:
    """Read all todos from the CSV file and return as a DataFrame."""
    df = pd.read_csv(CSV_FILE)
    print(f"Loaded {len(df)} todos from CSV")
    return df


def save_dataframe(df: pd.DataFrame) -> None:
    """Write the DataFrame back to the CSV file."""
    df.to_csv(CSV_FILE, index=False)
    print(f"Wrote {len(df)} todos to CSV")


def validate_status(status: str) -> None:
    """Raise an error if the status is not valid."""
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: '{status}'. Must be one of: {VALID_STATUSES}")


# =============================================================================
# MCP TOOLS
# =============================================================================


@mcp.tool()
def add_todo(name: str) -> dict:
    """
    Add a new todo to the TODO list.

    Args:
        name: The name/description of the todo (cannot be empty)

    Returns:
        The newly created todo with its assigned ID
    """
    # Validate input
    if not name or not name.strip():
        raise ValueError("Todo name cannot be empty")

    name = name.strip()

    # Read existing todos
    df = load_dataframe()

    # Generate new todo ID
    new_id = int(df["id"].max() + 1) if len(df) > 0 else 1

    # Create new todo row
    new_row = pd.DataFrame([{
        "id": new_id,
        "name": name,
        "status": "not_started"
    }])

    # Add to DataFrame and save
    df = pd.concat([df, new_row], ignore_index=True)
    save_dataframe(df)

    print(f"Added todo {new_id}: '{name}'")
    return {"id": new_id, "name": name, "status": "not_started"}


@mcp.tool()
def get_todos(status: str | None = None) -> dict:
    """
    List all todos, optionally filtered by status.

    Args:
        status: Optional filter - one of "not_started", "in_progress", "completed"

    Returns:
        Dictionary with 'todos' list and 'count'
    """
    # Validate status if provided
    if status is not None:
        validate_status(status)

    # Read all todos
    df = load_dataframe()

    # Filter by status if provided
    if status:
        df = df[df["status"] == status]
        print(f"Filtered to {len(df)} todos with status '{status}'")

    todos = df.to_dict(orient="records")
    return {"todos": todos, "count": len(todos)}


@mcp.tool()
def update_todo(
    id: int,
    name: str | None = None,
    status: str | None = None
) -> dict:
    """
    Update an existing todo's name and/or status.

    Args:
        id: The ID of the todo to update
        name: New name for the todo (optional)
        status: New status - one of "not_started", "in_progress", "completed" (optional)

    Returns:
        The updated todo
    """
    # Validate inputs
    if name is not None and not name.strip():
        raise ValueError("Todo name cannot be empty")

    if status is not None:
        validate_status(status)

    # Read all todos
    df = load_dataframe()

    # Find the todo to update
    mask = df["id"] == id
    if not mask.any():
        raise ValueError(f"Todo with ID {id} not found")

    # Update fields if provided
    if name is not None:
        df.loc[mask, "name"] = name.strip()

    if status is not None:
        df.loc[mask, "status"] = status

    # Save changes
    save_dataframe(df)

    # Return the updated todo
    updated_todo = df[mask].to_dict(orient="records")[0]
    print(f"Updated todo {id}")
    return updated_todo


@mcp.tool()
def delete_todo(id: int) -> dict:
    """
    Delete a todo from the TODO list.

    Args:
        id: The ID of the todo to delete

    Returns:
        Confirmation with the deleted todo ID
    """
    # Read all todos
    df = load_dataframe()

    # Check if todo exists
    mask = df["id"] == id
    if not mask.any():
        raise ValueError(f"Todo with ID {id} not found")

    # Remove the todo
    df = df[~mask]

    # Save changes
    save_dataframe(df)

    print(f"Deleted todo {id}")
    return {"deleted": True, "id": id}


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    print("Starting Todo List MCP Server...")
    mcp.run()
