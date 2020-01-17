from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class ColorButton(QPushButton):
	def __init__(self, color=0, parent=None):
		super().__init__(parent=parent)
		self.setColor(color)
		
	def setColor(self, color):
		self.color = QColor(color)
		
	def paintEvent(self, event: QPaintEvent):
		painter = QPainter(self)
		painter.fillRect(0, 0, self.width(), self.height(), self.color)
		

# TODO: Label or category? what term does coco use?
class LabelWidget(QWidget):
	def __init__(self, label, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.label = label
		
		layout = QHBoxLayout()
		self.setLayout(layout)
		
		layout.addWidget(QLabel(label["name"]))
		
		self.colorButton = ColorButton(label["color"])
		self.colorButton.clicked.connect(lambda: self.setColor(QColorDialog.getColor(options=QColorDialog.DontUseNativeDialog).rgba()))
		layout.addWidget(self.colorButton)
		
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		
		# TODO: Delete button (make sure you check that no annotations use this labl before deleting)
		# TODO: edit name
		
	def setColor(self, color):
		self.label["color"] = color
		self.colorButton.setColor(color)
		self.update()
		
	#def sizeHint(self):
		#return QSize(25,25)
	