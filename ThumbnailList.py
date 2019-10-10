from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *


class ThumbnailModel(QAbstractListModel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.image = QPixmap("data/test4.jpg")
		
	def rowCount(self, parent=QModelIndex()):
		return 200
		
	def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
		if role == Qt.DecorationRole:
			return self.image
			
class ThumbnailDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
		#return super().paint(painter, option, index)
		# TODO: dont forget to draw option.state
		# TODO: look into QStyle to draw selection
		# TODO: need to work out aspect ratio math again...
		pixm = index.data(Qt.DecorationRole)
		painter.drawPixmap(option.rect, pixm, pixm.rect())


# https://www.qtcentre.org/threads/33751-QListView-of-images
# https://doc.qt.io/qt-5/qtwidgets-itemviews-fetchmore-example.html
# https://doc.qt.io/qt-5/qabstractlistmodel.html#details
class ThumbnailList(QListView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.setViewMode(QListView.IconMode)
		self.setUniformItemSizes(True) # This is an optimization hint. It does not force items to have the same size. It is up to us to enforce this.
		self.setFlow(QListView.TopToBottom) # TODO: if we are width > height we probably want to switch to left to right
		self.setWrapping(False)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.setMovement(QListView.Static)
		self.setGridSize(QSize(192, 192))
		self.setItemDelegate(ThumbnailDelegate())
		self.setModel(ThumbnailModel())
		
		# TODO: data just add them to a queue and check visualRect before loading to see if it is in view
		
	def getSizeExtras(self):
		ext = QSize(self.frameWidth(), self.frameWidth()) * 2
		vscroll = self.verticalScrollBar()
		ext.setWidth(ext.width() + vscroll.sizeHint().width())
		return ext
		
	def resizeEvent(self, event: QResizeEvent):
		self.setGridSize(QSize(event.size().width(), event.size().width()))
		
	def sizeHint(self):
		return self.gridSize() + self.getSizeExtras()
