import numpy as np
import sys as sys
import os as os
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.callbacks import TensorBoard
from tensorflow import keras
sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
from moduls.GenericSysFunctions import Printtimer, ImportCSV, ExportCSV, ChooseFolder #Import of custom moduls
from moduls.ImageProcessing import ExtractImageCoordinates
import random as rng


def get_Data():
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, "Input.csv", ";")
    X = np.round(X, 0)
    X = X[:, 800:1000]
    X = np.transpose(X)

    Y = ImportCSV(Dir, "Output.csv", ";")
    Y = np.round(Y, 0)
    Y = Y[:, 800:1000]
    Y = np.transpose(Y)
    return X, Y

def main():
    NAME = "Test"
    model = keras.models.load_model("C:/Chesster NN Models/"+NAME)
    X, Y = get_Data()
    n_false = 0
    n_true = 0
    for i in range(X.shape[0]):
        index = rng.randint(0,199)
        Input = X[index, :]
        Input = Input[np.newaxis, :]
        Prediction = np.round(model.predict(Input), 0)
        Output = Y[index, :]
        Output = Output[np.newaxis, :]
        if np.array_equal(Prediction, Output):
            n_true = n_true + 1
        else:
            n_false = n_false + 1
    print(f'{np.round((n_true/X.shape[0]), 3)*100}% Predictions correct ({n_true} of {X.shape[0]})')



if __name__ == "__main__":
    main()