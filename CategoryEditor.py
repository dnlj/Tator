from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from CategoryWidget import CategoryWidget
from Listenable import Listenable

class CategoryList():
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
	
class CategoryEditor(QWidget):
	def __init__(self, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.onCategoryAdded = Listenable()
		self.cats = cats
		#self.setWindowFlags(flags)
		self.setWindowTitle("Category Editor")
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
		
		addCategoryButton = QPushButton("Add Category")
		addCategoryButton.clicked.connect(lambda: self.addCategory("test1", 0))
		layout.addWidget(addCategoryButton)
		
	def addCategory(self, name, color):
		cat = {
			"id": len(self.cats),
			"name": name,
			"color": color,
		}
		self.cats.append(cat)
		self.updateLabels()
		self.onCategoryAdded.notify(cat)
		
	def updateLabels(self):
		while self.scrollLayout.count():
			self.scrollLayout.takeAt(0).widget().deleteLater()
		for cat in self.cats:
			self.scrollLayout.addWidget(CategoryWidget(cat))