# Object Recognition Module Manual  

## Requirements  
- The chessboard doesn't move  
- The chessboard is fully visible in the image

## Steps  
### Generate Chessboard data  

Data (fields positions, center of fields, empty state) of the **empty** chessboard needs to be presaved before the module can 
be used.
```python
ObjectRecognition.create_chessboard_data()
```
This will save some required informations of the chessboard to a pickled file.


### Get matrix data  

Example:
```python
detector = ObjectRecognition()      # Loads the empty chessboard data from a file
detector.start()                    # Generate the chessboard start position. Requirements: All pieces need to be at their correponding possitions

detector.determine_changes()        # Determine the changed files and update the underlying matrix

chesspiece = detector.get_chesspiece_info() 


detector.stop()
```

