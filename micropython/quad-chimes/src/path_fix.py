# this should fail on micropython is just here for python3 testing in linux
print("path_fix being used")
try:
    import sys
    sys.path.append("/home/jim/MQTT-home/library") 
    sys.path.append("/homejim/MQTT-home/micropython/library") 
except:
    pass
print(sys.path)
