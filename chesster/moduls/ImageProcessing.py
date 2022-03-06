def ExtractImageCoordinates(color_image, depth_img, COLOR_UPPER_LIMIT, COLOR_LOWER_LIMIT, ImageTxt="TCP"):
    import cv2 as cv
    import imutils as imutils
    import numpy as np
    hsv_image = cv.cvtColor(color_image, cv.COLOR_BGR2HSV) #Colordetection works better with hsv space
    mask = cv.inRange(hsv_image, COLOR_LOWER_LIMIT, COLOR_UPPER_LIMIT)
    cnts = cv.findContours(mask, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    PxCoords = np.array([0,0])
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
            cv.putText(color_image, f"Depth: {depth_img[cY-1, cX-1]}mm",(20, 460), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
            PxCoords = np.array([cX, cY])
        
    if PxCoords.all() == 0:
        cv.putText(color_image, 'NO TCP FOUND', (int(color_image.shape[0]/2),int(color_image.shape[1]/2)), cv.FONT_HERSHEY_SIMPLEX, 2, (255, 0, 0), 2)
    mask = cv.cvtColor(mask, cv.COLOR_GRAY2BGR)
    images = np.hstack((color_image, mask))
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

def HSV_Color_Selector(images):
    import cv2 as cv
    import numpy as np
    def nothing(x):
        pass
    # Create a window
    cv.namedWindow('image')
    cv.namedWindow('Slider')
    cv.resizeWindow('Slider', 640, 240)
    

    # Create trackbars for color change
    # Hue is from 0-179 for Opencv
    cv.createTrackbar('HMin', 'Slider', 0, 179, nothing)
    cv.createTrackbar('SMin', 'Slider', 0, 255, nothing)
    cv.createTrackbar('VMin', 'Slider', 0, 255, nothing)
    cv.createTrackbar('HMax', 'Slider', 0, 179, nothing)
    cv.createTrackbar('SMax', 'Slider', 0, 255, nothing)
    cv.createTrackbar('VMax', 'Slider', 0, 255, nothing)

    # Set default value for Max HSV trackbars
    cv.setTrackbarPos('HMax', 'Slider', 179)
    cv.setTrackbarPos('SMax', 'Slider', 255)
    cv.setTrackbarPos('VMax', 'Slider', 255)

    # Initialize HSV min/max values
    hMin = sMin = vMin = hMax = sMax = vMax = 0
    phMin = psMin = pvMin = phMax = psMax = pvMax = 0

    while(1):
        # Get current positions of all trackbars
        hMin = cv.getTrackbarPos('HMin', 'Slider')
        sMin = cv.getTrackbarPos('SMin', 'Slider')
        vMin = cv.getTrackbarPos('VMin', 'Slider')
        hMax = cv.getTrackbarPos('HMax', 'Slider')
        sMax = cv.getTrackbarPos('SMax', 'Slider')
        vMax = cv.getTrackbarPos('VMax', 'Slider')

        # Set minimum and maximum HSV values to display
        lower = np.array([hMin, sMin, vMin])
        upper = np.array([hMax, sMax, vMax])
        results = []
        # Convert to HSV format and color threshold
        for i in range(3):
            hsv = cv.cvtColor(images[i], cv.COLOR_RGB2HSV)
            mask = cv.inRange(hsv, lower, upper)
            result = cv.bitwise_and(images[i], images[i], mask=mask)
            results.append(result)
        # Display result image
        results = np.hstack((results[0], results[1], results[2]))
        cv.imshow('image', results)
        if cv.waitKey(10) & 0xFF == ord('q'):
            break

    cv.destroyAllWindows()
    return upper, lower
