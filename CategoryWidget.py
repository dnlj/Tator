from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from Listenable import Listenable

class ColorButton(QPushButton):
	def __init__(self, color=0, parent=None):
		super().__init__(parent=parent)
		self.setColor(color)
		
	def setColor(self, color):
		self.color = QColor(color)
		
	def paintEvent(self, event: QPaintEvent):
		painter = QPainter(self)
		painter.fillRect(0, 0, self.width(), self.height(), self.color)
	
class EditableButton(QPushButton):
	def __init__(self, label, parent=None):
		super().__init__(parent=parent)
		self.onLabelChanged = Listenable()
		
		layout = QGridLayout()
		layout.setContentsMargins(0, 0, 0, 0)
		self.setLayout(layout)
		
		self.setText(label)
		self.clicked.connect(self.editBegin)
		
		self.lineEdit = QLineEdit()
		self.lineEdit.setAlignment(Qt.AlignCenter)
		self.lineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.lineEdit.textEdited.connect(self.editing)
		self.lineEdit.editingFinished.connect(self.editFinished)
		self.lineEdit.hide()
		layout.addWidget(self.lineEdit)
		
	def editBegin(self):
		self.lineEdit.setText(self.text())
		self.lineEdit.show()
		self.lineEdit.setFocus(Qt.OtherFocusReason)
		
	def editing(self, text):
		self.setText(text)
		self.update()
		
	def editFinished(self):
		self.lineEdit.hide()
		self.onLabelChanged.notify(self.text())
		
		
class CategoryWidget(QWidget):
	def __init__(self, cat, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.cat = cat
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		nameButton = EditableButton(cat["name"])
		layout.addWidget(nameButton)
		nameButton.onLabelChanged.addListener(self.setName)
		
		# TODO: move edit functionality into color button
		self.colorButton = ColorButton(cat["color"])
		def colorButtonCallback():
			color = QColorDialog.getColor(
				initial=QColor(self.cat["color"]),
				options=QColorDialog.DontUseNativeDialog
			)
			if color.isValid():
				self.setColor(color.rgba())
		self.colorButton.clicked.connect(colorButtonCallback)
		layout.addWidget(self.colorButton)
		
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		
		# TODO: Delete button (make sure you check that no annotations use this labl before deleting)
		# TODO: edit name
		
	def setName(self, name):
		self.cat["name"] = name
		
	def setColor(self, color):
		self.cat["color"] = color
		self.colorButton.setColor(color)
		self.update()
	