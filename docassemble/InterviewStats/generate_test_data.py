from docassemble.webapp.jsonstore import read_answer_json, write_answer_json
from docassemble.base.generate_key import random_alphanumeric
from docassemble.base.functions import get_current_info
from docassemble.base.util import variables_snapshot_connection

def write_random_user(data, filename=None, tags=None):
  if not filename:
    filename = get_current_info().get('yaml_filename', None)
  random_uid = random_alphanumeric(32)
  write_answer_json(random_uid, filename, data, tags, persistent=False)

def delete_data_from_interview(filename=None):
  if not filename:
    filename = get_current_info().get('yaml_filename', None)
  conn = variables_snapshot_connection()
  cur = conn.cursor()
  # use a parameterized query to prevent SQL injection
  query = "DELETE FROM jsonstorage WHERE filename=%(filename)s"
  cur.execute(query, {'filename': filename})
  conn.commit()
  conn.close()