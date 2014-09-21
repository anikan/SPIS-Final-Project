#Improvement ideas:
#Use remote desktop to view images live.
#Use ultrasound to make sure we don't crash.

import RPi.GPIO as GPIO, sys, threading, time
import io
import PIL
import math
import picamera
from PIL import Image

#use physical pin numbering
GPIO.setmode(GPIO.BOARD)

#use pwm on inputs so motors don't go too fast
# Pins 19, 21 Right Motor
# Pins 24, 26 Left Motor
GPIO.setup(19, GPIO.OUT)
#p is right motor
p=GPIO.PWM(19, 20)
p.start(0)
GPIO.setup(21, GPIO.OUT)
q=GPIO.PWM(21, 20)
q.start(0)
GPIO.setup(24, GPIO.OUT)
#A is left motor
a=GPIO.PWM(24,20)
a.start(0)
GPIO.setup(26, GPIO.OUT)
b=GPIO.PWM(26,20)
b.start(0)
SONAR = 8

#Standard movespeed
moveSpeed = 50
#Add or subtract factor to rotate.
deltaSpeed = 20

LED1 = 22
LED2 = 18
LED3 = 11
LED4 = 07
GPIO.setup(LED1, GPIO.OUT)
GPIO.setup(LED2, GPIO.OUT)
GPIO.setup(LED3, GPIO.OUT)
GPIO.setup(LED4, GPIO.OUT)

#Camera Setup
ioStream = io.BytesIO()
##with picamera.PiCamera() as camera:
##  camera.start_preview()
##  time.sleep(2)
##  camera.capture(ioStream, format = 'jpeg')
##ioStream.seek(0)
##image = Image.open(ioStream)
##image.show()
##image.save("HardWork.jpeg")

def setLEDs(L1, L2, L3, L4):
  GPIO.output(LED1, L1)
  GPIO.output(LED2, L2)
  GPIO.output(LED3, L3)
  GPIO.output(LED4, L4)

def stopAll():
  p.ChangeDutyCycle(0)
  q.ChangeDutyCycle(0)
  a.ChangeDutyCycle(0)
  b.ChangeDutyCycle(0)
  setLEDs(1, 1, 1, 1)
  print('stop')

def setLEDs(L1, L2, L3, L4):
  GPIO.output(LED1, L1)
  GPIO.output(LED2, L2)
  GPIO.output(LED3, L3)
  GPIO.output(LED4, L4)

#Walls of lab are very light so hopefully people are darker. Could also set a target color easily.
def getDarkestSquare(im, areaLength):
  '''Divides grid into many squares, and gets the x coordinate of the darkest one (using luminance).'''
  #This 2D list stores things in form [yCoordinate][xCoordinate]
  tileList = [[]]
  #We first think of the image as a grid where each square contains pixels. We only care about the xCoordinate of the darkest square.
  #im.save("darn.jpg")
  lowestAmount = 256
  xChampion = 0
  for yGrid in range(im.size[1]/areaLength):
    tileList.append([])
    for xGrid in range(im.size[0]/ areaLength):
      #Once we know which grid tile we are in, we find the colors of the pixels in the tile, and then put the average on a tile image in a list.
      (redAvg, greenAvg, blueAvg) = (0,0,0)
      #Keeping track of number of pixels for average.
      numPix = 0

      #For each grid tile, we add current values of colors and increment the number of pixels to be averaged after traveling through all pixels
      #Skip some pixels for speed, depending on fudgeAmount.
      fudgeAmount = 4
      #print "Accessing " + str(xGrid*areaLength) + ", " + str(yGrid*areaLength)
      for xPix in range(areaLength / fudgeAmount):
        for yPix in range(areaLength / fudgeAmount):
          numPix += 1
          (red, green, blue) = im.getpixel((xPix * fudgeAmount + xGrid*areaLength, yPix * fudgeAmount + yGrid*areaLength))
          redAvg += red
          greenAvg += green
          blueAvg += blue
      #After going through all pixels in this tile, we divide by number of pixels for average.
      redAvg /= numPix
      greenAvg /= numPix
      blueAvg /= numPix
      #Get brightness.
      luminance = int(redAvg * .21 + greenAvg *.72 + blueAvg * .07)
      if lowestAmount > luminance:
        lowestAmount = luminance
        xChampion = len(tileList[yGrid])
      tileList[yGrid].append(luminance)
#      print 'processing' + str(xGrid) +" " +  str(yGrid)
#      print luminance
##  currentTile = 0 #Keeps track of which tile should be pasted next.
##
##  #Keep track of index of desired value. Currently darkest.
##  xChampion = 0
##  yChampion = 0
##  for yGrid in range(im.size[1]/areaLength):
##    for xGrid in range(im.size[0]/ areaLength):
##      #We compare all tiles with the champion coordinates for the darkest tile.
##      if (tileList[yGrid][xGrid] < tileList[yChampion][xChampion]):
##        yChampion = yGrid
##        xChampion = xGrid
##      currentTile += 1
  #At this point we have the darkest area. Just use xChampion for needed coordinate.
  print "Xcom = " + str(xChampion)
  XRatio = xChampion / (im.size[0]/float(areaLength))
  print "XRatio = " + str(XRatio)
  return 1 - XRatio

  #Walls of lab are very light so hopefully people are darker. Movement is found by difference between images.
def getMostDifferentSquare(im1, im2, areaLength):
  '''Divides grid into many squares, finds the one most different brightness between the two images.'''
  tileList = [[]]
  #tileList2 = [[]]
  #We first think of the image as a grid where each square contains pixels. We only care about the xCoordinate of the lightest square.

  highestDifference = 0
  xChampion = 0
  for yGrid in range(im1.size[1]/ areaLength):
    tileList.append([])
    for xGrid in range(im1.size[0]/ areaLength):
      #Once we know which grid tile we are in, we find the colors of the pixels in the tile, and then put the average on a tile image in a list.
      (redAvg, greenAvg, blueAvg) = (0,0,0)
      numPix = 0

      #For each grid tile, we add current values of colors and increment the number of pixels to be averaged after traveling through all pixels
      fudgeAmount = 4

      for xPix in range(areaLength / fudgeAmount):
        for yPix in range(areaLength / fudgeAmount):
          numPix += 1
          (red, green, blue) = im1.getpixel((xPix * fudgeAmount + xGrid*areaLength, yPix * fudgeAmount + yGrid*areaLength))
          (red2, green2, blue2) = im2.getpixel((xPix * fudgeAmount + xGrid*areaLength, yPix * fudgeAmount + yGrid*areaLength))

          redAvg += abs(red - red2)
          greenAvg += abs(green - green2)
          blueAvg += abs(blue - blue2)
      redAvg /= numPix
      greenAvg /= numPix
      blueAvg /= numPix
      #Get brightness.
      luminance = int(redAvg * .21 + greenAvg *.72 + blueAvg * .07)

      if highestDifference < luminance:
        highestDifference = luminance
        xChampion = len(tileList[yGrid])
      tileList[yGrid].append(luminance)

  #currentTile = 0 #Keeps track of which tile should be pasted next. Starting with 1 should shift everything to the left.

  #Keep track of index of desired value. Currently goes towards most different square.
##  xChampion = 0
##  yChampion = 0
##  amount = 0
##  for yGrid in range(im1.size[1]/areaLength):
##    for xGrid in range(im1.size[0]/ areaLength):
##      if (abs(tileList[yGrid][xGrid]) > amount):
##        xChampion = xGrid
##	yChampion = yGrid
##        amount = abs(tileList[yGrid][xGrid])
  #At this point we have the most different area. Just use xChampion for needed coordinate.
  #If there wasn't much movement, then there isn't much difference; don't move.
  if (highestDifference < 20):
    return (False, 0)
  else:
    print "Xcom = " + str(xChampion)
    XRatio = xChampion / (im1.size[0]/float(areaLength))
    print "XRatio = " + str(XRatio)
    #Returns 1 - XRatio because the image is upside down.
    return (True, 1 - XRatio)

  #Walls of lab are very light so hopefully people are darker. Could also set a target color easily.
def getTennisBallSquare(im, areaLength):
  tennisBallColors = [255,69,0]
  '''Divides grid into many squares, and gets the x coordinate of the darkest one (using luminance).'''
  #This 2D list stores things in form [yCoordinate][xCoordinate]
  tileList = [[]]
  #We first think of the image as a grid where each square contains pixels. We only care about the xCoordinate of the darkest square.
  #im.save("darn.jpg")
  lowestdiff = 1000
  xChampion = 0
  for yGrid in range(im.size[1]/areaLength):
    tileList.append([])
    for xGrid in range(im.size[0]/ areaLength):
      #Once we know which grid tile we are in, we find the colors of the pixels in the tile, and then put the average on a tile image in a list.
      (redAvg, greenAvg, blueAvg) = (0,0,0)
      #Keeping track of number of pixels for average.
      numPix = 0

      #For each grid tile, we add current values of colors and increment the number of pixels to be averaged after traveling through all pixels
      #Skip some pixels for speed, depending on fudgeAmount.
      fudgeAmount = 3
      #print "Accessing " + str(xGrid*areaLength) + ", " + str(yGrid*areaLength)
      for xPix in range(areaLength / fudgeAmount):
        for yPix in range(areaLength / fudgeAmount):
          numPix += 1
          (red, green, blue) = im.getpixel((xPix * fudgeAmount + xGrid*areaLength, yPix * fudgeAmount + yGrid*areaLength))
          redAvg += red
          greenAvg += green
          blueAvg += blue
      #After going through all pixels in this tile, we divide by number of pixels for average.
      redAvg /= numPix
      greenAvg /= numPix
      blueAvg /= numPix
      #Get brightness.
      diff = (redAvg - tennisBallColors[0] + greenAvg - tennisBallColors[1] + blueAvg - tennisBallColors[0])
      print diff
      if lowestAmount > diff:
        lowestAmount = diff
        xChampion = len(tileList[yGrid])
      tileList[yGrid].append(diff)

  #At this point we have the darkest area. Just use xChampion for needed coordinate.
  print "Xcom = " + str(xChampion)
  XRatio = xChampion / (im.size[0]/float(areaLength))
  print "XRatio = " + str(XRatio)
  return 1 - XRatio
def getSpecificSquare(im, areaLength):
  color = [199,196,55]
  '''Divides grid into many squares, and gets the x coordinate of the darkest one (using luminance).'''
  #This 2D list stores things in form [yCoordinate][xCoordinate]
  tileList = [[]]
  #We first think of the image as a grid where each square contains pixels. We only care about the xCoordinate of the darkest square.
  #im.save("darn.jpg")
  lowestdiff = 1000
  xChampion = 0
  for yGrid in range(im.size[1]/areaLength):
    tileList.append([])
    for xGrid in range(im.size[0]/ areaLength):
      #Once we know which grid tile we are in, we find the colors of the pixels in the tile, and then put the average on a tile image in a list.
      (redAvg, greenAvg, blueAvg) = (0,0,0)
      #Keeping track of number of pixels for average.
      numPix = 0

      #For each grid tile, we add current values of colors and increment the number of pixels to be averaged after traveling through all pixels
      #Skip some pixels for speed, depending on fudgeAmount.
      fudgeAmount = 3
      #print "Accessing " + str(xGrid*areaLength) + ", " + str(yGrid*areaLength)
      for xPix in range(areaLength / fudgeAmount):
        for yPix in range(areaLength / fudgeAmount):
          numPix += 1
          (red, green, blue) = im.getpixel((xPix * fudgeAmount + xGrid*areaLength, yPix * fudgeAmount + yGrid*areaLength))
          redAvg += red
          greenAvg += green
          blueAvg += blue
      #After going through all pixels in this tile, we divide by number of pixels for average.
      redAvg /= numPix
      greenAvg /= numPix
      blueAvg /= numPix
      #print redAvg
      #print greenAvg
      #print blueAvg
      #Get difference of colors.
      diff = (abs(redAvg - color[0]) + abs(greenAvg - color[1]) + abs(blueAvg - color[2]))
      #print diff
      if lowestdiff > diff:
        lowestdiff = diff
        xChampion = len(tileList[yGrid])
      tileList[yGrid].append(diff)

  #At this point we have the darkest area. Just use xChampion for needed coordinate.
  print "Xcom = " + str(xChampion)
  XRatio = xChampion / (im.size[0]/float(areaLength))
  print "XRatio = " + str(XRatio)
  return 1 - XRatio
  
#53 degree field of view
#Head 26 degrees in either direction
#Assuming positive is clockwise and negative is counterclockwise
#Returns
def getDirection(pieceRatio):
  '''Given the ratio from 0 to 1 of the fishy part of the image, return the angle, we want to go to'''
  return (-26 + 52 * pieceRatio)

#Given angle in degrees, set motors to travel in that direction.
def moveMotors(angle):
  #If angle equals zero, then both motors have same speed.
  #If low angle, then head left, right motor = faster.
  #If high angle, head right, left motor = faster.
  deltaAmount = math.sin(angle* math.pi/180) * deltaSpeed
  print deltaAmount
  leftMotorSpeed = moveSpeed + deltaAmount
  rightMotorSpeed = moveSpeed - deltaAmount

  p.ChangeDutyCycle(rightMotorSpeed)
  q.ChangeDutyCycle(0)
  a.ChangeDutyCycle(leftMotorSpeed)
  b.ChangeDutyCycle(0)
  setLEDs(0, 0, 1, 1)
  if (deltaAmount < 2):
      print('left')
      setLEDs(0,0,1,1)
  elif (deltaAmount > 2):
      print ('right')
      setLEDs(1,1,0,0)
  else:
      print ('straight')
      setLEDs(1,0,0,1)

def rightTurn():
  p.ChangeDutyCycle(0)
  q.ChangeDutyCycle(0)
  a.ChangeDutyCycle(50)
  b.ChangeDutyCycle(0)
  time.sleep(.5)
  stopAll()

setLEDs(1, 1, 1, 1) # switch all LEDs off
#Select mode
mode = "basket" #Modes are color and motion

try:
  #Grab one photo and store in prevImage.
  #prevImage = Image.open(ioStream)
  #Camera Setup

  ioStream = io.BytesIO()
  #with picamera.PiCamera() as camera:
  ##camera.capture(ioStream, format = 'jpeg')
  ##ioStream.seek(0)
  ##prevImage = Image.open(ioStream)
  while True:
    stopAll()
    distance = 6

    if distance > 5:
      if mode in "color":
        print "hi"
        #Take photo to process
        with picamera.PiCamera() as camera:
          camera.resolution = (320,240)
          camera.capture(ioStream, format = 'jpeg')
        ioStream.seek(0)
        image = Image.open(ioStream)
        print 'photo taken'
        #Process photo, split into cells, check differences in color.
        #Choose direction
        #Set motors to go in that direction.
        ratio = getDarkestSquare(image, 40)
        print ratio
        moveMotors(getDirection(ratio))
        #Repeat every second.
      elif mode in "motion":
        print "hi"
        #Get first photo.
        with picamera.PiCamera() as camera:
          camera.resolution = (320,240)
          camera.capture(ioStream, format = 'jpeg')
        ioStream.seek(0)
        prevImage = Image.open(ioStream)
        prevImage.save("a.jpg")
        #Wait a bit.
        time.sleep(.1)
        #Get the next photo.
        ioStream.seek(0)
        with picamera.PiCamera() as camera:
          camera.resolution = (320,240)
          camera.capture(ioStream, format = 'jpeg')
        ioStream.seek(0)
        currentImage = Image.open(ioStream)
        currentImage.save("b.jpg")
        #Split into cells and compare cells with prevImage
        #Choose direction
        (Moving, ratio) = getMostDifferentSquare(prevImage, currentImage, 40)
        if (Moving):
          #getDirection
          #Set motors to go in that direction
          moveMotors(getDirection(ratio))
        #Repeat every second.
        else:
          print "No movement"
      elif mode in "basket":
        print "hi"
        #Get first photo.
        with picamera.PiCamera() as camera:
          camera.resolution = (320,240)
          camera.capture(ioStream, format = 'jpeg')
        ioStream.seek(0)
        image = Image.open(ioStream)
        #image.save("Tennis.jpg")
        #process photo, split into cells, check differences in color
        #Choose direction
        #Set motors to go in that direction
        ratio = getSpecificSquare(image, 40)
        print ratio
        moveMotors(getDirection(ratio))
        #Repeat every second

      if mode in "combined":
        print "hi"
        #Take photo.
        #Split image into cells, compare cells with prevImage.
        #process photo, binarize, split into cells, check differences in color.
        #Choose direction.
        #Set motors to go in that direction.
        #Repeat every second.
    else:
      rightTurn()

    time.sleep(1)

except KeyboardInterrupt:
       Going = False
       GPIO.cleanup()
       sys.exit()
