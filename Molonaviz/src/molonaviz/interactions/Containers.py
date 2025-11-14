"""
This file regroups different Containers, which are used to communicate between backend and frontend. The backend creates such objects and passes them to the frontend which displays them prettily.
Containers are just fancy classes which mimick a dictionnary or a named tuple. Their only goal is to have a list of attributes which can be easily read. They have no methods. 
"""
class Thermometer:
    def __init__(self, name : str, manuName : str, manuRef : str, error : float | str):
        self.name = name
        self.manuName = manuName
        self.manuRef = manuRef
        self.error = error

class PSensor:
    def __init__(self, name: str, datalogger: str, calibrationDate: str, 
                 intercept: float | str, dudh: float | str, dudt: float | str, 
                 error: float | str, dataloggerEUI: str | None = None):
        self.name = name
        self.datalogger = datalogger
        self.dataloggerEUI = dataloggerEUI
        self.calibrationDate = calibrationDate
        self.intercept = intercept
        self.dudh = dudh
        self.dudt = dudt
        self.error = error

class Shaft:
    def __init__(self, name: str, datalogger: str, depths: list[float | str], 
                 thermoType: str, dataloggerEUI: str | None = None):
        self.name = name
        self.datalogger = datalogger
        self.dataloggerEUI = dataloggerEUI
        self.thermoType = thermoType
        self.depths = depths

class SamplingPoint:
    def __init__(self, name : str, psensor : str, shaft : str, rivBed : float | str, offset : float | str):
        self.name = name
        self.psensor = psensor
        self.shaft = shaft
        self.rivBed = rivBed
        self.offset = offset


class Gateway:
    def __init__(self, name: str, study: str, tls_cert: bytes, 
                 tls_key: bytes, ca_cert: bytes, eui: str):
        self.name = name
        self.study = study
        self.tls_cert = tls_cert  
        self.tls_key = tls_key    
        self.ca_cert = ca_cert   
        self.eui = eui

class Relay:
    def __init__(self, name : str, gatewayEUI : str):
        self.name = name
        self.gatewayEUI = gatewayEUI

class Device:
    def __init__(self, name : str, relay : str, devEUI : str, shaft : str, psensor : str):
        self.name = name
        self.relay = relay
        self.devEUI = devEUI
        self.shaft = shaft
        self.psensor = psensor