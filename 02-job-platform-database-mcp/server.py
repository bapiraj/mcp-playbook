from fastmcp import FastMCP
from database.db_util import query, query_one, execute

mcp = FastMCP("Recruiting Platform")

# The currently logged-in user. Set by the login tool.
current_user = None

# Valid application statuses
APPLICATION_STATUSES = ("applied", "screening", "interview", "decision_pending", "offer", "rejected", "withdrawn")


def require_candidate():
    """Check that a candidate is logged in. Returns an error dict or None."""
    if not current_user:
        return {"error": "Not logged in. Please log in first."}
    if current_user["role"] != "candidate":
        return {"error": "Only candidates can perform this action."}
    return None


def require_recruiter():
    """Check that a recruiter is logged in. Returns an error dict or None."""
    if not current_user:
        return {"error": "Not logged in. Please log in first."}
    if current_user["role"] != "recruiter":
        return {"error": "Only recruiters can perform this action."}
    return None


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@mcp.tool()
def login(user_name: str) -> dict:
    """Log in as an existing user.

    Args:
        user_name: The unique username of the person logging in.

    Returns a welcome message with the user's full name and role.
    """
    user = query_one("SELECT * FROM users WHERE user_name = ?", (user_name,))
    if not user:
        return {"error": f"No user found with username '{user_name}'."}

    global current_user
    current_user = user
    return {
        "message": f"Welcome, {user['first_name']} {user['last_name']}!",
        "role": user["role"]
    }


# ---------------------------------------------------------------------------
# Shared Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def search_job_postings(keyword: str = None, location: str = None, company: str = None) -> dict:
    """Search open job postings. No login required.

    Args:
        keyword: Optional. Matches against job title and description (partial match).
        location: Optional. Matches against location (partial match).
        company: Optional. Matches against company name (exact match).
    """
    sql = """
        SELECT id, title, company, location, created_at
        FROM job_postings
        WHERE status = 'open'
    """
    params = []

    if keyword:
        sql += " AND (title LIKE ? OR description LIKE ?)"
        params.extend([f"%{keyword}%", f"%{keyword}%"])
    if location:
        sql += " AND location LIKE ?"
        params.append(f"%{location}%")
    if company:
        sql += " AND company = ?"
        params.append(company)

    sql += " ORDER BY created_at DESC"

    results = query(sql, params)
    if not results:
        return {"results": [], "message": "No open job postings found matching your search."}
    return {"results": results}


@mcp.tool()
def get_job_posting_detail(job_posting_id: int) -> dict:
    """Get full details of a job posting. No login required — job postings are public.

    Args:
        job_posting_id: The ID of the job posting to retrieve.
    """
    posting = query_one(
        "SELECT * FROM job_postings WHERE id = ?",
        (job_posting_id,)
    )
    if not posting:
        return {"error": f"No job posting found with ID {job_posting_id}."}
    return posting

@mcp.tool()
def apply_to_job(job_posting_id: int) -> dict:
    """Apply to a job posting as the currently logged-in candidate.
    The candidate's resume URL from their profile is automatically attached.

    Args:
        job_posting_id: The ID of the job posting to apply to.
    """
    err = require_candidate()
    if err:
        return err

    posting = query_one("SELECT * FROM job_postings WHERE id = ?", (job_posting_id,))
    if not posting:
        return {"error": f"No job posting found with ID {job_posting_id}."}
    if posting["status"] == "closed":
        return {"error": "This job posting is closed and no longer accepting applications."}

    existing = query_one(
        "SELECT id FROM job_applications WHERE job_posting_id = ? AND candidate_id = ?",
        (job_posting_id, current_user["id"])
    )
    if existing:
        return {"error": "You have already applied to this job."}
    
    if not current_user["resume_url"]:
        return {"error": "You have no resume on file. Please add a resume URL to your profile before applying."}

    execute(
        """
        INSERT INTO job_applications (job_posting_id, candidate_id, resume_url, status)
        VALUES (?, ?, ?, 'applied')
        """,
        (job_posting_id, current_user["id"], current_user["resume_url"])
    )
    return {"message": f"Successfully applied to '{posting['title']}' at {posting['company']}."}


@mcp.tool()
def get_job_applications(status: str = None) -> dict:
    """Get job applications for the currently logged-in candidate.

    Args:
        status: Optional filter — one of 'applied', 'screening', 'interview',
                'decision_pending', 'offer', 'rejected', 'withdrawn'. If omitted, returns all applications.
    """
    err = require_candidate()
    if err:
        return err
    if status and status not in APPLICATION_STATUSES:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(APPLICATION_STATUSES)}."}

    sql = """
        SELECT ja.id, jp.title, jp.company, jp.location, ja.status, ja.applied_at
        FROM job_applications ja
        JOIN job_postings jp ON ja.job_posting_id = jp.id
        WHERE ja.candidate_id = ?
    """
    params = [current_user["id"]]

    if status:
        sql += " AND ja.status = ?"
        params.append(status)

    sql += " ORDER BY ja.applied_at DESC"

    applications = query(sql, params)

    if not applications:
        return {"results": [], "message": "No applications found."}
    return {"results": applications}




@mcp.tool()
def withdraw_application(application_id: int) -> dict:
    """Withdraw a job application as the currently logged-in candidate.

    Args:
        application_id: The ID of the application to withdraw.
    """
    err = require_candidate()
    if err:
        return err

    application = query_one(
        "SELECT * FROM job_applications WHERE id = ?",
        (application_id,)
    )
    if not application:
        return {"error": f"No application found with ID {application_id}."}
    if application["candidate_id"] != current_user["id"]:
        return {"error": "Access denied. This application does not belong to you."}
    if application["status"] == "withdrawn":
        return {"error": "This application has already been withdrawn."}

    execute(
        "UPDATE job_applications SET status = 'withdrawn', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (application_id,)
    )
    return {"message": "Application successfully withdrawn."}


# ---------------------------------------------------------------------------
# Recruiter Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def create_job_posting(title: str, company: str, location: str, description: str) -> dict:
    """Create a new job posting as the currently logged-in recruiter.
    The posting is always created with status 'open'.

    Args:
        title: Job title (e.g. 'Senior Software Engineer').
        company: Company name.
        location: Job location (e.g. 'Bengaluru', 'Remote').
        description: Full job description.
    """
    err = require_recruiter()
    if err:
        return err

    new_id = execute(
        """
        INSERT INTO job_postings (recruiter_id, title, company, location, description, status)
        VALUES (?, ?, ?, ?, ?, 'open')
        """,
        (current_user["id"], title, company, location, description)
    )

    posting = query_one("SELECT * FROM job_postings WHERE id = ?", (new_id,))
    return posting


@mcp.tool()
def close_job_posting(job_posting_id: int) -> dict:
    """Close a job posting as the currently logged-in recruiter.

    Args:
        job_posting_id: The ID of the job posting to close.
    """
    err = require_recruiter()
    if err:
        return err

    posting = query_one("SELECT * FROM job_postings WHERE id = ?", (job_posting_id,))
    if not posting:
        return {"error": f"No job posting found with ID {job_posting_id}."}
    if posting["recruiter_id"] != current_user["id"]:
        return {"error": "Access denied. This job posting does not belong to you."}
    if posting["status"] == "closed":
        return {"error": "This job posting is already closed."}

    execute(
        "UPDATE job_postings SET status = 'closed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (job_posting_id,)
    )
    return {"message": f"Job posting '{posting['title']}' has been closed."}

@mcp.tool()
def get_job_postings(status: str = None) -> dict:
    """Get all job postings by the currently logged-in recruiter.

    Args:
        status: Optional filter — 'open' or 'closed'.
    """
    err = require_recruiter()
    if err:
        return err

    if status and status not in ("open", "closed"):
        return {"error": "Invalid status. Must be 'open' or 'closed'."}

    sql = """
        SELECT jp.id, jp.title, jp.status, jp.created_at,
               COUNT(ja.id) as applicant_count
        FROM job_postings jp
        LEFT JOIN job_applications ja ON jp.id = ja.job_posting_id
        WHERE jp.recruiter_id = ?
    """
    params = [current_user["id"]]

    if status:
        sql += " AND jp.status = ?"
        params.append(status)

    sql += " GROUP BY jp.id ORDER BY jp.created_at DESC"

    postings = query(sql, params)

    if not postings:
        return {"results": [], "message": "No job postings found."}
    return {"results": postings}

@mcp.tool()
def get_applicants_for_job(job_posting_id: int, status: str = None) -> dict:
    """Get applicants for a job posting as the currently logged-in recruiter.

    Args:
        job_posting_id: The ID of the job posting.
        status: Optional filter — one of 'applied', 'screening', 'interview',
                'decision_pending', 'offer', 'rejected', 'withdrawn'.
    """
    err = require_recruiter()
    if err:
        return err

    posting = query_one("SELECT * FROM job_postings WHERE id = ?", (job_posting_id,))
    if not posting:
        return {"error": f"No job posting found with ID {job_posting_id}."}
    if posting["recruiter_id"] != current_user["id"]:
        return {"error": "Access denied. This job posting does not belong to you."}

    if status and status not in APPLICATION_STATUSES:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(APPLICATION_STATUSES)}."}

    sql = """
        SELECT u.first_name, u.last_name, u.email, ja.resume_url, ja.status, ja.applied_at
        FROM job_applications ja
        JOIN users u ON ja.candidate_id = u.id
        WHERE ja.job_posting_id = ?
    """
    params = [job_posting_id]

    if status:
        sql += " AND ja.status = ?"
        params.append(status)

    sql += " ORDER BY ja.applied_at DESC"

    applicants = query(sql, params)

    if not applicants:
        return {"results": [], "message": "No applicants found for this job posting."}
    return {"results": applicants}


@mcp.tool()
def update_application_status(application_id: int, status: str) -> dict:
    """Update the status of a job application as the currently logged-in recruiter.

    Args:
        application_id: The ID of the application to update.
        status: New status — one of 'screening', 'interview', 'decision_pending', 'offer', 'rejected'.
    """
    err = require_recruiter()
    if err:
        return err

    recruiter_statuses = ("screening", "interview", "decision_pending", "offer", "rejected")
    if status not in recruiter_statuses:
        return {"error": f"Invalid status '{status}'. Must be one of: {', '.join(recruiter_statuses)}."}

    application = query_one(
        """
        SELECT ja.*, jp.recruiter_id
        FROM job_applications ja
        JOIN job_postings jp ON ja.job_posting_id = jp.id
        WHERE ja.id = ?
        """,
        (application_id,)
    )
    if not application:
        return {"error": f"No application found with ID {application_id}."}
    if application["recruiter_id"] != current_user["id"]:
        return {"error": "Access denied. This application is not for one of your job postings."}

    execute(
        "UPDATE job_applications SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, application_id)
    )
    return {"message": f"Application status updated to '{status}'."}


if __name__ == "__main__":
    mcp.run()
