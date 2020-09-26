from collections import defaultdict

class Event:
	def __init__(self,name,**kwargs):
		self.data=kwargs
		self.name=name
	def __getitem__(self,k):
		return self.data[k]
	def __getattr__(self,k):
		if k in self.data: return self.data[k]

class EventManager:
	def __init__(self):
		self.handlers=defaultdict(list)
	def clear(self):
		self.__init__()
	def on(self,event,func):
		self.handlers[event].append(func)
	def __call__(self,event_obj):
		print(event_obj.name,event_obj.data)
		if event_obj.name not in self.handlers: return
		handlers = self.handlers[event_obj.name]
		for handler in handlers: handler(event_obj)
