from binder import *

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from PIL import Image, ImageDraw

class ActionFill():
	def __init__(self, mask: QImage):
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("fill",
			inputs=[(Input(InputType.MOUSE, Qt.LeftButton), lambda e : e[0])],
		))
		self.binds.addListener("fill", BindEvent.PRESS, self.pressFill)
		
		self.mask = mask
		
	def pressFill(self, inp: Input, val, inputs):
		# TODO: this takes seconds. Try doing manually
		ImageDraw.floodfill(self.mask, (val[1].x(), val[1].y()), (0,255,0))
	
	# TODO: make base class so we dont need this
	def drawHints(self, canvas, target):
		pass