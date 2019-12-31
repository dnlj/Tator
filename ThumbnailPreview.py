from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

################################################################################
class Thumbnail(QWidget):
	def __init__(self, image: QPixmap, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.image = image
		self.setMinimumSize(64, 64)
		
	def paintEvent(self, event: QPaintEvent):
		target = event.rect()
		origin = self.image.rect()
		
		paint = QPainter(self)
		
		scale = min(target.width() / origin.width(), target.height() / origin.height())
		size = origin.size() * scale
		offset = (target.size() - size) / 2
		offset = QPoint(offset.width(), offset.height())
		new = QRect(origin.topLeft() + offset, size)
		
		paint.drawPixmap(new, self.image, origin)
	
################################################################################
class ThumbnailPreview(QWidget):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		
		self.temp = QPixmap("data/test4.jpg")
		
		layout = QVBoxLayout()
		
		for i in range(0, 5):
			thumb = Thumbnail(self.temp)
			thumb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
			layout.addWidget(thumb)
		
		btnCont = QWidget()
		btnLayout = QHBoxLayout()
		btnLayout.setContentsMargins(0, 0, 0, 0)
		
		self.prevButton = QPushButton("Prev")
		self.nextButton = QPushButton("Next")
		btnLayout.addWidget(self.prevButton)
		btnLayout.addWidget(self.nextButton)
		
		btnCont.setLayout(btnLayout)
		btnCont.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		layout.addWidget(btnCont)
		
		self.setLayout(layout)
		
	def sizeHint(self):
		return QSize(-1, -1)