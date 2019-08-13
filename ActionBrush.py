from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from PIL import Image, ImageDraw
import numpy as np
import skimage as ski

from binder import *

class ActionBrush():
	def __init__(self, mask: Image):
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("draw",
			inputs=[(Input(InputType.MOUSE, Qt.LeftButton), lambda e : e[0])],
			triggers=[Input(InputType.MOUSE, Qt.NoButton)]
		))
		self.binds.addListener("draw", BindEvent.PRESS, self.pressDraw)
		self.binds.addListener("draw", BindEvent.TRIGGER, self.triggerDraw)
		
		self.binds.addBind(Bind("erase",
			inputs=[(Input(InputType.MOUSE, Qt.RightButton), lambda e : e[0])],
			triggers=[Input(InputType.MOUSE, Qt.NoButton)]
		))
		self.binds.addListener("erase", BindEvent.PRESS, self.pressErase)
		self.binds.addListener("erase", BindEvent.TRIGGER, self.triggerErase)
		
		self.binds.addBind(Bind("resize", inputs=[],
			triggers=[
				Input(InputType.MOUSE_WHEEL),
			]
		))
		self.binds.addListener("resize", BindEvent.TRIGGER, self.triggerResize)
		
		self.mask = mask
		self.brushSize = 40
		
		self.oldPos = QPoint()
		self.curPos = QPoint()
		
	def pressDraw(self, inp: Input, val, inputs):
		self.oldPos = val[1]
		self.curPos = val[1]
		self.apply(255)
		
	def triggerDraw(self, inp: Input, val, inputs):
		self.oldPos = self.curPos
		self.curPos = val[1]
		self.apply(255)
		
	def pressErase(self, inp: Input, val, inputs):
		self.oldPos = val[1]
		self.curPos = val[1]
		self.apply(0)
		
	def triggerErase(self, inp: Input, val, inputs):
		self.oldPos = self.curPos
		self.curPos = val[1]
		self.apply(0)
		
	def triggerResize(self, inp: Input, val, inputs):
		self.brushSize = int(max(1, self.brushSize + val))
		
	def apply(self, value: np.uint8):
		rr, cc = ski.draw.ellipse(
			self.curPos.y(),
			self.curPos.x(),
			self.brushSize / 2,
			self.brushSize / 2,
			self.mask.shape
		)
		
		self.mask[rr, cc] = value
		
		# TODO: Line part
			
	def drawHints(self, canvas: Image, target: QPoint):
		size = self.brushSize // 2
		xyMin = (target.x() - size, target.y() - size)
		xyMax = (target.x() + size, target.y() + size)
		draw = ImageDraw.Draw(canvas)
		draw.ellipse([xyMin, xyMax], outline=(0,0,0))
		del draw