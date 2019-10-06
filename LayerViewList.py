from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from LayerBitmap import LayerBitmap
from LayerView import LayerView

class LayerViewList(QWidget):
	onSelectionChanged = pyqtSignal([LayerBitmap])
	onDeleteLayer = pyqtSignal([LayerBitmap])
	
	def __init__(self, layers, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.selected = None
		self.layers = layers
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		self.layout.setDirection(QBoxLayout.BottomToTop)
		self.setLayout(self.layout)
		
	def updateLayers(self):
		selectedLayer = self.selected and self.selected.layer or None
		
		while True:
			taken = self.layout.takeAt(0)
			if taken is not None:
				taken.widget().deleteLater()
			else:
				break
		for layer in self.layers:
			layerView = LayerView(layer)
			layerView.onClicked.connect(self.layerViewClicked)
			layerView.onDelete.connect(lambda: self.onDeleteLayer.signal(layer)) # TODO: this is wrong
			self.layout.addWidget(layerView)
			if layer is selectedLayer:
				self.setLayerSelection(layerView)
				
	def layerViewClicked(self, layerView: LayerView):
		self.setLayerSelection(layerView)
		
	def setLayerSelection(self, layer):
		layerView = None
		
		if isinstance(layer, int):
			layerView = self.layout.itemAt(layer).widget()
		elif isinstance(layer, LayerView):
			layerView = layer
		else:
			raise Exception("Unhandled type")
			
		if self.selected:
			self.selected.setSelected(False)
		self.selected = layerView
		self.selected.setSelected(True)
		self.onSelectionChanged.emit(layerView.layer)