#!/usr/bin/python3
import nvidia_smi
import json

myxml = nvidia_smi.XmlDeviceQuery()
mydict = nvidia_smi.JsonDeviceQuery()

# Example print JSON
print(json.dumps(mydict, indent=2))
