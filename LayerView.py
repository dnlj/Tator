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
	
	def __init__(self, layer, cats, parent=None, flags=Qt.WindowFlags()):
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
		for cat in cats:
			dropdown.addItem(cat["name"], cat["id"])
		dropdown.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
		dropdown.setCurrentIndex(layer.label.value)
		# TODO: we need to listen for this somewhere to update the layers (bgcolor)
		def onDropdownChanged(idx): layer.label.value = dropdown.itemData(idx)
		dropdown.currentIndexChanged.connect(onDropdownChanged)
		layout.addWidget(dropdown)
		
		# Layer type icon
		layout.addWidget(QLabel("[B]")) # TODO: Icon
		
		# Delete layer button
		self.deleteButton = QPushButton("-")
		self.deleteButton.clicked.connect(lambda: self.onDelete.emit())
		layout.addWidget(self.deleteButton)
		
		# Setup style
		self.setProperty("is-selected", False)
		bgColor = QColor(cats[layer.label.value]["color"])
		self.setStyleSheet( # TODO: move stylesheets into files?
			f"""
			LayerView {{
				background: {bgColor.name()};
			}}
			
			LayerView[is-selected=true] {{
				border: 0.5em solid rgba(0, 0, 0, 0.4);
			}}
			
			LayerView:hover {{
				border: 0.5em solid rgba(0, 0, 0, 0.6);
			}}
			""")
		
	# TODO: Needed for stylesheet support? what does this do exactly?
	def paintEvent(self, event: QPaintEvent):
		opt = QStyleOption()
		opt.initFrom(self)
		painter = QPainter(self)
		self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
		
	def onStateChanged(self, state: Qt.CheckState):
		self.layer.visible.value = bool(state) # TODO: how force EditArea to redraw
		
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton: # TODO: Change to bind system
			self.onClicked.emit(self)
			
	def setSelected(self, value: bool):
		self.setProperty("is-selected", value)
		self.style().unpolish(self)
		self.style().polish(self)
		