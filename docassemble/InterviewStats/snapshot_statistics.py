from docassemble.base.util import variables_snapshot_connection, interview_menu
from typing import List

__all__ = ['get_filenames', 'get_summary_stats', 'get_stats', 'get_columns', 'get_column_values', 'get_combined_filename_list', "get_overall_stats", "get_summary_stats_by_filename", 'shorten_filename']

def get_filenames():
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = "SELECT DISTINCT(filename) AS filename FROM jsonstorage WHERE tags IS DISTINCT FROM 'metadata'"
        cur.execute(query)
        results = [record for record in cur]
    conn.close()
    return results


def get_combined_filename_list():
    json_filenames = get_filenames()
    interview_filenames = interview_menu()
    combined_interviews = []
    for json_interview in json_filenames:
        found_match = False
        for interview in interview_filenames:
            if interview["filename"] == json_interview[0]:
                combined_interviews.append({interview["filename"]: interview.get("title", interview["filename"]) })
                found_match = True
                continue
        if not found_match:
            combined_interviews.append({json_interview[0]: json_interview[0]})
    return combined_interviews


def shorten_filename(filename: str, max_length: int = 20) -> str:
    """Return a shortened, display-friendly version of a filename.

    Heuristics (applied in order):
    - If a colon is present, remove everything before the first ':' (typical package prefix).
    - Remove a trailing '.yml' if present.
    - Insert zero-width spaces after underscores so long YAML-style names can wrap at underscores.
    - If the resulting name is longer than max_length, collapse the middle with an ellipsis.

    Returns a string safe for display (contains \u200b zero-width spaces to allow wrapping).
    """
    if not filename:
        return ''
    # Remove package prefix before ':'
    name = filename.split(':', 1)[-1]
    # Remove .yml suffix
    if name.endswith('.yml'):
        name = name[:-4]
    # Replace path-like slashes with just the last component
    if '/' in name:
        name = name.split('/')[-1]
    # Insert zero-width space after underscores to allow wrapping
    name = name.replace('_', '_' + '\u200b')

    # Collapse middle if too long
    if len(name) > max_length:
        keep = max_length - 3
        front = (keep + 1) // 2
        back = keep // 2
        name = name[:front] + '...' + name[-back:]

    return name

def get_summary_stats(filename: str):
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = """SELECT 
                    COUNT(modtime), 
                    MIN(modtime), 
                    MAX(modtime) 
                    FROM jsonstorage 
                    WHERE filename=%(filename)s 
                    AND 
                    tags IS DISTINCT FROM 'metadata'
                """
        cur.execute(query, {'filename': filename})
        val = cur.fetchone()
    conn.close()
    return val


def get_summary_stats_by_filename():
    query = """SELECT 
                    filename,
                    -- Last 30 days
                    COUNT(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '30 days') AS count_30d,
                    MIN(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '30 days') AS min_30d,
                    MAX(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '30 days') AS max_30d,
                    -- Last 90 days
                    COUNT(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '90 days') AS count_90d,
                    MIN(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '90 days') AS min_90d,
                    MAX(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '90 days') AS max_90d,
                    -- Last 365 days
                    COUNT(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '365 days') AS count_365d,
                    MIN(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '365 days') AS min_365d,
                    MAX(modtime) FILTER (WHERE modtime >= CURRENT_TIMESTAMP - INTERVAL '365 days') AS max_365d,
                    -- All time
                    COUNT(modtime) AS count_all,
                    MIN(modtime) AS min_all,
                    MAX(modtime) AS max_all
                    FROM jsonstorage 
                    WHERE tags IS DISTINCT FROM 'metadata'
                    GROUP BY filename
                    ORDER BY count_30d DESC, count_90d DESC, count_365d DESC
                """

    conn = variables_snapshot_connection()
    try:
        # Try SQLAlchemy-style execute that returns a Result with mappings()
        try:
            result = conn.execute(query)
        except Exception:
            # Some connection objects require a cursor() for execution
            result = None

        if result is not None and hasattr(result, 'mappings'):
            rows = list(result.mappings())
            results = [dict(r) for r in rows]
        else:
            # Fallback to DB-API cursor approach
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
            results = [dict(zip(cols, row)) for row in rows]
    finally:
        conn.close()

    # Normalize None counts to 0 for count columns
    for r in results:
        for key in ('count_30d', 'count_90d', 'count_365d', 'count_all'):
            if r.get(key) is None:
                r[key] = 0
    return results


def get_overall_stats():
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        query = "SELECT COUNT(modtime), MIN(modtime), MAX(modtime) FROM jsonstorage WHERE tags IS DISTINCT FROM 'metadata'"
        cur.execute(query)
        val = cur.fetchone()
    conn.close()
    return val
  
      
def get_stats(filename: str, column:str=None):
    conn = variables_snapshot_connection()
    with conn.cursor() as cur:
        # use a parameterized query to prevent SQL injection
        # Always filter out `metadata` tag because it's used by AssemblyLine to store
        # things like the interview title (which can have user's name).
        # using the tag for anything else isn't something we've commonly seen in the wild
        query = """SELECT 
                   modtime, 
                   data, 
                   tags 
                   FROM jsonstorage 
                   WHERE filename=%(filename)s
                   AND 
                   tags IS DISTINCT FROM 'metadata'"""
        cur.execute(query, {'filename': filename})
        records = list()
        for record in cur:
            # Add modtime to the all stats
            record[1]['modtime'] = record[0]
            # Note that this is normally empty or 'metadata'
            # in store_variables_snapshot() this is the `key` parameter
            record[1]['tags'] = record[2]
            if column:
                if column in record[1]:
                    records.append(record[1][column])
                else:
                    records.append(None)
            else:
                # Adds all of the info to the returned result
                records.append(record[1])
    conn.close()
    return records

def get_columns(records):
    if not records:
        return []
    first_row = next(iter(records), None)
    if first_row and isinstance(first_row, dict):
        return list(first_row.keys())
    else:
        return []

def get_column_values(records, column) -> set:
    if not records or not column:
        return []
    return set([record.get(column) for record in records])
    