from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

from CategoryWidget import CategoryWidget
from Listenable import Listenable

class CategoryList(QWidget):
	def __init__(self, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.cats = cats
		self.onCategoryChanged = Listenable()
		self.layout = QVBoxLayout()
		self.layout.setContentsMargins(0, 0, 0, 0) # TODO: Can we control this on a application level? intead of per widget?
		self.setLayout(self.layout)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.updateCategories()
		
	def updateCategories(self):
		while self.layout.count():
			self.layout.takeAt(0).widget().deleteLater()
		for cat in self.cats:
			widget = CategoryWidget(cat)
			widget.onCategoryChanged.addListener(lambda: self.onCategoryChanged.notify())
			self.layout.addWidget(widget)
			
		
class CategoryListScroll(QScrollArea):
	def __init__(self, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent)
		self.setWindowFlags(flags)
		self.catList = CategoryList(cats)
		self.onCategoryChanged = self.catList.onCategoryChanged
		self.setWidget(self.catList)
		
		self.setFrameShape(QFrame.NoFrame)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setWidgetResizable(True)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		
	def updateCategories(self):
		self.catList.updateCategories()
	
class CategoryEditor(QWidget):
	def __init__(self, cats, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.onCategoryAdded = Listenable()
		self.cats = cats
		self.setWindowTitle("Category Editor")
		self.setMinimumSize(256, 0)
		
		layout = QVBoxLayout()
		self.setLayout(layout)
		
		# TODO: notify label updated (color/name changed)
		
		self.catList = CategoryListScroll(cats)
		self.onCategoryChanged = self.catList.onCategoryChanged
		layout.addWidget(self.catList)
		
		addCategoryButton = QPushButton("Add Category")
		addCategoryButton.clicked.connect(lambda: self.addCategory("label " + str(len(cats)), QColor("#000").rgba()))
		layout.addWidget(addCategoryButton)
		
		self.updateCategories()
		
	def addCategory(self, name, color):
		cat = {
			"id": len(self.cats),
			"name": name,
			"color": color,
		}
		self.cats.append(cat)
		self.updateCategories()
		self.onCategoryAdded.notify(cat)
		
	def updateCategories(self):
		self.catList.updateCategories()