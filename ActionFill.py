from binder import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class ActionBrush():
	def __init__(self, mask: QImage):
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("fill",
			inputs=[(Input(InputType.MOUSE, Qt.LeftButton), lambda e : e[0])],
		))
		self.binds.addListener("fill", BindEvent.PRESS, self.pressFill)
		
		self.mask = mask
		self.brushSize = 20
		self.configure()
		
		self.oldPos = QPoint()
		self.curPos = QPoint()
		
	def configure(self):
		self.pen = QPen(Qt.red, self.brushSize * 2, cap = Qt.RoundCap, join = Qt.RoundJoin)
		self.brush = QBrush(Qt.red)
		
	def pressFill(self, inp: Input, val, inputs):
		self.oldPos = val[1]
		self.curPos = val[1]
		self.apply(QPainter.CompositionMode_SourceOver)
		
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