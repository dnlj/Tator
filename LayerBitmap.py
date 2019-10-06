import random
import numpy as np

from PyQt5.QtGui import QColor

from Listenable import Listenable

nextRand = random.random()
goldenRatioConjugate = ((5 ** 0.5) - 1) / 2

def randColor():
	global nextRand
	global goldenRatioConjugate
	
	color = QColor()
	color.setHsvF(nextRand, 0.5, 1.0, 0.65)
	nextRand += goldenRatioConjugate
	nextRand %= 1
	return color.rgba()

class LayerBitmap:
	def __init__(self, width: int, height: int):
		self.mask = np.zeros((width, height), dtype=np.uint8)
		self.label = Listenable("") # TODO: change to using indexes into the "global" list
		self.visible = Listenable(True)
		self.color = randColor() # TODO: change to use color associated with global label list
		