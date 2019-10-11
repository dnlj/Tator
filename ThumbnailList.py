from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import queue

class ThumnailLazy():
	def __init__(self, valid: bool = False, pixmap: QPixmap = None):
		self.valid = valid
		self.pixmap = pixmap

# TODO: for placeholder loading look into https://doc.qt.io/qt-5/qabstractitemmodel.html#dataChanged
class ThumbnailModel(QAbstractListModel):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.image = QPixmap("data/test4.jpg")
		self.cache = {} # TODO: how to clear old?
		self.queue = queue.Queue() # TODO: process queue and update cache[i].valid
	
	def rowCount(self, parent=QModelIndex()):
		return 200000
		
	def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
		if role == Qt.DecorationRole:
			if not index in self.cache:
				self.cache[index] = ThumnailLazy(False, self.image)
				self.queue.put(self.cache[index])
			return self.cache[index]
		#elif role == Qt.SizeHintRole:
		#	# Take as much space a possible
		#	return QSize(2**16, 2**16) # If this number is to large it breaks scrolling.
			
class ThumbnailDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		self.poly = QPolygonF([
			QPointF(0, 1),
			QPointF(0.5, 0.5),
			QPointF(1, 1),
			QPointF(0, 1),
		])
		self.lastScale = (1, 1)
		self.polyCache = self.poly
		self.itemSize = 0
		
	def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex):
		# TODO: dont forget to draw option.state
		# TODO: look into QStyle to draw selection
		data = index.data(Qt.DecorationRole)
		o = option.rect
		print(o)
		print(option.decorationSize)
		if data.valid:
			pixm = data.pixmap
			p = pixm.rect()
			
			scale = min(o.width() / p.width(), o.height() / p.height())
			size = p.size() * scale
			offset = (o.size() - size)/2
			offset = QPoint(offset.width(), offset.height())
			new = QRect(o.topLeft() + offset, size)
			painter.drawPixmap(new, pixm, pixm.rect())
		else:
			painter.save()
			## TODO: Look into QStyle src: `QStyle *style = widget ? widget->style() : QApplication::style();`
			painter.setBrush(Qt.red)
			painter.drawRect(o)
			painter.setBrush(Qt.blue)
			w = o.width()
			h = o.height()
			if not self.lastScale == (w, h):
				trans = QTransform().translate(o.left(), o.top()).scale(w, h)
				self.polyCache = trans.map(self.poly)
			painter.drawConvexPolygon(self.polyCache)
			painter.restore()
			
	def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex):
		return QSize(self.itemSize, self.itemSize)

# https://www.qtcentre.org/threads/33751-QListView-of-images
# https://doc.qt.io/qt-5/qtwidgets-itemviews-fetchmore-example.html
# https://doc.qt.io/qt-5/qabstractlistmodel.html#details
class ThumbnailList(QListView):
	def __init__(self, parent=None):
		super().__init__(parent=parent)
		# TODO: Look into lazy loading. I though that was the whole point of ListView...
		self.setViewMode(QListView.IconMode)
		self.setUniformItemSizes(True) # This is an optimization hint. It does not force items to have the same size. It is up to us to enforce this.
		self.setFlow(QListView.TopToBottom) # TODO: if we are width > height we probably want to switch to left to right
		self.setWrapping(False)
		#self.setSizeAdjustPolicy(QListView.AdjustToContents)
		self.setResizeMode(QListView.Adjust)
		self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)
		self.setMovement(QListView.Static)
		#self.setGridSize(QSize(128, 128))
		
		class MyViewport(QWidget):
			def __init__(self, parent=None, flags=Qt.WindowFlags()):
				super().__init__(parent=parent, flags=flags)
			def sizeHint(self):
				return QSize(128, 128)
				
		self.setViewport(MyViewport())
		self.setItemDelegate(ThumbnailDelegate())
		self.setModel(ThumbnailModel())
		
		
		# TODO: data just add them to a queue and check visualRect before loading to see if it is in view
		
	def resizeEvent(self, event: QResizeEvent):
		size = event.size().width()
		self.itemDelegate().itemSize = size
		super().resizeEvent(event)
		return
		self.scheduleDelayedItemsLayout()
		
		# TODO: this lags very bad with a large number of items (>100,000). Can we wait to set grid size until drop?
		# TODO: could also just bypass sizehint and update ThumbnailDelegate directly
		#self.setGridSize(QSize(size, size))
		
	#def viewportSizeHint(self):
	#	return self.sizeHint() - self.verticalScrollBar().sizeHint()
		
	def sizeHint(self):
		vscroll = self.verticalScrollBar()
		print(" ssize: ", self.size())
		print(" gsize: ", self.geometry().size())
		print("     v: ", self.viewport())
		print(" vsize: ", self.viewport().size())
		print("vsizeh: ", self.viewport().sizeHint())
		print("csizeh: ", vscroll.sizeHint())
		print()
		# TODO: look at QAbstractScrollArea::viewportSizeHint
		return QSize(128,128) + self.verticalScrollBar().sizeHint()
