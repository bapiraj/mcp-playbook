# Job Platform Database MCP

A Model Context Protocol (MCP) server built on top of a SQLite database for a job recruiting platform. It exposes tools that allow an AI assistant (like Claude) to help job candidates search and apply for jobs, and help recruiters manage postings and applicants — all via natural language.

---

## What It Does

The server provides two roles:

- **Candidates** — search job postings, apply, track application status, and withdraw applications
- **Recruiters** — create and close job postings, view applicants, and update application statuses

All interactions are authenticated via a `login` tool that sets the current user session. Tools enforce role-based access and data ownership — candidates only see their own applications, recruiters only see their own postings.

---

## Project Structure

```
02-job-platform-database-mcp/
├── server.py               # MCP server — all tools defined here
├── requirements.txt        # Dependencies (just: fastmcp)
└── database/
    ├── schema.sql          # Table definitions
    ├── db_util.py          # SQLite connection and query helpers
    ├── db_setup.py         # Run once to initialize the database
    └── seed.py             # Optional: load sample data
```

---

## Local Setup

### Prerequisites

- Python 3.10+
- [Claude Desktop](https://claude.ai/download) (to connect the MCP server)

### 1. Clone and navigate

```bash
git clone <repo-url>
cd mcp-playbook/02-job-platform-database-mcp
```

### 2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS/Linux
# .venv\Scripts\activate       # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Initialize the database

```bash
python database/db_setup.py
```

This creates `database/job-platform.db` with empty tables, ready to use.

### 5. (Optional) Seed sample data

```bash
cd database
python seed.py
cd ..
```

This loads sample users and job postings so you can try the tools right away.

---

## Running the MCP Server

### Connect to Claude Desktop

Add the following to your Claude Desktop config file:

```json
{
  "mcpServers": {
    "jobs-platform-database": {
      "command": "/bin/bash",
      "args": [
        "-c",
        "cd /absolute/path/to/02-job-platform-database-mcp && .venv/bin/python server.py"
      ]
    }
  }
}
```

Replace `/absolute/path/to/02-job-platform-database-mcp` with the actual path on your machine, then restart Claude Desktop.

### Verify it's running

Open Claude Desktop and look for the hammer icon in the toolbar — this confirms the MCP tools are loaded. You can ask Claude:

> "What tools do you have available?"

---

## Available Tools

| Tool | Role | Description |
|---|---|---|
| `login` | Any | Log in as a user by username |
| `search_job_postings` | Any | Search open postings by keyword, location, or company |
| `get_job_posting_detail` | Any | Get full details on a specific posting |
| `apply_to_job` | Candidate | Apply to a job posting |
| `get_job_applications` | Candidate | List your applications, optionally filtered by status |
| `withdraw_application` | Candidate | Withdraw a submitted application |
| `create_job_posting` | Recruiter | Post a new job |
| `close_job_posting` | Recruiter | Close an existing posting |
| `get_job_postings` | Recruiter | List your postings with applicant counts |
| `get_applicants_for_job` | Recruiter | See who applied to one of your postings |
| `update_application_status` | Recruiter | Move an applicant through the hiring pipeline |

---

## Example Prompts to Try

**As a candidate** (after seeding, log in as e.g. `ravi.shankar`):
- "Log me in as ravi.shankar"
- "Search for engineering jobs in San Francisco"
- "Apply me to job posting 1"
- "Show me all my applications"
- "Withdraw my application with ID 2"

**As a recruiter** (log in as e.g. `sarah.jones`):
- "Log me in as sarah.jones"
- "Create a job posting for a Senior Backend Engineer at Acme Corp in Austin, TX"
- "Show me all my open job postings"
- "Who has applied to my job posting 1?"
- "Move application 3 to the interview stage"

---

## Tech Stack

- **Python** 3.10+
- **SQLite** — file-based, no database server needed
- **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server framework
