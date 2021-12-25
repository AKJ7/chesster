def Printtimer(n):
    import time as time
    import sys as sys
    for i in range(n+1):
        sys.stdout.write(f"\rproceeding in {n-i} seconds...")
        sys.stdout.flush()
        time.sleep(1)

def ImportCSV(path, filename, delimiter, data_type=float):
    import numpy as np
    import os as os
    compl_path = os.path.join(path, filename)
    with open(compl_path, newline='') as csvfile:
        Matrix = np.loadtxt(csvfile, delimiter=";", dtype=data_type)

    return Matrix  

def ExportCSV(Data_Matrix, path, filename, delimiter):
    import numpy as np
    import os as os
    compl_path = os.path.join(path, filename)
    np.savetxt(compl_path, Data_Matrix, delimiter=delimiter)

def ChooseFolder():
    from tkinter import filedialog
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    #root.destroy()
    return folder_selected
