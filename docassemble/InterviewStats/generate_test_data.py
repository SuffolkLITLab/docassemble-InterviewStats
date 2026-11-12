from docassemble.base.generate_key import random_alphanumeric
from docassemble.base.functions import get_current_info
from docassemble.base.util import variables_snapshot_connection

from .data_report import JsonStorage, _json_scope

__all__ = ["write_random_user", "delete_data_from_interview"]


def write_random_user(data_iterator, filename=None, tags=None, modtime_generator=None):
    if not filename:
        filename = get_current_info().get("yaml_filename", None)
    new_entries = []
    for data in data_iterator:
        random_uid = random_alphanumeric(32)
        if modtime_generator:
            new_entry = JsonStorage(
                filename=filename,
                key=random_uid,
                data=data,
                tags=tags,
                persistent=False,
                modtime=modtime_generator(),
            )
        else:
            new_entry = JsonStorage(
                filename=filename,
                key=random_uid,
                data=data,
                tags=tags,
                persistent=False,
            )
        new_entries.append(new_entry)
    with _json_scope() as session:
        for new_entry in new_entries:
            session.add(new_entry)


def delete_data_from_interview(filename=None):
    if not filename:
        filename = get_current_info().get("yaml_filename", None)
    conn = variables_snapshot_connection()
    cur = conn.cursor()
    # use a parameterized query to prevent SQL injection
    query = "DELETE FROM jsonstorage WHERE filename=%(filename)s"
    cur.execute(query, {"filename": filename})
    conn.commit()
    conn.close()
