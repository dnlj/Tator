from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import numpy as np
import skimage as ski

from binder import *
from LayerBitmap import LayerBitmap

class ActionBrush():
	def __init__(self):
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("target", inputs=[],
			triggers=[Input(InputType.MOUSE, Qt.NoButton)]
		))
		self.binds.addListener("target", BindEvent.TRIGGER, self.triggerTarget)
		
		self.binds.addBind(Bind("draw",
			inputs=[(Input(InputType.MOUSE, Qt.LeftButton), lambda e : e[0])],
			triggers=[Input(InputType.MOUSE, Qt.NoButton)]
		))
		self.binds.addListener("draw", BindEvent.PRESS, lambda *a, **k: self.pressDraw(*a, **k, value=255))
		self.binds.addListener("draw", BindEvent.TRIGGER, lambda *a, **k: self.triggerDraw(*a, **k, value=255))
		
		self.modifier = False
		self.binds.addBind(Bind("modifier",
			inputs=[(Input(InputType.KEYBOARD, Qt.Key_Shift), lambda e : e[0])]
		))
		self.binds.addListener("modifier", BindEvent.PRESS, self.pressModifier)
		self.binds.addListener("modifier", BindEvent.RELEASE, self.releaseModifier)
		
		self.binds.addBind(Bind("erase",
			inputs=[(Input(InputType.MOUSE, Qt.RightButton), lambda e : e[0])],
			triggers=[Input(InputType.MOUSE, Qt.NoButton)]
		))
		self.binds.addListener("erase", BindEvent.PRESS, lambda *a, **k: self.pressDraw(*a, **k, value=0))
		self.binds.addListener("erase", BindEvent.TRIGGER, lambda *a, **k: self.triggerDraw(*a, **k, value=0))
		
		self.binds.addBind(Bind("resize", inputs=[],
			triggers=[
				Input(InputType.MOUSE_WHEEL),
			]
		))
		self.binds.addListener("resize", BindEvent.TRIGGER, self.triggerResize)
		
		self.brushRadius = 20
		
		self.oldPos = QPoint()
		self.curPos = QPoint()
		
	def setLayer(self, layer: LayerBitmap):
		# TODO: Check layer type
		self.mask = layer.mask if layer else None
		
	def pressModifier(self, inp: Input, val, inputs):
		self.oldPos = self.curPos
		self.modifier = True
		
	def releaseModifier(self, inp: Input, val, inputs):
		self.modifier = False
		self.oldPos = self.curPos
		
	def triggerTarget(self, inp: Input, val, inputs):
		self.curPos = val[1]
		
	def pressDraw(self, inp: Input, val, inputs, value):
		if not self.modifier:
			self.oldPos = self.curPos
		self.apply(value)
		self.oldPos = self.curPos
		
	def triggerDraw(self, inp: Input, val, inputs, value):
		if not self.modifier:
			self.apply(value)
			self.oldPos = self.curPos
		
	def triggerResize(self, inp: Input, val, inputs):
		self.brushRadius = int(max(1, self.brushRadius + val/40))
	
	# TODO: why is this a member function?
	def drawBrush(self, out, begin, end, rad, value: np.uint8 = 255):
		shape = out.shape
		rr, cc = ski.draw.ellipse(begin[0], begin[1], rad, rad, shape=shape)
		out[rr, cc] = value
		
		if not np.array_equal(begin, end):
			rows = np.empty(4)
			cols = np.empty(4)
			
			rectTan = (end - begin).astype(np.float32)
			mag = np.linalg.norm(rectTan)
			rectTan /= mag
			rectNorm = np.flip(rectTan) * (rad, -rad)
			
			rows[0] = begin[0] + rectNorm[0]
			cols[0] = begin[1] + rectNorm[1]
			
			rows[1] = end[0] + rectNorm[0]
			cols[1] = end[1] + rectNorm[1]
			
			rows[2] = end[0] - rectNorm[0]
			cols[2] = end[1] - rectNorm[1]
			
			rows[3] = begin[0] - rectNorm[0]
			cols[3] = begin[1] - rectNorm[1]
			
			rr, cc = ski.draw.polygon(rows, cols, shape=shape)
			out[rr, cc] = value
			
			rr, cc = ski.draw.ellipse(end[0], end[1], rad, rad, shape=shape)
			out[rr, cc] = value
			
	def apply(self, value: np.uint8):
		begin = np.array([self.curPos.y(), self.curPos.x()])
		end = np.array([self.oldPos.y(), self.oldPos.x()])
		self.drawBrush(self.mask, begin, end, self.brushRadius, value)
			
	def drawHints(self, canvas: QImage, target: QPoint):
		# TODO: Cache hint layer?
		shape = (canvas.height(), canvas.width())
		hints = np.zeros(shape, dtype=np.uint8)
		x = target.x()
		y = target.y()
		rad = self.brushRadius
		
		rr, cc = ski.draw.ellipse(y, x, rad, rad, shape=shape)
		hints[rr, cc] = 255
		
		if rad > 1:
			rad -= 1
			rr, cc = ski.draw.ellipse(y, x, rad, rad, shape=shape)
			hints[rr, cc] = 0
		
		if self.modifier:
			begin = np.array([self.curPos.y(), self.curPos.x()])
			end = np.array([self.oldPos.y(), self.oldPos.x()])
			self.drawBrush(hints, begin, end, self.brushRadius)
		
		with QPainter(canvas) as painter:
			hintsToQt = QImage(hints.data, hints.shape[1], hints.shape[0], QImage.Format_Indexed8)
			hintsToQt.setColorTable([0] * 255 + [qRgba(0,0,0,127)])
			painter.drawImage(0, 0, hintsToQt)
			# TODO: draw line hint
			