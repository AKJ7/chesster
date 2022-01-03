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


def get_Data(Norm=True, Fixed_height=True, XName="Input775Bereinigt.csv", YName="Output775Bereinigt.csv"):
    DIRPATH = os.path.dirname(__file__)
    Dir = DIRPATH+"/Trainingsdaten/"
    X = ImportCSV(Dir, XName, ";")
    X = np.round(X, 3)
    Y = ImportCSV(Dir, YName, ";")
    Y = np.round(Y, 3)
    X = np.transpose(X)
    Y = np.transpose(Y)

    if Fixed_height == True:
        Y[2,:] = 70.0
    if Norm == True:    
        X_Norm = 2.*(X - np.min(X))/np.ptp(X)-1 #normalization
        Y_Norm = 2.*(Y - np.min(Y))/np.ptp(Y)-1 #normalization
    else: 
        X_Norm = X
        Y_Norm = Y
    return X_Norm, Y_Norm, X, Y

def main():
    DIRPATH = os.path.dirname(__file__)
    Norm = True
    Fixed_height = True
    n_Output = 2
    n_Input = 3
    NAME = 'nD2_nN128_nData775_nEpochs25000_mae_Norm_True_FH_True_Input3_Output2_loss_mae'
    model = keras.models.load_model("C:/Chesster NN Models/"+NAME)
    X, Y, X_Backup, Y_Backup = get_Data(Norm, Fixed_height, XName='Input775Artificial.csv', YName='Output775Artificial.csv')
    Input = X[-50:,0:n_Input]
    Prediction = model.predict(Input)
    Output = Y[-50:,:]
    if Norm == True:
        X = ((X+1)*np.ptp(X_Backup))*2+np.min(X_Backup)
        Output = ((Output+1)*np.ptp(Y_Backup))/2+np.min(Y_Backup)
        Prediction = ((Prediction+1)*np.ptp(Y_Backup))/2+np.min(Y_Backup)

    Output = np.round(Output, 2)
    Prediction = np.round(Prediction, 2)
    Err = np.zeros((3, Prediction.shape[0]))
    if n_Output== 2:
        temp = np.zeros((Prediction.shape[0], 3))
        temp[:, 2] = 70.0
        temp[:, 0:2] = Prediction
        Prediction = temp
        for i in range(Output.shape[0]):
            Err[:,i] = np.abs(Prediction[i, :]-Output[i, :])
            print('####################################################################')
            print(f'Real Output: X: {Output[i,0]}; Y: {Output[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Prediction: X: {Prediction[i,0]}; Y: {Prediction[i,1]}; Z: {Y_Backup[i,2]}')
            print(f'Abs. Error {i+1}. Output:  X: {Err[0,i]}; Y: {Err[1, i]}; Z: {Err[2, i]}')
            print(f'Rel. Error {i+1}. Output:  X: {round(abs((Prediction[i, 0]-Output[i, 0])/Output[i, 0])*100)}%; Y: {round(abs((Prediction[i, 1]-Output[i, 1])/Output[i,1])*100)}%; Z: {round(abs((Y_Backup[i, 2]-Y_Backup[i, 2])/Y_Backup[i,2])*100)}%')
    Data = ImportCSV(DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')
    if Data.size == 0:
        ExportCSV(Err, DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')
    else:
        temp = np.zeros((Data.shape[0]+3, Data.shape[1]))
        temp[:Data.shape[0],:Data.shape[1]] = Data
        temp[-3:,:] = Err
        ExportCSV(temp, DIRPATH+'/NeuralNetworkComparison/', 'Measurements.csv', ';')
    NAME = 'TEST ARTIFICIAL DATA ON TRAINED MODEL'
    Names = ImportCSV(DIRPATH+'/NeuralNetworkComparison/', 'Names.csv', ';', data_type=np.string_)
    if Names.size == 0:
        ExportCSV(np.array([NAME]), DIRPATH+'/NeuralNetworkComparison/', 'Names.csv', ';', format='%s')
    else:
        with open(DIRPATH+'/NeuralNetworkComparison/Names.csv', 'a') as file:
            file.write(NAME+'\n')

if __name__ == "__main__":
    main()