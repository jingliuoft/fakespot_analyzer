import pickle
import datetime
import re

def save_pickle(obj, pickle_file_name):
    with open(f"{pickle_file_name}.pkl", 'wb') as f:
        pickle.dump(obj, f)
        print(f"obj successfully saved.")

def load_pickle(pickle_file_name):
    with open(f"{pickle_file_name}.pkl", 'rb') as f:
        obj = pickle.load(f)
        print(f"obj successfully loaded.")
    return obj

def extract_date_from_review_string(review_string):
  """Extracts the date from a review string in the format """
  pattern = r"([A-Za-z]+ \d{1,2}, \d{4})"
  match = re.search(pattern, review_string)

  if match:
    date_string = match.group(1)
    date_object = datetime.datetime.strptime(date_string, "%B %d, %Y").date()
    return date_object
  else:
    return None