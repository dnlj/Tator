from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from LayerViewList import LayerViewList

class LayerViewListScroll(QScrollArea):
	def __init__(self, cats, parent=None):
		super().__init__(parent=parent)
		
		self.setFrameShape(QFrame.NoFrame)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setWidgetResizable(True)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		self.layerViewList = LayerViewList(cats=cats)
		self.setWidget(self.layerViewList)
		
	def setLayerSelection(self, idx: int):
		self.layerViewList.setLayerSelection(idx)
		
	def sizeHint(self):
		return self.layerViewList.sizeHint() + self.verticalScrollBar().sizeHint()
		
	def updateLayers(self, layers):
		self.layerViewList.updateLayers(layers)
		self.updateGeometry()
		
	def updateCategories(self):
		self.layerViewList.updateCategories()