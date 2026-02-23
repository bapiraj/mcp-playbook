# Todo MCP Server

A Model Context Protocol server that manages todos in a CSV file using [FastMCP](https://github.com/jlowin/fastmcp).

## Tools

| Tool | Description |
|------|-------------|
| `add_todo` | Add a new todo (starts as `not_started`) |
| `get_todos` | List all todos, optionally filtered by status |
| `update_todo` | Update a todo's name and/or status |
| `delete_todo` | Delete a todo by ID |

**Statuses:** `not_started`, `in_progress`, `completed`

## Prerequisites

- Python 3.10+
- Dependencies: `mcp`, `pandas`

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
python server.py
```

## Project Structure

```
01-todo-mcp-server/
├── server.py          # MCP server with all tool definitions
├── requirements.txt   # Python dependencies
├── data/
│   └── todos.csv      # CSV file storing todos (id, name, status)
└── README.md
```

## Usage

Once running, connect to this server from any MCP client. The server exposes four tools for full CRUD operations on the todo list. All data is persisted to `data/todos.csv`.
