	
try:
	import pycallgraph
	pycallgraph.start_trace()
except ImportError:
	print "Do not have pycallgraph installed. Not tracing calls"


def go():

	import PyGalil.galilInterface

	PyGalil.galilInterface.test()



if __name__ == "__main__":
	go()
