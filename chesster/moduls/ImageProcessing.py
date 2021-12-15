def ExtractImageCoordinates(color_image, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT, ImageTxt="TCP"):
    import cv2 as cv
    import imutils as imutils
    import numpy as np
    hsv_image = cv.cvtColor(color_image, cv.COLOR_BGR2HSV) #Colordetection works better with hsv space
    mask = cv.inRange(hsv_image, COLOR_LOWER_LIMIT, COLOR_UPPER_LIMIT)

    cv.imshow(f"Masked Image", mask)
    cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    for c in cnts:
        M = cv.moments(c)
        area = cv.contourArea(c)
        if (area >= 20):
            cX = int(M["m10"] / M["m00"])
            cY = int(M["m01"] / M["m00"])
            #print(f"Centerpoint {i} painted")
            cv.drawContours(color_image, [c], -1, [0, 0, 255], 2)
            cv.circle(color_image, (cX,cY), 3, [0, 0, 255], -1)
            cv.putText(color_image, ImageTxt, (cX-20, cY-20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            PxCoords = np.array([cX, cY])
    images = np.hstack((mask, color_image))
    return PxCoords, color_image, images

def FigureMapping(path, filename):
    import sys as sys
    import os as os
    import numpy as np
    sys.path.append(os.path.dirname(sys.path[0])) #preperation for import of custom moduls
    from moduls.GenericSysFunctions import ImportCSV
    
    ColorMappingNp = ImportCSV(path, filename, ";", str)
    temp = []
    for j in range(ColorMappingNp.shape[0]):
        temp.append([ColorMappingNp[j,0], [float(ColorMappingNp[j,1]),float(ColorMappingNp[j,2]),float(ColorMappingNp[j,3])], [float(ColorMappingNp[j,4]),float(ColorMappingNp[j,5]),float(ColorMappingNp[j,6])]])
    temp = np.array(temp) #Shape: Figur; UpperLimit; LowerLimit
    return temp

