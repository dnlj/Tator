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
	onDelete = pyqtSignal([])
	
	def __init__(self, layer, labels, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.layer = layer
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		# Visibility toggle checkbox
		visBox = QCheckBox() # TODO: Custom eye icons?
		visBox.setCheckState(Qt.Checked if layer.visible.value else Qt.Unchecked)
		visBox.stateChanged.connect(self.onStateChanged)
		layout.addWidget(visBox)
		
		# TODO: Layer Preview
		
		# Layer label dropdown
		dropdown = ComboBoxNoScroll()
		try:
			labelIdx = labels.index(layer.label.value)
		except ValueError:
			labels.append(layer.label.value)
			labelIdx = len(labels) - 1
		for label in labels:
			dropdown.addItem(label)
		dropdown.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
		dropdown.setCurrentIndex(labelIdx)
		def onDropdownChanged(label): layer.label.value = label
		dropdown.currentTextChanged.connect(onDropdownChanged)
		layout.addWidget(dropdown)
		
		# Layer type icon
		layout.addWidget(QLabel("[B]")) # TODO: Icon
		
		# Delete layer button
		self.deleteButton = QPushButton("-")
		self.deleteButton.clicked.connect(lambda: self.onDelete.emit())
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
		