from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from Listenable import Listenable

class ColorButton(QPushButton):
	def __init__(self, color=0, parent=None):
		super().__init__(parent=parent)
		self.onColorChanged = Listenable()
		self.setColor(color)
		self.clicked.connect(self.clicked_callback)
		
	def clicked_callback(self):
		color = QColorDialog.getColor(
			initial=self.color,
			options=QColorDialog.DontUseNativeDialog
		)
		if color.isValid():
			self.setColor(color.rgba())
				
	def setColor(self, color):
		self.color = QColor(color)
		self.onColorChanged.notify(color)
		
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
		nameButton.onLabelChanged.addListener(self.onNameChanged_callback)
		layout.addWidget(nameButton)
		self.onNameChanged = nameButton.onLabelChanged
		
		# TODO: move edit functionality into color button
		colorButton = ColorButton(cat["color"])
		colorButton.onColorChanged.addListener(self.onColorChanged_callback)
		layout.addWidget(colorButton)
		self.onColorChanged = colorButton.onColorChanged
		
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
		
		# TODO: Delete button (make sure you check that no annotations use this labl before deleting)
		# TODO: edit name
		
	def onNameChanged_callback(self, name):
		self.cat["name"] = name
		
	def onColorChanged_callback(self, color):
		self.cat["color"] = color
	