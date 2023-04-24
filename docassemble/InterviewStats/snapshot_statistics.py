from docassemble.base.util import variables_snapshot_connection, interview_menu
from typing import List

__all__ = ['get_filenames', 'get_summary_stats', 'get_stats', 'get_columns', 'get_column_values', 'get_combined_filename_list', "get_overall_stats"]

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
    