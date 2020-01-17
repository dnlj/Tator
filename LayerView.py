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
		self.cats = cats
		self.updatingCategories = False
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Preferred)
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		# Visibility toggle checkbox
		visBox = QCheckBox() # TODO: Custom eye icons?
		visBox.setCheckState(Qt.Checked if layer.visible.value else Qt.Unchecked)
		visBox.stateChanged.connect(self.callback_onVisibilityChanged)
		layout.addWidget(visBox)
		
		# TODO: Layer Preview
		
		# Layer label dropdown
		self.dropdown = ComboBoxNoScroll()
		self.dropdown.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Maximum)
		self.dropdown.currentIndexChanged.connect(self.callback_onDropdownChanged)
		self.updateCategories()
		layout.addWidget(self.dropdown)
		
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
	
	def callback_onDropdownChanged(self, idx):
		# TODO: we need to listen for this somewhere to update the layers (bgcolor)
		if not self.updatingCategories:
			self.layer.label.value = self.dropdown.itemData(idx)
		
	def callback_onVisibilityChanged(self, state: Qt.CheckState):
		self.layer.visible.value = bool(state)
		
	def updateCategories(self):
		self.updatingCategories = True
		self.dropdown.clear()
		for cat in self.cats:
			self.dropdown.addItem(cat["name"], cat["id"])
		self.dropdown.setCurrentIndex(self.layer.label.value)
		self.update()
		self.updatingCategories = False
			
	# TODO: Needed for stylesheet support? what does this do exactly?
	def paintEvent(self, event: QPaintEvent):
		opt = QStyleOption()
		opt.initFrom(self)
		painter = QPainter(self)
		self.style().drawPrimitive(QStyle.PE_Widget, opt, painter, self)
		
	def mousePressEvent(self, event):
		if event.button() == Qt.LeftButton: # TODO: Change to bind system
			self.onClicked.emit(self)
			
	def setSelected(self, value: bool):
		self.setProperty("is-selected", value)
		self.style().unpolish(self)
		self.style().polish(self)
		