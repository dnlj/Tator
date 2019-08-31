import random
import numpy as np

class LayerBitmap:
	def __init__(self, width: int, height: int):
		self.mask = np.zeros((width, height), dtype=np.uint8)
		self.label = "This is the layer label"
		self.visible = True
		
		# TODO: Better color generation
		# http://devmag.org.za/2012/07/29/how-to-choose-colours-procedurally-algorithms/
		# https://martin.ankerl.com/2009/12/09/how-to-create-random-colors-programmatically/
		self.color = random.randint(0x99_000000, 0x99_FFFFFF) # AA_RRGGBB
		