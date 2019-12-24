class Listenable:
	def __init__(self):
		self._listeners = []
	
	def addListener(self, listener):
		self._listeners.append(listener)
		
	def notify(self, *argv):
		for l in self._listeners:
			l(*argv)
	