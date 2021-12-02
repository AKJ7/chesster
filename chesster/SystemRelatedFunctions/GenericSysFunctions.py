import time as time
import sys as sys

def Printtimer(n):
    for i in range(n+1):
        sys.stdout.write(f"\rproceeding in {n-i} seconds...")
        sys.stdout.flush()
        time.sleep(1)

def ImportCSV(path, filename, delimiter):
    import csv as csv
    import numpy as np
    import os as os
    Matrix = np.array([])
    compl_path = os.path.join(path, filename)
    with open(compl_path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=delimiter)
        for i, row in enumerate(reader):
            Matrix = np.append(Matrix, np.array(row), axis=i)

    return Matrix  
            
    

print(sys.path)