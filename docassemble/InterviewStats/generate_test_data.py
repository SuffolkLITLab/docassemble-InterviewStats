from docassemble.webapp.jsonstore import read_answer_json, write_answer_json, JsonStorage, JsonDb
from docassemble.base.generate_key import random_alphanumeric
from docassemble.base.functions import get_current_info
from docassemble.base.util import variables_snapshot_connection

__all__ = ['write_random_user', 'delete_data_from_interview']

def write_random_user(data_iterator, filename=None, tags=None):
  if not filename:
    filename = get_current_info().get('yaml_filename', None)
  for data in data_iterator:
    random_uid = random_alphanumeric(32)
    new_entry = JsonStorage(filename=filename, key=random_uid, data=data, tags=tags, persistent=False)
    JsonDb.add(new_entry)
  JsonDb.commit()
  
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