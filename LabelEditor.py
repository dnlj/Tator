from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from LabelWidget import LabelWidget
from Listenable import Listenable

class LabelEditor(QWidget):
	def __init__(self, labels, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.onLabelAdded = Listenable()
		self.labels = labels
		#self.setWindowFlags(flags)
		self.setWindowTitle("Label Editor")
		self.setMinimumSize(256, 0)
		
		layout = QVBoxLayout()
		self.setLayout(layout)
		
		# TODO: notify label updated (color/name changed)
		
		# TODO: get scroll working
		self.scrollPanel = QScrollArea()
		self.scrollLayout = QVBoxLayout()
		self.scrollPanel.setLayout(self.scrollLayout)
		layout.addWidget(self.scrollPanel)
		
		self.updateLabels()
		
		addLabelButton = QPushButton("Add Label")
		addLabelButton.clicked.connect(lambda: self.addLabel("test1", 0))
		layout.addWidget(addLabelButton)
		
	def addLabel(self, name, color):
		label = {
			"id": len(self.labels),
			"name": name,
			"color": color,
		}
		self.labels.append(label)
		self.updateLabels()
		self.onLabelAdded.notify(label)
		
	def updateLabels(self):
		while self.scrollLayout.count():
			self.scrollLayout.takeAt(0).widget().deleteLater()
		for label in self.labels:
			self.scrollLayout.addWidget(LabelWidget(label))