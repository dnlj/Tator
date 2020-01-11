from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

import rapidjson as json

from binder import *
from ActionBrush import ActionBrush
from ActionFill import ActionFill
from LayerListWidget import LayerListWidget
from EditArea import EditArea
from LabelEditor import LabelEditor

# GrabCut (https://docs.opencv.org/3.4/d8/d83/tutorial_py_grabcut.html)
#	https://stackoverflow.com/questions/16705721/opencv-floodfill-with-mask
# https://www.cc.gatech.edu/~aagrawal307/magic.pdf

# TODO: look into watershed:
#	https://en.wikipedia.org/wiki/Watershed_(image_processing)
#	https://scikit-image.org/docs/dev/auto_examples/segmentation/plot_watershed.html
# 	https://docs.opencv.org/master/d3/db4/tutorial_py_watershed.html

# TODO: change events to send np arrays instead of QPoints
# TODO: Undo/Redo
# TODO: cursor per tool
# TODO: Tool shortcuts
# TODO: Tool options menu
# TODO: Switch visible tools depending on.activeLayer.mask layer type
# TODO: Make 1-9+0 shortcuts for changing the active layers label
# TODO: Warn if a layer is unlabeled
# TODO: right click open dropdown to select layer type?

################################################################################
class MainWindow(QMainWindow):
	def __init__(self, parent=None, flags=Qt.WindowFlags()):
		super().__init__(parent=parent, flags=flags)
		self.setFocusPolicy(Qt.WheelFocus)
		
		windowFeatures = QDockWidget.DockWidgetMovable
		
		actions = {
			ActionBrush: {
				"name": "Brush",
				"key": Qt.Key_B,
			},
			ActionFill: {
				"name": "Fill",
				"key": Qt.Key_G,
			},
		}
		
		self.binds = BindSystem()
		
		self.binds.addBind(Bind("prev",
			inputs=[(Input(InputType.KEYBOARD, Qt.Key_Comma), lambda e: e[0])]
		))
		self.binds.addListener("prev", BindEvent.PRESS, lambda *_: self.prevImage())
		
		self.binds.addBind(Bind("next",
			inputs=[(Input(InputType.KEYBOARD, Qt.Key_Period), lambda e: e[0])]
		))
		self.binds.addListener("next", BindEvent.PRESS, lambda *_: self.nextImage())
		
		self.binds.addBind(Bind("close",
			inputs=[(Input(InputType.KEYBOARD, Qt.Key_Escape), lambda e: e[0])]
		))
		self.binds.addListener("close", BindEvent.PRESS, lambda *_: self.close())
		
		########################################################################
		with open("project.json") as pfile:
			self.project = json.load(pfile)
		
		# TODO: We should be able to delete things from the json file and have it just work. Will need to change this.
		# Verify category ids
		labels = self.project["labels"]
		for i in range(len(labels)):
			if i != labels[i]["id"]: raise RuntimeError("Incorrect label id")
			oldColor = labels[i]["color"]
			newColor = QColor(oldColor)
			labels[i]["color"] = newColor.rgba()
		
		# Verify image ids
		imgs = self.project["images"]
		for i in range(len(imgs)):
			if i != imgs[i]["id"]: raise RuntimeError("Incorrect image id")
			
		# Verify annotation ids
		anns = self.project["annotations"]
		for i in range(len(anns)):
			if i != anns[i]["id"]: raise RuntimeError("Incorrect annotation id")
			
		#######################################################################
		self.setWindowTitle("Tator")
		self.setWindowIcon(QIcon("icon.png"))
		self.setDockOptions(QMainWindow.AnimatedDocks | QMainWindow.AllowTabbedDocks | QMainWindow.AllowNestedDocks)
		
		self.editArea = EditArea(labels)
		self.setCentralWidget(self.editArea)
		self.editArea.setAction(ActionBrush)
		
		self.toolbar = QToolBar("Tools")
		self.toolbar.addAction("Prev", self.prevImage)
		self.toolbar.addAction("Next", self.nextImage)
		self.toolbar.addSeparator()
		self.toolbar.addAction("Box")
		self.toolbar.addAction("Polygon")
		self.toolbar.addSeparator()
		
		for a, d in actions.items():
			def callback(*_, a=a): self.editArea.setAction(a)
			self.toolbar.addAction(d["name"], callback)
			self.binds.addBind(Bind(d["name"],
				inputs=[(Input(InputType.KEYBOARD, d["key"]), lambda e : e[0])]
			))
			self.binds.addListener(d["name"], BindEvent.PRESS, callback)
			
		self.toolbar.addAction("Wand Select")
		self.toolbar.addSeparator()
		self.toolbar.addAction("Smart Select")
		
		
		# TODO: This isnt really important. Make a proper image browser/explorer window if you want this.
		#self.thumbnailPreview = ThumbnailPreview()
		#self.imagePanel = QDockWidget("")
		#self.imagePanel.setFeatures(windowFeatures)
		#self.imagePanel.setWidget(self.thumbnailPreview)
		#self.thumbnailPreview.prevButton.clicked.connect(lambda: self.prevImage())
		#self.thumbnailPreview.nextButton.clicked.connect(lambda: self.nextImage())
		
		# TODO: Again, this isnt really needed here. Make a proper category editor window.
		#self.labelPanel = QDockWidget("Categories Panel")
		#self.labelPanel.setFeatures(windowFeatures)
		
		# TODO: Move into own file?
		self.otherPanel = QDockWidget("Other")
		self.otherPanel.setFeatures(windowFeatures)
		otherWidget = QWidget()
		otherLayout = QHBoxLayout()
		otherWidget.setLayout(otherLayout)
		
		otherWidget.labelsButton = QPushButton("Labels")
		otherWidget.labelWindow = LabelEditor(self.project["labels"], self, Qt.Window)
		otherWidget.labelsButton.clicked.connect(lambda: otherWidget.labelWindow.show())
		
		otherLayout.addWidget(otherWidget.labelsButton)
		otherLayout.addWidget(QPushButton("Browse"))
		otherWidget.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
		self.otherPanel.setWidget(otherWidget)
		
		self.layerList = LayerListWidget(labels)
		self.layerList.onNewBitmapClicked.connect(self.editArea.addBitmapLayer)
		self.layerList.onLayerSelectionChanged.connect(self.editArea.setActiveLayer)
		self.layerList.onDeleteLayer.connect(lambda layer: self.editArea.deleteLayer(layer))
		self.editArea.onLayersUpdated.addListener(self.layerList.updateLayers)
		
		self.layerPanel = QDockWidget("Layers Panel")
		self.layerPanel.setFeatures(windowFeatures)
		self.layerPanel.setWidget(self.layerList)
		
		self.addToolBar(self.toolbar)
		self.addDockWidget(Qt.RightDockWidgetArea, self.otherPanel)
		self.addDockWidget(Qt.RightDockWidgetArea, self.layerPanel)
		self.setStatusBar(QStatusBar())
		
		self.curImage = -1
		self.nextImage()
	
	def setImage(self, path):
		self.editArea.setImage(QImage(path))
		self.editArea.addBitmapLayer()
		self.layerList.setLayerSelection(0)
		
	def nextImage(self, skipKnown: bool = False):
		if self.curImage == len(self.project["images"]) - 1: return # TODO: warning or something?
		self.curImage += 1
		img = self.project["images"][self.curImage]
		self.setImage(img["path"])
		
	def prevImage(self):
		if self.curImage == 0: return # TODO: warning or something?
		self.curImage -= 1
		img = self.project["images"][self.curImage]
		self.setImage(img["path"])
	
	def keyPressEvent(self, event: QKeyEvent):
		self.binds.update(Input(InputType.KEYBOARD, event.key()), (True,))
		self.editArea.keyPressEvent(event)
		
	def keyReleaseEvent(self, event: QKeyEvent):
		self.binds.update(Input(InputType.KEYBOARD, event.key()), (False,))
		self.editArea.keyReleaseEvent(event)
		
	#def closeEvent(self, event: QCloseEvent):
	# TODO: write to temp file then rename once complete
	#	with open("test.json", "w") as pfile:
	#		json.dump(
	#			self.project,
	#			pfile,
	#			ensure_ascii=False,
	#			indent=4
	#		)

################################################################################
if __name__ == "__main__":
	app = QApplication([])
	# TODO: Set dark theme
	main = MainWindow()
	main.resize(1920, 1080)
	main.show()
	app.exec_()