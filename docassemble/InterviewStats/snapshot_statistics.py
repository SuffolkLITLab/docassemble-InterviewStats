from docassemble.base.util import variables_snapshot_connection, user_info

__all__ = ['get_stats']

def get_stats(filename):
  conn = variables_snapshot_connection()
  cur = conn.cursor()
  # use a parameterized query to prevent SQL injection
  query = "select data from jsonstorage where filename=%(filename)s"
  cur.execute(query, {'filename': filename})
  records = list()
  for record in cur.fetchall():
    records.append(record)
  conn.close()
  return records