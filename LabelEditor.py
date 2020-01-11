from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from LabelWidget import LabelWidget

class LabelEditor(QScrollArea):
	def __init__(self, labels, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent)
		self.setWindowFlags(flags)
		
		layout = QVBoxLayout()
		self.setLayout(layout)
		self.setWindowTitle("Label Editor")
		self.setMinimumSize(256, 0)
		
		for label in labels:
			layout.addWidget(LabelWidget(label))
		