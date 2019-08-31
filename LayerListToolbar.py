from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class LayerListToolbar(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
		
		layout = QHBoxLayout()
		layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		
		self.newBitmapButton = QPushButton("New Bitmap")
		layout.addWidget(self.newBitmapButton)
		
		layout.addWidget(QPushButton("New Vector"))
		
		self.setLayout(layout)
		
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.green)
		self.setAutoFillBackground(True)
		self.setPalette(pal)