from typing import *
from collections import *

################################################################################
class InputType:
	MOUSE = 0
	MOUSE_WHEEL = 1
	KEYBOARD = 2
################################################################################
class Input:
	def __init__(self, inType: InputType, inId: Any = None):
		self.inType = inType
		self.inId = inId
	
	def __ident__(self):
		return (self.inType, self.inId)
	
	def __hash__(self):
		return hash(self.__ident__())
	
	def __eq__(self, other):
		assert(type(other) == Input)
		return self.__ident__() == other.__ident__()
################################################################################
InputComparator = Callable[[Any], bool]
InputComparePair = Tuple[Input, InputComparator]
################################################################################
class InputState:
	def __init__(self, value: Any, comp: InputComparator):
		self.value = value
		self.comp = comp
	def check(self) -> bool:
		if self.value is not None: # TODO: Is there a way to avoid this? seems hacky
			return self.comp(self.value)
		else:
			return False
################################################################################
class BindEvent:
	PRESS = 0
	RELEASE = 1
	TRIGGER = 2
################################################################################
class Bind:
	# TODO: change to use addListener pattern instead of passing in constructor
	def __init__(self, name: str, inputs: List[InputComparePair], triggers = []):
		self.name = name
		self.inputs = {}
		self.triggers = {}
		self.listeners = defaultdict(list)
		
		for inp, comp in inputs:
			self.inputs[inp] = InputState(None, comp)
		for inp in triggers:
			self.triggers[inp] = True
		
	def isActive(self):
		for inp, state in self.inputs.items():
			if not state.check():
				return False
		return True
		
	def update(self, inp: Input, val: Any):
		pre = self.isActive()
		self.inputs[inp].value = val
		post = self.isActive()
		if post and not pre:
			for l in self.listeners[BindEvent.PRESS]:
				l(inp, val, self.inputs)
		elif pre and not post:
			for l in self.listeners[BindEvent.RELEASE]:
				l(inp, val, self.inputs)
				
	def trigger(self, inp: Input, val: Any):
		if self.isActive():
			for l in self.listeners[BindEvent.TRIGGER]:
				l(inp, val, self.inputs)
				
	def addListener(self, event, listener): # TODO: types
		self.listeners[event].append(listener)
################################################################################
class BindSystem:
	def __init__(self, *args, **kwargs):
		self.binds = {}
		self.inputToBinds = defaultdict(list)
		self.triggersToBinds = defaultdict(list)
	
	def addBind(self, bind: Bind):
		assert(self.binds.get(bind.name) is None)
		self.binds[bind.name] = bind
		for inp in bind.inputs:
			self.inputToBinds[inp].append(bind)
		for inp in bind.triggers:
			self.triggersToBinds[inp].append(bind)
			
	def addListener(self, bind: str, event, listener): # TODO: Types
		self.binds[bind].addListener(event, listener)
			
	def update(self, inp: Input, val: Any):
		for bind in self.inputToBinds[inp]:
			bind.update(inp, val)
		for bind in self.triggersToBinds[inp]:
			bind.trigger(inp, val)