class Listenable:
	def __init__(self, value):
		self._listeners = []
		self._value = value
		
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, new):
		old = self._value
		self._value = new
		self._notify(new, old)
	
	def addListener(self, listener):
		self._listeners.append(listener)
		
	def _notify(self, new, old):
		#print("_notify new(" + str(new) + ") old(" + str(old) + ")")
		for l in self._listeners:
			l(new, old)
	