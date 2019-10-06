from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from LayerBitmap import LayerBitmap
from LayerViewListScroll import LayerViewListScroll
from LayerListToolbar import LayerListToolbar

class LayerListWidget(QWidget):
	def __init__(self, layers, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.listView = LayerViewListScroll(layers=layers)
		self.toolbar = LayerListToolbar()
		
		self.onNewBitmapClicked = self.toolbar.newBitmapButton.clicked
		self.onLayerSelectionChanged = self.listView.layerViewList.onSelectionChanged
		self.onDeleteLayer = self.listView.layerViewList.onDeleteLayer
		
		layout = QVBoxLayout()
		layout.addWidget(self.listView)
		layout.addWidget(self.toolbar)
		self.setLayout(layout)
	
	def layerAdded(self, idx: int, layer: LayerBitmap):
		self.listView.updateLayers()
		self.listView.setLayerSelection(idx)
		
	def layerDeleted(self, layer: LayerBitmap):
		self.listView.updateLayers()