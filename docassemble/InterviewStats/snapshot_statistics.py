from docassemble.base.util import variables_snapshot_connection

__all__ = ['get_stats']


def get_stats(filename: str, column:str=None):
    conn = variables_snapshot_connection()
    cur = conn.cursor()
    # use a parameterized query to prevent SQL injection
    query = "select modtime, data from jsonstorage where filename=%(filename)s"
    cur.execute(query, {'filename': filename})
    records = list()
    for record in cur:
        # Add modtime to the all stats
        record[1]['modtime'] = record[0]
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
    if first_row and isinstance(first_row[1], dict):
        return list(first_row[1].keys())
    else:
        return []

def get_column_values(records, column) -> set:
    if not records or not column:
        return []
    return set([record.get(column) for record in records])
    