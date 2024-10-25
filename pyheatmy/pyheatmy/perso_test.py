import datetime
import matplotlib.pyplot as plt
from sklearn import linear_model
import numpy as np
import os

def date():
    t = datetime.datetime(1977,1,14)
    tot = (t-datetime.datetime(1970,1,1)).total_seconds()
    print(tot)


    from datetime import datetime, timedelta
    # Original timestamp
    timestamp = 1485714600
    # Convert the timestamp to a datetime object
    dt = datetime.fromtimestamp(timestamp)
    # Add an offset, for example, 2 days and 3 hours
    offset = timedelta(days=2, hours=3)
    new_dt = dt + offset
    # Format the new datetime
    formatted_date = new_dt.strftime("%A, %B %d, %Y %I:%M:%S")

    print(formatted_date)

def which_venv():
    import sys
    print(sys.prefix)

def plot():
    X = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10]).reshape(-1, 1)
    Y = [2, 4, 3, 6, 8, 9, 9, 10, 11, 13]
    lm = linear_model.LinearRegression()
    lm.fit(X, Y)
    plt.scatter(X, Y, color="r", marker="o", s=30)
    y_pred = lm.predict(X)
    plt.plot(X, y_pred, color="k")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Simple Linear Regression")
    plt.show()


def search_word_in_files(directory, word):
    # Loop through all files in the given directory
    for foldername, subfolders, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(foldername, filename)

            # Only read text files (optional check)
            if filename.endswith(".txt") or filename.endswith(".py"):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                        # if print(content)
                        # Check if the word is in the content
                        if word in content:
                            print(f"Found '{word}' in: {file_path}")
                except Exception as e:
                    print(f"Could not read file: {file_path}, due to error: {e}")

directory_to_search = ".\pyheatmy\pyheatmy"
word_to_find = "column"

search_word_in_files(directory_to_search, word_to_find)
