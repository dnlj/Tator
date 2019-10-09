from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class ThumbnailModel(QAbstractListModel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.image = QPixmap("data/test.jpg")
		
	def rowCount(self, parent=QModelIndex()):
		return 1000
		
	def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
		if role == Qt.DecorationRole:
			return self.image

# https://www.qtcentre.org/threads/33751-QListView-of-images
# https://doc.qt.io/qt-5/qtwidgets-itemviews-fetchmore-example.html
# https://doc.qt.io/qt-5/qabstractlistmodel.html#details
class ThumbnailList(QListView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setModel(ThumbnailModel())
		self.setViewMode(QListView.IconMode)
		self.setGridSize(QSize(192, 192)) # TODO: can we just make this scale to widget's short dimension (usually width)?
		# TODO: if we are width > height we probably want to switch to left to right
		self.setFlow(QListView.TopToBottom)
		self.setWrapping(False)
		self.setUniformItemSizes(True) # This is an optimization hint. It does not force items to have the same size. It is up to us to enforce this.
