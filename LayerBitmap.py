import numpy as np

class LayerBitmap:
	def __init__(self, width: int, height: int):
		self.mask = np.zeros((width, height), dtype=np.uint8)
		self.label = "This is the layer label"
		self.visible = True
		