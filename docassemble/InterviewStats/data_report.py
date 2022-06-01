from docassemble.webapp.jsonstore import read_answer_json, write_answer_json, JsonStorage, JsonDb
from docassemble.base.generate_key import random_alphanumeric
from docassemble.base.functions import get_current_info
from docassemble.base.util import variables_snapshot_connection
import random
from .snapshot_statistics import *

__all__ = ['get_column_values_list', 
           'get_col_val_count', 
           'processing_data', 
           'save_random_records',
           'phrase']

def processing_data(raw_data=None, headings=None):
    """
    This function is used by interviewStats to extract saved data. It does the following:
    1. "Unflatten" the data for multi-valued fields
    2. Calculate answer count/pct for each field's data
    3. Return data needed for single-valued fields table and multi-valued fields table display
    """
    # 1. Build filtered field-type lists
    # 1.1 Get field-types column from raw_data
    field_type_full_dict = {}
    field_type_full_dict = raw_data[0]['field_type_list']
    records_count = len(raw_data)
    
    # 1.2. Identify multi-valued type fields for graph, this is the list of original question variable names, not the flattened column headings in the database.
    multi_choices_fld_list = []
    for k, v in field_type_full_dict.items():
      if v in ['checkboxes', 'multiselect']:
        multi_choices_fld_list.append(k)      
    
    # 1.2.1 Set multi-valued headings to the database column headings (un-flatten them)
    multi_choices_heading_dict = {}    
    for fld in multi_choices_fld_list:      
      multi_choices_heading_dict[fld] = [v for v in headings  if fld in v] #{fld: [fld_subkeys]}
    
    # 1.3. Set single value field list - remove text/numberic fields and multi-valued fields from field_type_full_list
    single_value_fld_list = list()
    for k, v in field_type_full_dict.items():
      if v not in ['text', 'area', 'number', 'integer', 'currency'] and k not in multi_choices_fld_list:        
        single_value_fld_list.append(k)
    
    # 2. Build data dictionaries for tabular data arrays
    answer_counts_multi = dict() 
    possible_answers_multi = list() # Question's possible answers
    answer_counts_single = dict()    
    possible_answers_single = list() # Question's possible answers
        
    # 2.1 Build data for multi-valued questions
    for fld in multi_choices_fld_list: 
      # Merge flattened columns into multi_sub_dict        
      # subkeys are "choices" names of the question variable
      sub_dict = dict()
      for row, subkeys in multi_choices_heading_dict.items(): 
        if row == fld:
          for k in subkeys:                                     
            # Remove prefix portion from each subkey
            original_k = k.replace(fld + "_", '')          
            # Get answer data for each subkey
            col = get_column_values_list(raw_data, k)
            # Get answer's count and % for each subkey
            sub_dict[original_k] = get_col_val_count(records_count, column = col)

      # Save answer's "count / %" for fld      
      answer_counts_multi[fld] = {k: v for k, v in sub_dict.items()}
      # Possible_answers_single will be used as index in the table display
      possible_answers_multi.append([k for k in sub_dict.keys()])
      
    # 2.2 Build data for single value questions
    for fld in single_value_fld_list:
      # Get list of unique values for fld
      unique_col = get_column_values(raw_data, fld) 
      # Get list of complete data for fld
      col = get_column_values_list(raw_data, fld)  
      # Save answer's "count / %" for fld
      answer_counts_single[fld] = get_col_val_count(records_count, labels=unique_col, column = col)
      # Possible_answers_single will be used as index in the table display
      possible_answers_single.append([t for t in unique_col])
    
    # 3. Return results - separate multi-valued fields from single-valued fields
    return [answer_counts_multi, possible_answers_multi, answer_counts_single, possible_answers_single]
  
def get_column_values_list(records, column) -> list:    
    if not records or not column:
        return []
    return [record.get(column) for record in records]
  
def get_col_val_count(records_count=None, label=None, labels=None, column=None):    
    if labels: # Single-valued fields
      results = dict()
      for val in labels:
        cnt = column.count(val)
        pct = "%.1f%%" % round(cnt*100/records_count, 1)
        results[val] = f'{cnt} / {pct}'
        
    else: # Multi-choices fields, count True for each label/subkey      
      cnt = 0
      for item in column:              
        if item:
          cnt += 1
      pct = "%.1f%%" % round(cnt*100/records_count, 1)
      results = f'{cnt} / {pct}'
    return results

def save_random_records(number_of_records, title = '', seed_data_list = None, date_input=None, tags=None):
    """
    Generate random survey type records for testing data reports.
    """    
    for index in range(number_of_records): 
      type_dict = dict()
      field_dict = dict()
      for k, v in seed_data_list.items():
        type_dict[k] = list(v)[1]
        field_dict[k] = list(v)[0] # Field name without quotes   
      
      data_to_save = dict()
      data_to_save['title'] = title
      data_to_save['field_type_list'] = type_dict
      
      for k, v in type_dict.items():  
        # If a field is of checkboxes type, flatten its subkeys
        # so that each subkey/value pair is saved in its own column.
        if v in ['checkboxes', 'multiselect']:          
          for label in field_dict[k]:
            data_to_save[k + '_' + label] = (random.choice(field_dict[k]) == label)
        else:          
          data_to_save[k]  = random.choice(field_dict[k])
      
      record_date = random.choice(date_input)
      
      filename = get_current_info().get('yaml_filename', None)   
      random_uid = random_alphanumeric(32)
      new_entry = JsonStorage(filename=filename, key=random_uid, data=data_to_save, tags=tags, modtime=record_date, persistent=False)
      JsonDb.add(new_entry)
    JsonDb.commit()
    
def phrase(input:str = None) -> str:
    base = {'eq': 'on', 'gt': 'after', 'lt': 'before', 'between': 'between'}
    return base[input]