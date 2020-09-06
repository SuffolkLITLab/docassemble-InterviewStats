from docassemble.base.util import variables_snapshot_connection, user_info

__all__ = ['get_stats']

def get_stats(filename, variable_name):
  conn = variables_snapshot_connection()
  cur = conn.cursor()
  query = "select data->>'" # This is how we get SQL injection
  query += variable_name
  query += "' from jsonstorage where filename='" + filename + "'"
  cur.execute(query)
  records = list()
  for record in cur.fetchall():
    records.append(record)
  conn.close()
  return records