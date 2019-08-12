from binder import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class ActionBrush():
	def __init__(self, mask: QImage):
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
		self.brushSize = 20
		self.configure()
		
		self.oldPos = QPoint()
		self.curPos = QPoint()
		
	def configure(self):
		self.pen = QPen(Qt.red, self.brushSize * 2, cap = Qt.RoundCap, join = Qt.RoundJoin)
		self.brush = QBrush(Qt.red)
		
	def pressDraw(self, inp: Input, val, inputs):
		self.oldPos = val[1]
		self.curPos = val[1]
		self.apply(QPainter.CompositionMode_SourceOver)
		
	def triggerDraw(self, inp: Input, val, inputs):
		self.oldPos = self.curPos
		self.curPos = val[1]
		self.apply(QPainter.CompositionMode_SourceOver)
		
	def pressErase(self, inp: Input, val, inputs):
		self.oldPos = val[1]
		self.curPos = val[1]
		self.apply(QPainter.CompositionMode_Clear)
		
	def triggerErase(self, inp: Input, val, inputs):
		self.oldPos = self.curPos
		self.curPos = val[1]
		self.apply(QPainter.CompositionMode_Clear)
		
	def triggerResize(self, inp: Input, val, inputs):
		self.brushSize = max(1, self.brushSize + val)
		self.configure()
		
	def apply(self, comp: QPainter.CompositionMode):
		painter = QPainter(self.mask)
		painter.setCompositionMode(comp)
		if self.oldPos == self.curPos:
			painter.setBrush(self.brush)
			painter.setPen(Qt.NoPen)
			painter.drawEllipse(self.curPos, self.brushSize, self.brushSize)
		else:
			painter.setBrush(Qt.NoBrush)
			painter.setPen(self.pen)
			painter.drawLine(self.oldPos, self.curPos)
			
	def drawHints(self, canvas: QImage, target: QPoint):
		painter = QPainter(canvas)
		painter.setBrush(Qt.NoBrush)
		painter.drawEllipse(target, self.brushSize, self.brushSize)