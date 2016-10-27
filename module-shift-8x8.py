import RPi.GPIO as GPIO
import time
from threading import Thread,Timer
from copy import copy, deepcopy

class LedMatrix(Thread):
        def __init__(self, rows, columns, shiftDelay=0, shiftDirection=0):
                self._rows = rows
                self._columns = columns
                self._shiftRegister = ShiftRegister(rows + columns, 37, 35, 33)
                self._run = True
                self._hexaMatrix = [[0 for x in range(self._columns)] for y in range (self._rows)]
                self._shiftRegisterCoordinates = [[0 for x in range(self._columns + self._rows)] for y in range (self._rows)]

                #if shiftDelay then a new thread for shifting the screen pattern is created and started
                if shiftDelay > 0:
                        self._shiftThread = Thread(target=self._shiftWorker)
                        self._shiftDelay = shiftDelay
                        self._shiftThread.daemon = True
                        self._shiftThread.start()

                Thread.__init__(self)
                self.daemon = True
                self.start()

        #Main method
        #Loop infinitely through rows in the screen matrix, and passes each one to the shift register, to be displayed as fast as possible
        #Private method, not to be called from outside
        def run(self):
                while (self._run):
                        for i in range(self._rows):
                                matrixCoordinates = self._shiftRegisterCoordinates[i]
                                self._shiftRegister.set(matrixCoordinates)                

        def _convertMatrixToShiftRegisterCoordinates(self, grid):
                srCoordinates = []

                for i in range(self._rows):
                        srCoordinates.append(self._convertLineToMatrixCoordinates(self._hexaMatrix[i], i))

                return srCoordinates

        #gently stops threads
        def stop(self):
                self._run = False
                self.join(2)

	#main entry point (meant to be called from the outside) for displaying a new pattern on the screen
        def draw(self, hexaMatrix):
                print ('Drawing new pattern on matrix ')
                self._hexaMatrix = hexaMatrix
                self._shiftRegisterCoordinates = self._convertMatrixToShiftRegisterCoordinates(hexaMatrix)

        #shift method
        #meant to be called in its own thread
        #executes infinitely until script shutdowns
        def _shiftWorker(self):
                while (self._run):
                        time.sleep(self._shiftDelay)
                        self.shift()

        #method from shifting screen pattern 1px right
        def shift(self):
                matrix = deepcopy(self._hexaMatrix)
                for y in range(self._rows):
                        line = matrix[y]
                        originalLine =  self._hexaMatrix[y]
                        for x in range(self._columns):
                                if x == 0:
                                        line[x] = originalLine[self._columns - 1]
                                else:
                                        line[x] = originalLine[x - 1]
                        
                        matrix[y] = line

                self.draw(matrix)
        
        def _convertLineToMatrixCoordinates(self, line=[], row=0):
                if len(line) != self._columns:
                        print ('Invalid line length specified value is ' + str(len(line)) + ' but matrix has ' + str(self._columns) + ' columns')          
                
                grid = [0] * (self._rows + self._columns)
                grid[row] = 1

                for i in range(self._columns):
                        if line[i] == 0:
                                grid[self._rows + i] = 1
                        else:
                                grid[self._rows + i] = 0

                return grid

class ShiftRegister:
	def __init__(self, length, serPin, registerClockPin, shiftClockPin):
		self.length = length
		self.serPin = serPin
		self.registerClockPin = registerClockPin
		self.shiftClockPin = shiftClockPin
		GPIO.setup(self.serPin, GPIO.OUT)
		GPIO.setup(self.registerClockPin, GPIO.OUT)
		GPIO.setup(self.shiftClockPin, GPIO.OUT)
		print ('Initialized Shift Register of size ' + str(length))
	def shiftLeft(self):
		v = self.values[:]
		for i in range (0, self.length):
			if i == self.length - 1:
				v[i] = self.values[0]
			else:
				v[i] = self.values[i+1]
		self.set(v)
	def shiftRight(self):
		v = self.values[:]
		for i in range (0, self.length):
			if i == 0:
				v[i] = self.values[self.length - 1]
			else:
				v[i] = self.values[i-1]
		self.set(v)
	def off(self):
		val = [0] * self.length
		self.set(val)
	def on(self):
                val = [1] * self.length
                self.set(val)
	def set(self, valeurs = []):
		if len(valeurs) != self.length:
			print ('Invalid register length')
			return

		self.values = valeurs[:]
		self.values.reverse()

		#Don't commit changes
		GPIO.output(self.registerClockPin, False)

		for valeur in self.values:
			GPIO.output(self.shiftClockPin, False)
			if valeur > 0:
				GPIO.output(self.serPin, True)
			else:	
				GPIO.output(self.serPin, False)

			GPIO.output(self.shiftClockPin, True)

		#Commit changes
		GPIO.output(self.registerClockPin, True)

try:
        GPIO.setmode(GPIO.BOARD)
        ledDisplay = LedMatrix(8,8,0.5)
        ledDisplay.draw([[0,0,0,0,0,0,0,0],[0,1,1,0,0,1,1,0],[0,1,1,0,0,1,1,0],[0,1,1,1,1,1,1,0],[0,1,1,1,1,1,1,0],[0,1,1,0,0,1,1,0],[0,1,1,0,0,1,1,0],[0,0,0,0,0,0,0,0]])
        GPIO.setup(18, GPIO.OUT)
        GPIO.output(18, True)
        
        print ('Display started')

        while True:
                time.sleep(1)

except KeyboardInterrupt:
        print ('Display interrupted')
        ledDisplay.stop()
        GPIO.output(18, False)
        GPIO.cleanup()
