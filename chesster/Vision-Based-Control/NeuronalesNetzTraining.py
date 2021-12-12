import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from tensorflow.keras.callbacks import TensorBoard
from sklearn.datasets import make_regression
import os as os
import sys as sys
sys.path.append(os.path.dirname(sys.path[0]))
from SystemRelatedFunctions.GenericSysFunctions import ImportCSV

def get_Model(n_input, n_output, n_Dense, n_nodes):
    model = Sequential()
    model.add(Dense(n_nodes, input_dim=n_input, kernel_initializer='he_uniform', activation='relu')) #INPUT-LAYER

    for i in range(n_Dense):
        model.add(Dense(n_nodes, kernel_initializer='he_uniform', activation='relu'))

    model.add(Dense(n_output)) #OUTPUT-LAYER

    model.compile(loss='mae', optimizer='adam', metrics=['accuracy'])
    NAME = f'nD{n_Dense}_nN{n_nodes}'
    return model, NAME

def get_Data_test():
    X, Y = make_regression(n_samples=200, n_features=3, n_informative=3, n_targets=3, random_state=2)
    return X, Y

def get_Data():
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, "Input.csv", ";")
    Y = ImportCSV(Dir, "Output.csv", ";")
    return X, Y


def train():
    X, Y = get_Data_test()
    n_data = X.shape[0]
    Epochs = 200
    model, NAME = get_Model(3, 3, 3, 40)
    NAME = NAME+f"_nData{n_data}_nEpochs{Epochs}"
    tensorboard = TensorBoard(log_dir='chesster/Vision-Based-Control/logs/'+NAME) #to start tensorboard: Navigate to Chesster Root -> CMD ->
    #tensorboard --logdir=chesster/Vision-Based-Control/logs/

    model.fit(X, Y, epochs=Epochs, validation_split=0.2, callbacks=[tensorboard])
    model.save("c:/Chesster NN Models/"+NAME)
if __name__=="__main__":
    train()