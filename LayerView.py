from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class LayerView(QWidget):
	onClicked = pyqtSignal([QWidget])
	
	def __init__(self, layer, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.layer = layer
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		layout.addWidget(QCheckBox()) # TODO: Custom eye icons?
		# TODO: Layer Preview
		layout.addWidget(QLabel(layer.label)) # TODO: Dropdown to select
		layout.addWidget(QLabel("[B]")) # TODO: Icon
		layout.addWidget(QPushButton("-"))
		
		# TODO: override paint? call super().paint ?
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.red)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
		
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton: # TODO: Change to bind system
			self.onClicked.emit(self)
			
	def setSelected(self, value: bool):
		pal = QPalette() # TODO: surely not the best way to handle this. Look into style sheets?
		if value:
			pal.setColor(QPalette.Background, Qt.blue)
		else:
			pal.setColor(QPalette.Background, Qt.red)
		self.setPalette(pal)
		