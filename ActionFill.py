from binder import *

import numpy as np
import skimage as ski
import skimage.segmentation as skis

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class ActionFill():
	def __init__(self, mask: QImage):
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("fill",
			inputs=[(Input(InputType.MOUSE, Qt.LeftButton), lambda e : e[0])],
		))
		self.binds.addListener("fill", BindEvent.PRESS, self.pressFill)
		
		self.mask = mask
		
	def pressFill(self, inp: Input, val, inputs):
		skis.flood_fill(self.mask, (val[1].y(), val[1].x()), 255, inplace=True)
	
	# TODO: make base class so we dont need this
	def drawHints(self, canvas, target):
		pass