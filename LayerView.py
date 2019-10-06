from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

# TODO: Move
class ComboBoxNoScroll(QComboBox):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setFocusPolicy(Qt.StrongFocus)
		
	def wheelEvent(self, event: QWheelEvent):
		return self.parent().wheelEvent(event)
		
class LayerView(QWidget):
	onClicked = pyqtSignal([QWidget])
	
	def __init__(self, layer, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.layer = layer
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		visBox = QCheckBox() # TODO: Custom eye icons?
		visBox.setCheckState(Qt.Checked if layer.visible.value else Qt.Unchecked)
		visBox.stateChanged.connect(self.onStateChanged) # TODO: impl
		layout.addWidget(visBox)
		
		# TODO: Layer Preview
		
		# TODO: implement functionality
		dropdown = ComboBoxNoScroll() # TODO: how to populate?
		dropdown.addItem("")
		dropdown.addItem("label 1")
		dropdown.addItem("label 2")
		dropdown.addItem("label 3")
		dropdown.addItem("label 4")
		dropdown.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
		layout.addWidget(dropdown)
		
		layout.addWidget(QLabel("[B]")) # TODO: Icon
		
		self.deleteButton = QPushButton("-")
		self.onDelete = self.deleteButton.clicked
		layout.addWidget(self.deleteButton)
		
		# TODO: override paint? call super().paint ?
		pal = QPalette()
		pal.setColor(QPalette.Background, Qt.red)
		self.setAutoFillBackground(True)
		self.setPalette(pal)
	
	def onStateChanged(self, state: Qt.CheckState):
		self.layer.visible.value = bool(state) # TODO: how force EditArea to redraw
		
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
		