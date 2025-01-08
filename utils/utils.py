import pickle

def save_pickle(df, pickle_file_name):
    with open("pickle_file_name.pkl", 'wb') as f:  # 'wb' for writing in binary mode
        pickle.dump(df, f)
        print(f"df successfully saved.")

def load_pickle(pickle_file_name):
    with open("{pickle_file_name}.pkl", 'rb') as f:  # 'wb' for writing in binary mode
        df = pickle.load(f)
        print(f"df successfully loaded.")
    return df