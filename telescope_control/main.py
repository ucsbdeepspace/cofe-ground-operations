import globalConf
import ipCheck
import startGui #GUI handling

try:
    import pycallgraph
    pycallgraph.start_trace()
except ImportError:
    print("Do not have pycallgraph installed. Not tracing calls")
except AttributeError:
    print("Unrecognized version of pycallgraph installed. Not tracing calls")

def go():

    ipCheckWin = ipCheck.IpChecker(0)
    ipCheckWin.MainLoop()

    print("Startup check complete. IP = \"" + str(globalConf.galilIP) + "\"")

    import PyGalil.galilInterface

    globalConf.gInt = PyGalil.galilInterface.GalilInterface(
        ip=globalConf.galilIP, port=globalConf.galilPort,
        poll=False, resetGalil=False)

    print("opened galil. Connection:" + str(globalConf.gInt))

    startGui.main()

if __name__ == "__main__":
    go()
