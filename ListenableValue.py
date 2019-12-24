from Listenable import Listenable

class ListenableValue(Listenable):
	def __init__(self, value):
		super().__init__()
		self._value = value
		
	@property
	def value(self):
		return self._value
	
	@value.setter
	def value(self, new):
		old = self._value
		self._value = new
		self.notify(new, old)
	