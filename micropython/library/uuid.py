import machine
import ubinascii


def getnode():
    # id = ubinascii.hexlify(machine.unique_id()).decode('utf-8')
    mid = machine.unique_id()
    id = int.from_bytes(mid, "big")
    print("getnode id[%s]" % (id,))
    return id
