import random
import numpy as np

from PyQt5.QtGui import QColor

from ListenableValue import ListenableValue

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
	def __init__(self, layer_id: int, width: int, height: int):
		self.id = layer_id
		self.mask = np.zeros((width, height), dtype=np.uint8)
		self.label = ListenableValue(0)
		self.visible = ListenableValue(True)
	
	def toAnnotation(self, image_id: int):
		ann = {}
		ann["id"] = self.id
		ann["image_id"] = image_id
		ann["category_id"] = self.label.value
		ann["type"] = "rle"
		# TODO: rle data
		ann["data"] = [123, 111, 222, 333, 444, 555, 666]
		return ann
		
	def fromAnnotation(self):
		pass # TODO: impl
		