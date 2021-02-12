#####
# Copyright (c) 2011-2012, NVIDIA Corporation.  All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    * Redistributions of source code must retain the above copyright notice,
#      this list of conditions and the following disclaimer.
#    * Redistributions in binary form must reproduce the above copyright
#      notice, this list of conditions and the following disclaimer in the
#      documentation and/or other materials provided with the distribution.
#    * Neither the name of the NVIDIA Corporation nor the names of its
#      contributors may be used to endorse or promote products derived from
#      this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
#####

#
# nvidia_smi
# nvml_bindings <at> nvidia <dot> com
#
# Sample code that attempts to reproduce the output of nvidia-smi -q- x
# For many cases the output should match
#
# To Run:
# $ python
# Python 2.7 (r27:82500, Sep 16 2010, 18:02:00)
# [GCC 4.5.1 20100907 (Red Hat 4.5.1-3)] on linux2
# Type "help", "copyright", "credits" or "license" for more information.
# >>> import nvidia_smi
# >>> print(nvidia_smi.XmlDeviceQuery())
# ...
#

from pynvml import *
import datetime
from xml.dom.minidom import parseString
import json

# We should vendor this dependency
from dicttoxml import dicttoxml

#
# Helper functions
#

# CounterType: NVML_VOLATILE_ECC, NVML_AGGREGATE_ECC
# bitType: NVML_SINGLE_BIT_ECC, NVML_DOUBLE_BIT_ECC

def DictGetEccByType(handle, counterType, bitType):
    try:
        count = str(nvmlDeviceGetTotalEccErrors(handle, bitType, counterType))
    except NVMLError as err:
        count = handleError(err)

    try:
        detail = nvmlDeviceGetDetailedEccErrors(handle, bitType, counterType)
        deviceMemory = str(detail.deviceMemory)
        registerFile = str(detail.registerFile)
        l1Cache = str(detail.l1Cache)
        l2Cache = str(detail.l2Cache)
    except NVMLError as err:
        msg = handleError(err)
        deviceMemory = msg
        registerFile = msg
        l1Cache = msg
        l2Cache = msg

    return {'device_memory': deviceMemory, 'register_file': registerFile, 'l1_cache': l1Cache, 'l2_cache': l2Cache, 'total': count }


def GetEccByType(handle, counterType, bitType):
    try:
        count = str(nvmlDeviceGetTotalEccErrors(handle, bitType, counterType))
    except NVMLError as err:
        count = handleError(err)

    try:
        detail = nvmlDeviceGetDetailedEccErrors(handle, bitType, counterType)
        deviceMemory = str(detail.deviceMemory)
        registerFile = str(detail.registerFile)
        l1Cache = str(detail.l1Cache)
        l2Cache = str(detail.l2Cache)
    except NVMLError as err:
        msg = handleError(err)
        deviceMemory = msg
        registerFile = msg
        l1Cache = msg
        l2Cache = msg
    strResult = ''
    strResult += '          <device_memory>' + deviceMemory + '</device_memory>\n'
    strResult += '          <register_file>' + registerFile + '</register_file>\n'
    strResult += '          <l1_cache>' + l1Cache + '</l1_cache>\n'
    strResult += '          <l2_cache>' + l2Cache + '</l2_cache>\n'
    strResult += '          <total>' + count + '</total>\n'
    return strResult

def GetEccByCounter(handle, counterType):
    strResult = ''
    strResult += '        <single_bit>\n'
    strResult += str(GetEccByType(handle, counterType, NVML_SINGLE_BIT_ECC))
    strResult += '        </single_bit>\n'
    strResult += '        <double_bit>\n'
    strResult += str(GetEccByType(handle, counterType, NVML_DOUBLE_BIT_ECC))
    strResult += '        </double_bit>\n'
    return strResult

def GetEccStr(handle):
    strResult = ''
    strResult += '      <volatile>\n'
    strResult += str(GetEccByCounter(handle, NVML_VOLATILE_ECC))
    strResult += '      </volatile>\n'
    strResult += '      <aggregate>\n'
    strResult += str(GetEccByCounter(handle, NVML_AGGREGATE_ECC))
    strResult += '      </aggregate>\n'
    return strResult

#
# Converts errors into string messages
#
def handleError(err):
    if (err.value == NVML_ERROR_NOT_SUPPORTED):
        return "N/A"
    else:
        return err.__str__()

#######
def JsonDeviceQuery():
  try:
    # initialize NVML
    nvmlInit()
    nvml_log = {}
    nvml_log['timestamp'] = str(datetime.date.today())
    nvml_log['driver_version'] = str(nvmlSystemGetDriverVersion())

    deviceCount = nvmlDeviceGetCount()

    nvml_log['attached_gpus'] = deviceCount
    nvml_log['gpus'] = {}

    for i in range(0, deviceCount):

      handle = nvmlDeviceGetHandleByIndex(i)
      pciInfo = nvmlDeviceGetPciInfo(handle)

      nvml_log['gpus']["gpu%s" % i] = {}

      nvml_log['gpus']["gpu%s" % i]['busId'] = pciInfo.busId.decode('utf-8')
      nvml_log['gpus']["gpu%s" % i]['product_name'] = nvmlDeviceGetName(handle)

      try:
        state = ('Enabled' if (nvmlDeviceGetDisplayMode(handle) != 0) else 'Disabled')
      except NVMLError as err:
        state = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['display_mode'] = state

      try:
        mode = 'Enabled' if (nvmlDeviceGetPersistenceMode(handle) != 0) else 'Disabled'
      except NVMLError as err:
        mode = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['persistence_mode'] = mode

      nvml_log['gpus']["gpu%s" % i]['driver_model'] = {}

      try:
        current = str(nvmlDeviceGetCurrentDriverModel(handle))
      except NVMLError as err:
        current = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['driver_model']['current_dm'] = current

      try:
        pending = str(nvmlDeviceGetPendingDriverModel(handle))
      except NVMLError as err:
        pending = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['driver_model']['pending_dm'] = pending

      try:
        serial = nvmlDeviceGetSerial(handle)
      except NVMLError as err:
        serial = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['serial'] = serial

      try:
        uuid = nvmlDeviceGetUUID(handle)
      except NVMLError as err:
        uuid = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['uuid'] = uuid

      try:
        vbios = nvmlDeviceGetVbiosVersion(handle)
      except NVMLError as err:
        vbios = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['vbios_version'] = vbios


      nvml_log['gpus']["gpu%s" % i]['inforom_version'] = {}
      try:
        oem = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_OEM)
        if oem == '':
          oem = 'N/A'
      except NVMLError as err:
        oem = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['inforom_version']['oem_object'] = oem

      try:
        ecc = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_ECC)
        if ecc == '':
          ecc = 'N/A'
      except NVMLError as err:
        ecc = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['inforom_version']['ecc'] = ecc

      try:
        pwr = nvmlDeviceGetInforomVersion(handle, NVML_INFOROM_POWER)
        if pwr == '':
          pwr = 'N/A'
      except NVMLError as err:
        pwr = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['inforom_version']['pwr_object'] = pwr


      # PCI
      nvml_log['gpus']["gpu%s" % i]['pci'] = {}
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_bus'] = pciInfo.bus
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_device'] = pciInfo.device
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_domain'] = pciInfo.domain
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_device_id'] = pciInfo.pciDeviceId
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_sub_system_id'] = pciInfo.pciSubSystemId
      nvml_log['gpus']["gpu%s" % i]['pci']['pci_bus_id'] = pciInfo.busId.decode('utf-8')

      nvml_log['gpus']["gpu%s" % i]['pci']['pcie_gen'] = {}
      try:
        gen = str(nvmlDeviceGetMaxPcieLinkGeneration(handle))
      except NVMLError as err:
        gen = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['pci']['pcie_gen']['max_link_gen'] = gen

      try:
        gen = str(nvmlDeviceGetCurrPcieLinkGeneration(handle))
      except NVMLError as err:
        gen = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['pci']['pcie_gen']['current_link_gen'] = gen

      nvml_log['gpus']["gpu%s" % i]['pci']['link_widths'] = {}
      try:
        width = str(nvmlDeviceGetMaxPcieLinkWidth(handle)) + 'x'
      except NVMLError as err:
        width = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['pci']['link_widths']['max_link_width'] = width

      try:
        width = str(nvmlDeviceGetCurrPcieLinkWidth(handle)) + 'x'
      except NVMLError as err:
        width = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['pci']['link_widths']['current_link_width'] = width


      # MEMORY
      try:
        fan = str(nvmlDeviceGetFanSpeed(handle)) + ' %'
      except NVMLError as err:
        fan = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['fan_speed'] = fan

      try:
        memInfo = nvmlDeviceGetMemoryInfo(handle)
        mem_total = str(memInfo.total / 1024 / 1024) + ' MB'
        mem_used = str(memInfo.used / 1024 / 1024) + ' MB'
        mem_free = str(memInfo.free / 1024 / 1024) + ' MB'
      except NVMLError as err:
        error = handleError(err)
        mem_total = error
        mem_used = error
        mem_free = error

      nvml_log['gpus']["gpu%s" % i]['memory_usage'] = {}
      nvml_log['gpus']["gpu%s" % i]['memory_usage']['total'] = mem_total
      nvml_log['gpus']["gpu%s" % i]['memory_usage']['used'] = mem_used
      nvml_log['gpus']["gpu%s" % i]['memory_usage']['free'] = mem_free


      try:
        mode = nvmlDeviceGetComputeMode(handle)
        if mode == NVML_COMPUTEMODE_DEFAULT:
          modeStr = 'Default'
        elif mode == NVML_COMPUTEMODE_EXCLUSIVE_THREAD:
          modeStr = 'Exclusive Thread'
        elif mode == NVML_COMPUTEMODE_PROHIBITED:
          modeStr = 'Prohibited'
        elif mode == NVML_COMPUTEMODE_EXCLUSIVE_PROCESS:
          modeStr = 'Exclusive Process'
        else:
          modeStr = 'Unknown'
      except NVMLError as err:
        modeStr = handleError(err)

      nvml_log['gpus']["gpu%s" % i]['compute_mode'] = modeStr


      # MEMORY UTILIZATION
      try:
        util = nvmlDeviceGetUtilizationRates(handle)
        gpu_util = str(util.gpu)
        mem_util = str(util.memory)
      except NVMLError as err:
        error = handleError(err)
        gpu_util = error
        mem_util = error

      nvml_log['gpus']["gpu%s" % i]['utilization'] = {}
      nvml_log['gpus']["gpu%s" % i]['utilization']['gpu_util'] = gpu_util
      nvml_log['gpus']["gpu%s" % i]['utilization']['memory_util'] = mem_util

      # ECC
      try:
        (current, pending) = nvmlDeviceGetEccMode(handle)
        curr_str = 'Enabled' if (current != 0) else 'Disabled'
        pend_str = 'Enabled' if (pending != 0) else 'Disabled'
      except NVMLError as err:
        error = handleError(err)
        curr_str = error
        pend_str = error

      nvml_log['gpus']["gpu%s" % i]['ecc_mode'] = {}
      nvml_log['gpus']["gpu%s" % i]['ecc_mode']['current_ecc'] = curr_str
      nvml_log['gpus']["gpu%s" % i]['ecc_mode']['pending_ecc'] = pend_str

      # ECC ERRORS
      nvml_log['gpus']["gpu%s" % i]['ecc_errors'] = {}
      nvml_log['gpus']["gpu%s" % i]['ecc_errors']['volatile'] = {}
      nvml_log['gpus']["gpu%s" % i]['ecc_errors']['aggregate'] = {}
      # CounterType: NVML_VOLATILE_ECC, NVML_AGGREGATE_ECC
      # bitType: NVML_SINGLE_BIT_ECC, NVML_DOUBLE_BIT_ECC
      for countertype in [NVML_VOLATILE_ECC,NVML_AGGREGATE_ECC]:
        for bittype in [NVML_SINGLE_BIT_ECC, NVML_DOUBLE_BIT_ECC]:

          d = DictGetEccByType(handle, countertype, bittype)

          if bittype == NVML_SINGLE_BIT_ECC and countertype == NVML_VOLATILE_ECC:
            nvml_log['gpus']["gpu%s" % i]['ecc_errors']['volatile']['single_bit'] = d

          if bittype == NVML_SINGLE_BIT_ECC and countertype == NVML_AGGREGATE_ECC:
            nvml_log['gpus']["gpu%s" % i]['ecc_errors']['aggregate']['single_bit'] = d

          if bittype == NVML_DOUBLE_BIT_ECC and countertype == NVML_VOLATILE_ECC:
            nvml_log['gpus']["gpu%s" % i]['ecc_errors']['volatile']['double_bit'] = d

          if bittype == NVML_DOUBLE_BIT_ECC and countertype == NVML_AGGREGATE_ECC:
            nvml_log['gpus']["gpu%s" % i]['ecc_errors']['aggregate']['double_bit'] = d

      # TEMPERATURE
      try:
        temp = str(nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)) + ' C'
      except NVMLError as err:
        temp = handleError(err)

      nvml_log['gpus']["gpu%s" % i]['temperature'] = temp

      # POWER READINGS
      nvml_log['gpus']["gpu%s" % i]['power_readings'] = {}

      try:
        perfState = nvmlDeviceGetPowerState(handle)
      except NVMLError as err:
        perfState = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['power_readings']['power_state'] = perfState

      try:
        powMan = nvmlDeviceGetPowerManagementMode(handle)
        powManStr = 'Supported' if powMan != 0 else 'N/A'
      except NVMLError as err:
        powManStr = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['power_readings']['power_management'] = powManStr

      try:
        powDraw = (nvmlDeviceGetPowerUsage(handle) / 1000.0)
        powDrawStr = '%.2f W' % powDraw
      except NVMLError as err:
        powDrawStr = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['power_readings']['power_draw'] = powDrawStr

      try:
        powLimit = (nvmlDeviceGetPowerManagementLimit(handle) / 1000.0)
        powLimitStr = '%d W' % powLimit
      except NVMLError as err:
        powLimitStr = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['power_readings']['power_limit'] = powLimitStr

      # CLOCKS
      nvml_log['gpus']["gpu%s" % i]['clocks'] = {}

      try:
        graphics = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_GRAPHICS))
      except NVMLError as err:
        graphics = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['clocks']['graphics_clock'] = "%s MHz" % graphics

      try:
        sm = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_SM))
      except NVMLError as err:
        sm = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['clocks']['sm_clock'] = "%s MHz" % sm

      try:
        mem = str(nvmlDeviceGetClockInfo(handle, NVML_CLOCK_MEM))
      except NVMLError as err:
        mem = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['clocks']['mem_clock'] = "%s MHz" % mem


      # MAX CLOCKS
      nvml_log['gpus']["gpu%s" % i]['max_clocks'] = {}

      try:
        graphics = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_GRAPHICS))
      except NVMLError as err:
        graphics = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['max_clocks']['graphics_clock'] = "%s MHz" % graphics

      try:
        sm = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_SM))
      except NVMLError as err:
        sm = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['max_clocks']['sm_clock'] = "%s MHz" % sm

      try:
        mem = str(nvmlDeviceGetMaxClockInfo(handle, NVML_CLOCK_MEM))
      except NVMLError as err:
        mem = handleError(err)
      nvml_log['gpus']["gpu%s" % i]['max_clocks']['mem_clock'] = "%s MHz" % mem


      # PERFORMANCE STATE
      try:
        perfState = nvmlDeviceGetPowerState(handle)
        perfStateStr = 'P%s' % perfState
      except NVMLError as err:
        perfStateStr = handleError(err)

      nvml_log['gpus']["gpu%s" % i]['performance_state'] = perfStateStr


      # COMPUTE PROCESSES
      nvml_log['gpus']["gpu%s" % i]['compute_processes'] = {}

      try:
        procs = nvmlDeviceGetComputeRunningProcesses(handle)
      except NVMLError as err:
        procs = []
        procstr = handleError(err)

      for p in procs:
        nvml_log['gpus']["gpu%s" % i]['compute_processes']['process_info'] = {}
        nvml_log['gpus']["gpu%s" % i]['compute_processes']['process_info'][p.pid] = {}

        try:
          name = str(nvmlSystemGetProcessName(p.pid))
        except NVMLError as err:
          if (err.value == NVML_ERROR_NOT_FOUND):
            # probably went away
            continue
          else:
            name = handleError(err)
            nvml_log['gpus']["gpu%s" % i]['compute_processes']['process_info'][p.pid]['process_name'] = name

            if (p.usedGpuMemory == None):
              used_gpu_mem += 'N\A'
            else:
              used_gpu_mem += '%d MB\n' % (p.usedGpuMemory / 1024 / 1024)
            nvml_log['gpus']["gpu%s" % i]['compute_processes']['process_info'][p.pid]['used_memory'] = used_gpu_mem


  except NVMLError as err:
    nvml_log = {}

  nvmlShutdown()

  return nvml_log

#######
# This used to be the primary
def XmlDeviceQuery():
  # We might have a problem with section as the xml uses an ID to identify them.
  #   strResult += '  <gpu id="%s">\n' % pciInfo.busId.decode('utf-8')
  # Our XML does <gpuN></gpuN> instead.

  d = []
  d.append(JsonDeviceQuery())
  xml = dicttoxml(d, custom_root='nvidia_smi_log', attr_type=False).decode('utf-8')
  dom = parseString(xml)
  return dom.toprettyxml(indent="  ")

