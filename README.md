# chesster
AI Chess Robot Project  

## Installation  
Requirements: `pipenv`.  
If `pipenv` not installed but `pip` is:
```bash
pip install pipenv
```
Finally, install the dependencies with
```bash
pipenv install
```  
and to access the shell
```bash
pipenv shell
```  
To generate the UI files, The `PyQT` dev tools need to be installed. Do so using
```bash  
sudo apt-get install qtcreator pyqt5-dev-tools
```
Use
```bash 
pyuic5 chesster/gui/res/window.ui -o chesster/gui/window_ui.py
```
for the UI and 
```bash 
pyrcc5 -o chesster/gui/chess_rules_resources.py chesster/gui/res/chess_rules_resources.qrc
```
for the resource files.

## Run  
After following the Installation steps
```bash
pipenv run main
```
or 
```bash 
python -m chesster
```


## Miscellaneous  

### Camera  
1. The expected camera used is the Realsense D435. Its libraries and packages can be found [here](https://www.intelrealsense.com/get-started-depth-camera/).  
2. [Code examples](https://github.com/IntelRealSense/librealsense/tree/master/wrappers/python/examples)  
3. [3D File format](https://de.wikipedia.org/wiki/Polygon_File_Format)  


### Chessboard  
1. [Chessboard fields notation](https://www.dummies.com/games/chess/understanding-chess-notation/)
2. [Chess Notation](https://en.wikipedia.org/wiki/Chess_notation)  
3. [FEN Notation](https://en.wikipedia.org/wiki/Forsyth%E2%80%93Edwards_Notation)
4. [Universal Chess Interface (UCI)](https://en.wikipedia.org/wiki/Universal_Chess_Interface)  


### Robot Arm  
1. [Code examples](https://github.com/SintefManufacturing/python-urx/tree/master/examples)  

### Object Recognition  
1. [Chessboard detection](https://en.wikipedia.org/wiki/Chessboard_detection)
2. [Unsharp masking](https://en.wikipedia.org/wiki/Unsharp_masking)  


### GUI  
1. The GUI was made using [PyQt5](https://wiki.python.org/moin/PyQt).
2. The chess rules originates from [here](https://www.wiki-schacharena.de/Schachregeln_f%C3%BCr_Einsteiger).  
