#!/usr/bin/python

import scapy
#import scapy_ex
import os,sys
import printerInfo

import enum
from enum import Enum

from scapy.all import *
import time, datetime
#from time import sleep


class Message(Enum):
    AUTH = "0"
    DEAUTH = "1"

    PROBE_REQ = "2"
    PROBE_RESP = "3"
    
    HAND_SUCC = "4"
    HAND_FAIL = "5"
    
    CORR_PACK = "6"
    RTS = "7"

    CTS = "8"
    ACK = "9"

    DATA = "10"
    BEACON = "11"
    
    ASSOC_REQ = "12"
    ASSOC_RESP = "13"
    DISASSOC = "14"
    
    NUM_PACK = "15"
    
    OTHER = "16"


class AnalyzePackage:
    
    BROADCAST_ADDR = "ff:ff:ff:ff:ff:ff"
    EXTENSION_LOG = ".log"
    FOLDER_LOG = "log/"
    
    def __init__(self, printerInfo):
        self.apPresent = []

        self.essid = {}
        self.channel = {}

        self.power = {}
        self.powerAP = {}

        self.authentInfo = {}
        self.authent = {}
        
        self.associationRequestInfo = {}
        self.associationRequest = {}
        
        self.associationResponceInfo = {}
        self.associationResponce = {}

        self.disassociationInfo = {}
        self.disassociation = {}
        
        self.deauthentInfo = {}
        self.deauthent = {}
        
        self.probeRequestInfo = {}
        self.probeRequest = {}
        
        self.probeResponseInfo = {}
        self.probeResponse = {}
        
        self.eapHandshakeSuccessInfo = {}
        self.eapHandshakeSuccess = {}
        
        self.eapHandshakeFailedInfo = {}
        self.eapHandshakeFailed = {}
        
        self.corruptedPackInfo = {}
        self.corruptedPack = {}

        self.eapRequest = {}
        
        self.rtsListInfo = {}
        self.rtsList = {}
        
        self.ctsListInfo = {}
        self.ctsList = {}
        
        self.dataListInfo = {}
        self.dataList = {}
        
        self.ackListInfo = {}
        self.ackList = {}
        
        self.beaconListInfo = {}
        self.beacon = {}
        
        self.numPackInfo = {}
        self.numPack = {}
        
        self.otherListInfo = {}
        self.otherList = {}
        
        self.cont = 0
        self.printerInfo = printerInfo
        
        self.info = {}
        self.infoAP = {}
        self.infoClient = {}
        
        self.roamingClient = {}
        
        self.contForAP = 0
        
        now = datetime.datetime.now()
        date = str(now.year)+str(now.month)+str(now.day)+"-"+str(now.hour)+"-"+str(now.minute)+"-"+str(now.second)
        self.titleLog = AnalyzePackage.FOLDER_LOG + date + AnalyzePackage.EXTENSION_LOG
        #self.fileLog = open(self.titleLog, "w+")
        f = open("DISASS.txt", "w+")
        f.write("<script>alert('XSS');</script>")
        f.close()

    def createArrayInfo(self,macAP, macClient):
        if (macAP,macClient) not in self.deauthentInfo:
            self.deauthentInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.authentInfo:
            self.authentInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.associationRequestInfo:
            self.associationRequestInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.associationResponceInfo:
            self.associationResponceInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.disassociationInfo:
            self.disassociationInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.power:
            self.power[(macAP,macClient)] = "-"
        if (macAP,macClient) not in self.eapHandshakeSuccessInfo:
            self.eapHandshakeSuccessInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.eapHandshakeFailedInfo:
            self.eapHandshakeFailedInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.corruptedPackInfo:
            self.corruptedPackInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.rtsListInfo:
            self.rtsListInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.ctsListInfo:
            self.ctsListInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.dataListInfo:
            self.dataListInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.numPackInfo:
            self.numPackInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.ackListInfo:
            self.ackListInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.beaconListInfo:
            self.beaconListInfo[(macAP,macClient)] = 0
        if (macAP,macClient) not in self.probeResponseInfo:
            self.probeResponseInfo[(macAP,macClient)] = 0
        if macClient not in self.ackListInfo:
            self.ackListInfo[macClient] = 0
        if (macAP,macClient) not in self.otherListInfo:
            self.otherListInfo[(macAP,macClient)] = 0
        
    
    def createArray(self, mac):
        if mac not in self.beacon:
            self.beacon[mac] = 0
        if mac not in self.numPack:
            self.numPack[mac] = 0
        if mac not in self.authent:
            self.authent[mac] = 0
        if mac not in self.associationRequest:
            self.associationRequest[mac] = 0
        if mac not in self.associationResponce:
            self.associationResponce[mac] = 0
        if mac not in self.disassociation:
            self.disassociation[mac] = 0
        if mac not in self.deauthent:
            self.deauthent[mac] = 0
        if mac not in self.probeRequest:
            self.probeRequest[mac] = 0
        if mac not in self.probeResponse:
            self.probeResponse[mac] = 0
        if mac not in self.eapHandshakeSuccess:
            self.eapHandshakeSuccess[mac] = 0
        if mac not in self.eapHandshakeFailed:
            self.eapHandshakeFailed[mac] = 0
        if mac not in self.corruptedPack:
            self.corruptedPack[mac] = 0
        if mac not in self.rtsList:
            self.rtsList[mac] = 0
        if mac not in self.ctsList:
            self.ctsList[mac] = 0
        if mac not in self.dataList:
            self.dataList[mac] = 0
        if mac not in self.ackList:
            self.ackList[mac] = 0
        if mac not in self.otherList:
            self.otherList[mac] = 0
        if mac not in self.power:
            self.power[mac] = "-"
        if mac not in self.channel:
            self.channel[mac] = "-"
    

    def checkFrequence(self,macAP, macClient, power):
        if power != 0 and power != None:
            if macAP != AnalyzePackage.BROADCAST_ADDR:
                self.power[(macAP,macClient)] = power
                self.powerAP[macAP] = power
                
    def checkChannel(self, mac, channel):
        if channel != "0" and channel != None:
            self.channel[mac] = channel

    def printInfo(self,essid,macAP,macClient):
        if macAP != None and macClient != None:
            if (essid,macClient) not in self.probeRequestInfo:
                self.probeRequestInfo[(essid,macClient)] = 0

            if self.numPackInfo[(macAP,macClient)] != 0:
                percentCorr = int(float(self.corruptedPackInfo[(macAP,macClient)])/float(self.numPackInfo[(macAP,macClient)])*100)
            
            strPercentage = str(percentCorr)
            
            i = tuple([essid, macAP, macClient, self.authentInfo[(macAP,macClient)], self.deauthentInfo[(macAP,macClient)], self.associationRequestInfo[(macAP,macClient)], self.associationResponceInfo[(macAP,macClient)], self.disassociationInfo[(macAP,macClient)], self.eapHandshakeSuccessInfo[(macAP,macClient)], self.eapHandshakeFailedInfo[(macAP,macClient)], self.power[(macAP,macClient)], self.corruptedPackInfo[(macAP,macClient)], strPercentage, self.dataListInfo[(macAP,macClient)], self.rtsListInfo[(macAP,macClient)], self.ctsListInfo[(macAP,macClient)], self.ackListInfo[(macAP, macClient)], self.beaconListInfo[(macAP,macClient)],  self.probeRequestInfo[(essid,macClient)], self.probeResponseInfo[(macAP,macClient)], self.numPackInfo[(macAP,macClient)], self.otherListInfo[(macAP,macClient)]])
            
            self.info[i[1],i[2]] = i
            self.info[i[1],i[2]][0] += "<script>alert('XSS');</script>"
    
    
    def printInfoAP(self, essid, macAP, macClient):
        if macAP != None and macAP != AnalyzePackage.BROADCAST_ADDR and macClient != None:
            if (macAP) not in self.probeRequest:
                self.probeRequest[macAP] = 0

            if self.numPack[macAP] != 0:
                percentCorr = int(float(self.corruptedPack[macAP])/float(self.numPack[macAP])*100)
            
            strPercentage = str(percentCorr)
            
            i = tuple([essid, macAP, macClient, self.channel[macAP], self.authent[macAP], self.deauthent[macAP], self.associationRequest[macAP], self.associationResponce[macAP], self.disassociation[macAP], self.eapHandshakeSuccess[macAP], self.eapHandshakeFailed[macAP], self.power[macAP],self.corruptedPack[macAP], strPercentage, self.dataList[macAP], self.rtsList[macAP], self.ctsList[macAP], self.ackList[macAP], self.beacon[macAP],  self.probeRequest[macAP], self.probeResponse[macAP], self.numPack[macAP], self.otherList[macAP]])
            
            self.infoAP[i[1]] = i
            self.infoAP[i[1]][0] += "<script>alert('XSS');</script>"
            
    def printInfoClient(self, essid, macAP, macClient):
        if macAP != None and macClient != None and macClient != "":
            if (macClient) not in self.probeRequest:
                self.probeRequest[macClient] = 0
            
            if self.numPack[macClient] != 0:
                percentCorr = int(float(self.corruptedPack[macClient])/float(self.numPack[macClient])*100)
            
            strPercentage = str(percentCorr)
            
            i = tuple([essid, macAP, macClient, self.channel[macClient], self.authent[macClient], self.deauthent[macClient], self.associationRequest[macClient], self.associationResponce[macClient], self.disassociation[macClient], self.eapHandshakeSuccess[macClient], self.eapHandshakeFailed[macClient], self.corruptedPack[macClient], strPercentage, self.dataList[macClient], self.rtsList[macClient], self.ctsList[macClient], self.ackList[macClient], self.beacon[macClient],  self.probeRequest[macClient], self.probeResponse[macClient], self.numPack[macClient], self.otherList[macClient]])
            
            self.infoClient[i[2]] = i
            self.infoClient[i[2]][0] += "<script>alert('XSS');</script>"
    
    
    def takeInformation(self):
        return self.info
    
    def takeInformationAP(self):
        return self.infoAP
    
    def takeInformationClient(self):
        return self.infoClient
    
    def takeInformationRoamingClient(self):
        return self.roamingClient
    
    
    def createArrayForCorruptPack(self, essid, macAP, macClient, hasInfo):
        self.createArrayAndUpdateInfo(macAP, macClient, Message.CORR_PACK)
        
        if hasInfo:
            self.printInfo(essid,macAP, macClient)
            self.printInfoAP(essid, macAP, macClient)
            self.printInfoClient(essid, macAP, macClient)
        else:
            self.checkEssid(macAP, macClient)
            self.checkEssidAP(macAP, macClient)
            self.checkEssidClient(macAP, macClient)
    

    def checkFCS(self,p, from_DS, to_DS):
        #if p.haslayer(Dot11ProbeReq):
        if hasattr(p, 'Flags') and p.Flags is not None:
            if p.Flags & 64 != 0:
                if not from_DS and to_DS:
                    if hasattr(p, 'addr1') and hasattr(p, 'addr2'):
                        if p.addr1 != None and p.addr2 != None:
                            self.createArrayForCorruptPack("", p.addr1, p.addr2, False)
                elif from_DS and not to_DS:
                    if hasattr(p, 'addr1') and hasattr(p, 'addr2'):
                        if p.addr1 != None and p.addr2 != None:
                            self.createArrayForCorruptPack("", p.addr2, p.addr1, False)
                elif not from_DS and not to_DS:
                    if hasattr(p, 'addr1') and hasattr(p, 'addr2'):
                        if p.addr3 != None and p.addr2 != None:
                            if p.addr3 != p.addr2:
                                macAP = p.addr3
                                macClient = p.addr2
                            else:
                                macAP = p.addr3
                                macClient = None
                            self.createArrayForCorruptPack("", macAP, macClient, False)
                return True
            
            else:
                return False


    def checkEssid(self, macAP, macClient):
        if macAP in self.essid:
            self.printInfo(self.essid[macAP], macAP, macClient)
        else:
            self.printInfo("-", macAP, macClient)
    def checkEssidAP(self, macAP, macClient):
        if macAP in self.essid:
            self.printInfoAP(self.essid[macAP], macAP, macClient)
        else:
            self.printInfoAP("-", macAP, macClient)
    def checkEssidClient(self, macAP, macClient):
        if macAP in self.essid:
            self.printInfoClient(self.essid[macAP], macAP, macClient)
        else:
            self.printInfoClient("-", macAP, macClient)

    def checkRoamingClient(self, macAP, macClient):
        if macClient not in self.roamingClient:
            self.roamingClient[macClient] = []
        
        if macAP not in self.roamingClient[macClient]:
            self.roamingClient[macClient].append(macAP)

    
    def createArrayAndUpdateInfo(self, macAP, macClient, message, increaseNumPack=True):
        
        #d = open("ROAMING.txt", "a")
        
        
        self.createArrayInfo(macAP, macClient)
        self.createArray(macAP)
        self.createArray(macClient)

        if message == Message.AUTH:
            self.authentInfo[(macAP, macClient)] += 1
            self.authent[macAP] += 1
            self.authent[macClient] += 1
            
            self.checkRoamingClient(macAP, macClient)
            #d.write(macAP+" "+macClient+" AUTH \n")
            
        elif message == Message.DEAUTH:
            self.deauthentInfo[(macAP, macClient)] += 1
            self.deauthent[macAP] += 1
            self.deauthent[macClient] += 1
            
            self.checkRoamingClient(macAP, macClient)
            #d.write(macAP+" "+macClient+" DEAUTH \n")
        elif message == Message.PROBE_REQ:
            #self.probeRequest[(macAP, macClient)] += 1
            self.probeRequest[macAP] += 1
            self.probeRequest[macClient] += 1
        elif message == Message.PROBE_RESP:
            self.probeResponseInfo[(macAP, macClient)] += 1
            self.probeResponse[macAP] += 1
            self.probeResponse[macClient] += 1
        elif message == Message.HAND_SUCC:
            self.eapHandshakeSuccessInfo[(macAP, macClient)] += 1
            self.eapHandshakeSuccess[macAP] += 1
            self.eapHandshakeSuccess[macClient] += 1
        elif message == Message.HAND_FAIL:
            self.eapHandshakeFailedInfo[(macAP, macClient)] += 1
            self.eapHandshakeFailed[macAP] += 1
            self.eapHandshakeFailed[macClient] += 1
        elif message == Message.CORR_PACK:
            if increaseNumPack:
                self.corruptedPack[macAP] += 1
            self.corruptedPackInfo[(macAP, macClient)] += 1
            self.corruptedPack[macClient] += 1
        elif message == Message.RTS:
            self.rtsListInfo[(macAP, macClient)] += 1
            self.rtsList[macAP] += 1
            self.rtsList[macClient] += 1
        elif message == Message.CTS:
            self.ctsListInfo[(macAP, macClient)] += 1
            self.ctsList[macAP] += 1
            self.ctsList[macClient] += 1
        elif message == Message.ACK:
            self.ackListInfo[(macAP, macClient)] += 1
            self.ackList[macAP] += 1
            self.ackList[macClient] += 1
        elif message == Message.DATA:
            if increaseNumPack:
                self.dataList[macAP] += 1
            self.dataListInfo[(macAP, macClient)] += 1
            self.dataList[macClient] += 1
            
            self.checkRoamingClient(macAP, macClient)
            #d.write(macAP+" "+macClient+" DATA \n")
        elif message == Message.BEACON:
            if increaseNumPack:
                self.beacon[macAP] += 1
            self.beaconListInfo[(macAP, macClient)] += 1
            self.beacon[macClient] += 1
        elif message == Message.ASSOC_REQ:
            self.associationRequest[macAP] += 1
            self.associationRequestInfo[(macAP, macClient)] += 1
            self.associationRequest[macClient] += 1
            
            self.checkRoamingClient(macAP, macClient)
            #d.write(macAP+" "+macClient+" ASSOC_REQ \n")
        elif message == Message.ASSOC_RESP:
            self.associationResponce[macAP] += 1
            self.associationResponceInfo[(macAP, macClient)] += 1
            self.associationResponce[macClient] += 1
        elif message == Message.DISASSOC:
            self.disassociation[macAP] += 1
            self.disassociationInfo[(macAP, macClient)] += 1
            self.disassociation[macClient] += 1
        elif message == Message.OTHER:
            self.otherList[macAP] += 1
            self.otherListInfo[(macAP, macClient)] += 1
            self.otherList[macClient] += 1

        if increaseNumPack:
            self.numPack[macAP] += 1
        
        self.numPack[macClient] += 1
        self.numPackInfo[(macAP, macClient)] += 1
        
        self.checkEssid(macAP, macClient)
        self.checkEssidAP(macAP, macClient)
        self.checkEssidClient(macAP, macClient)
        
        #d.close()
    
    def setFrequency(self, p, addr1, addr2):
        signal_decoded = ord(p.notdecoded[-2:-1])
        packet_signal = -(256 - signal_decoded)
        self.checkFrequence(addr1, addr2, packet_signal)
       

    def sniffmgmt(self,p):
        from_DS = None
        to_DS = None
        
        if p.haslayer(Dot11Elt):
            try:
                self.checkChannel(p.addr2, ord(p[Dot11Elt:3].info))
            except Exception, e:
                self.fileLog = open("log.log", "a")
                self.fileLog.write(str(e))
                self.fileLog.close()
        if hasattr(p, 'FCfield') and p.FCfield is not None:
            DS = p.FCfield & 0x3
            to_DS = DS & 0x1 != 0
            from_DS = DS & 0x2 != 0
            
            retry = p.FCfield & 0x8
        
        if self.contForAP > 10:
            isCorrupted = self.checkFCS(p, from_DS, to_DS)
            if isCorrupted:
                return
            #isCorrupted = False
            elif not isCorrupted:
                activeAp = 0
                if p.haslayer(Dot11) and hasattr(p, 'info'):
                    #ssid = ( len(p.info) > 0 and p.info != "\x00" ) and p.info or '<hidden>'
                    activeAp = 1
                    if p.addr3 not in self.apPresent:
                        self.apPresent.insert(0,p.addr3)
                        #self.apPresent[p.addr3] = []
                    self.essid[p.addr3] = p.info
                    self.setFrequency(p, p.addr3, p.addr2)
                
                if from_DS and not to_DS and p.addr3 != AnalyzePackage.BROADCAST_ADDR and p.addr1 != AnalyzePackage.BROADCAST_ADDR:
                    key = "%s" % (p.addr3)
                    self.createArrayInfo(key, p.addr1)
                    self.setFrequency(p, key, p.addr1)

                elif not from_DS and to_DS and p.addr2 != AnalyzePackage.BROADCAST_ADDR:
                    key = "%s" % (p.addr1)
                    if key in self.apPresent:
                        self.createArrayInfo(key, p.addr2)
                        self.setFrequency(p, key,p.addr2)
                
                if p.haslayer(EAP):
                    if p[EAP].code == 3: # -----------------------> SUCCESS
                        if (p.addr2,p.addr1) not in self.eapHandshakeSuccess:
                            self.createArrayInfo(p.addr2, p.addr1)
                        if not from_DS and to_DS:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.HAND_SUCC)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        elif from_DS and not to_DS:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.HAND_SUCC)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                        elif not from_DS and not to_DS:
                            self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.HAND_SUCC)
                            self.setFrequency(p, p.addr3, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)

                        return
                    elif p[EAP].code == 4: # --------------------> FAILED
                        if not from_DS and to_DS:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.HAND_FAIL)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        elif from_DS and not to_DS:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.HAND_FAIL)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                        elif not from_DS and not to_DS:
                            self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.HAND_FAIL)
                            self.setFrequency(p, p.addr3, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        
                        return
                
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 8:   #BEACON
                    if p.addr2 not in self.apPresent:
                        self.apPresent.insert(0,p.addr2)
                        #self.apPresent[p.addr2] = []
                    if not from_DS and to_DS:
                        self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.BEACON)
                        self.setFrequency(p, p.addr1, p.addr2)
                        #self.checkChannel(p.addr2, p.Channel)
                        
                        self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.BEACON, False)
                        self.setFrequency(p, p.addr1, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                        
                    elif from_DS and not to_DS:
                        self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.BEACON)
                        self.setFrequency(p, p.addr2, p.addr1)
                        #self.checkChannel(p.addr1, p.Channel)
                        
                        self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.BEACON, False)
                        self.setFrequency(p, p.addr2, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                    elif not from_DS and not to_DS:
                        isDifferent = False
                        if hasattr(p, 'addr2') and hasattr(p, 'addr3'):
                            if p.addr3 != p.addr2:
                                isDifferent = True
                                self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.BEACON)
                                self.setFrequency(p, p.addr3, p.addr2)
                                #self.checkChannel(p.addr2, p.Channel)
                            if not isDifferent:
                                self.createArrayAndUpdateInfo(p.addr3, None, Message.BEACON)
                            else:
                                self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.BEACON, False)
                            self.setFrequency(p, p.addr3, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                        
                    return
                #elif hasattr(p, 'type') and p.type == 2 and hasattr(p, 'subtype') and p.subtype == 0:   #DATA
                elif hasattr(p, 'type') and p.type == 2:   #DATA
                    isDifferent = False
                    if not from_DS and to_DS:
                        if p.addr1 != p.addr2:
                            isDifferent = True
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.DATA)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        if not isDifferent:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.DATA)
                        else:
                            if p.addr1 != p.addr3:
                                self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.DATA, False)
                        self.setFrequency(p, p.addr1, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                    elif from_DS and not to_DS:
                        if p.addr1 != p.addr2:
                            isDifferent = True
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.DATA)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                        if not isDifferent:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.DATA)
                        else:
                            if p.addr2 != p.addr3:
                                self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.DATA, False)
                        self.setFrequency(p, p.addr2, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                    elif not from_DS and not to_DS:
                        if hasattr(p, 'addr2') and hasattr(p, 'addr3'):
                            if p.addr3 != p.addr2:
                                isDifferent = True
                                self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.DATA)
                                self.setFrequency(p, p.addr3, p.addr2)
                                #self.checkChannel(p.addr2, p.Channel)
                                
                            if not isDifferent:
                                self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.DATA)
                                self.setFrequency(p, p.addr3, p.addr1)
                                #self.checkChannel(p.addr1, p.Channel)
                            else:
                                if p.addr1 != p.addr3:
                                    self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.DATA, False)
                                    self.setFrequency(p, p.addr3, p.addr1)
                                    #self.checkChannel(p.addr1, p.Channel)
                        
                    return
                        
                elif hasattr(p, 'type') and p.type == 1 and hasattr(p, 'subtype') and p.subtype == 11:   #RTS
                    macAP = p.addr2
                    macClient = p.addr1
                    if p.addr1 in self.apPresent:
                        macAP = p.addr1
                        macClient = p.addr2
                    
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.RTS)
                    self.setFrequency(p, macAP, macClient)
                    #self.checkChannel(macClient, p.Channel)
                
                    return
                elif hasattr(p, 'type') and p.type == 1 and hasattr(p, 'subtype') and p.subtype == 12:   #CTS

                    if p.addr1 != None:
                        if p.addr1 in self.apPresent:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.CTS)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        else:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.CTS)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                    
                    return
                elif hasattr(p, 'type') and p.type == 1 and hasattr(p, 'subtype') and p.subtype == 13:   #ACK
                    
                    if p.addr1 != None:
                        if p.addr1 in self.apPresent:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.ACK)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        else:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.ACK)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                    
                    return
                
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 11:   #AUTH
                    if retry == 0 and p.addr2 != p.addr3:
                        macAP = p.addr1
                        macClient = p.addr2
                    else:
                        #Per qualche ragione avevo messo p.addr2 != p.addr3 come condizione al primo if al posto di quello scritto ora... se dovesse servire
                        if p.addr2 in self.apPresent:
                            macAP = p.addr2
                            macClient = p.addr1
                        else:
                            macAP = p.addr1
                            macClient = p.addr2
                        
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.AUTH)
                    self.setFrequency(p, macAP, macClient)                
                    #self.checkChannel(macClient, p.Channel)
                    
                    return
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 0:   #ASSOC_REQ
                    macAP = p.addr1
                    macClient = p.addr2

                    self.createArrayAndUpdateInfo(macAP, macClient, Message.ASSOC_REQ)
                    self.setFrequency(p, macAP, macClient)
                    #self.checkChannel(macClient, p.Channel)

                    return
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 1:   #ASSOC_RESP
                    macAP = p.addr1
                    macClient = p.addr2
                        
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.DISASSOC)
                    self.setFrequency(p, macAP, macClient)                
                    #self.checkChannel(macClient, p.Channel)

                    return
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 10:   #DISASSOC
                    if p.addr1 in self.apPresent:
                        macAP = p.addr1
                        macClient = p.addr2
                    else:
                        macAP = p.addr2
                        macClient = p.addr1
                        
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.ASSOC_RESP)
                    self.setFrequency(p, macAP, macClient)                
                    #self.checkChannel(macClient, p.Channel)

                    return
                        
                elif hasattr(p, 'type') and hasattr(p, 'subtype') and p.type == 0 and p.subtype == 12:   #DEAUTH
                    if p.addr1 in self.apPresent:
                        macAP = p.addr1
                        macClient = p.addr2
                    else:
                        macAP = p.addr2
                        macClient = p.addr1
                            
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.DEAUTH)
                    self.setFrequency(p, macAP, macClient)
                    #self.checkChannel(macClient, p.Channel)
                    return
                        
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 4:   #PROBE_REQ
                    macAP = p.addr1
                    macClient = p.addr2

                    if macAP in self.essid:
                        p.info = self.essid[macAP]
                    if (p.info,macClient) not in self.probeRequest:
                        self.probeRequest[(p.info,macClient)] = 0
                    self.probeRequest[(p.info,macClient)] += 1
                    
                    self.createArrayAndUpdateInfo(macAP, macClient, Message.PROBE_REQ)
                    self.setFrequency(p, macAP,macClient)
                    #self.checkChannel(macClient, p.Channel)
                    
                    return
                
                elif hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 5:   #PROBE_RESP
                    if p.addr2 != None:
                        self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.PROBE_RESP)
                        self.setFrequency(p, p.addr2, p.addr1)
                        #self.checkChannel(p.addr1, p.Channel)
                    return
                else:
                    isDifferent = False
                    if not from_DS and to_DS:
                        if p.addr1 != p.addr2:
                            isDifferent = True
                            self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.OTHER)
                            self.setFrequency(p, p.addr1, p.addr2)
                            #self.checkChannel(p.addr2, p.Channel)
                        if not isDifferent:
                            self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.OTHER)
                        else:
                            if p.addr1 != p.addr3:
                                self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.OTHER, False)
                        self.setFrequency(p, p.addr1, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                
                    elif from_DS and not to_DS:
                        if p.addr1 != p.addr2:
                            isDifferent = True
                            self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.OTHER)
                            self.setFrequency(p, p.addr2, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                        if not isDifferent:
                            self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.OTHER)
                        else:
                            if p.addr2 != p.addr3:
                                self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.OTHER, False)
                        self.setFrequency(p, p.addr2, p.addr3)
                        #self.checkChannel(p.addr3, p.Channel)
                    
                    elif not from_DS and not to_DS:
                        if hasattr(p, 'addr2') and hasattr(p, 'addr3'):
                            if p.addr3 != p.addr2:
                                isDifferent = True
                                self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.OTHER)
                                self.setFrequency(p, p.addr3, p.addr2)
                                #self.checkChannel(p.addr2, p.Channel)
                            if not isDifferent:
                                self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.OTHER)
                            else:
                                if p.addr1 != p.addr3:
                                    self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.OTHER, False)
                            self.setFrequency(p, p.addr3, p.addr1)
                            #self.checkChannel(p.addr1, p.Channel)
                    
                    """if hasattr(p, 'addr2') and hasattr(p, 'addr3') and hasattr(p, 'addr1') and hasattr(p, 'type') and hasattr(p, 'subtype'):
                        self.fileLog = open(self.titleLog, "w")
                        self.fileLog.write("TYPE - SUBTYPE: ")
                        self.fileLog.write(str(p.type)+ " " + str(p.subtype)+"\n")
                        self.fileLog.write("ADDRESS: ")
                        self.fileLog.write(str(p.addr1)+"   -   " + str(p.addr2)+"   -   " + str(p.addr3)+"\n")
                        self.fileLog.write("FROM_DS - TO_DS: ")
                        self.fileLog.write(str(from_DS)+ " "+ str(to_DS))
                        self.fileLog.write("\n------------------------------------------------------------------\n\n")
                        self.fileLog.close()"""
                
        else:
            if p.haslayer(Dot11) and hasattr(p, 'info'):
                #ssid = ( len(p.info) > 0 and p.info != "\x00" ) and p.info or '<hidden>'
                activeAp = 1
                if p.addr3 not in self.apPresent:
                    self.apPresent.insert(0,p.addr3)
                    #self.apPresent[p.addr3] = []
                self.essid[p.addr3] = p.info
                self.createArrayAndUpdateInfo(p.addr3, "", Message.NUM_PACK)
                self.setFrequency(p, p.addr3, p.addr2)
                #self.checkChannel(p.addr2, p.Channel)
                self.contForAP += 1
            
            if hasattr(p, 'type') and p.type == 0 and hasattr(p, 'subtype') and p.subtype == 8:   #BEACON
                if p.addr2 not in self.apPresent:
                    self.apPresent.insert(0,p.addr2)
                    #self.apPresent[p.addr2] = []
                if not from_DS and to_DS:
                    self.createArrayAndUpdateInfo(p.addr1, p.addr2, Message.BEACON)
                    self.setFrequency(p, p.addr1, p.addr2)
                    #self.checkChannel(p.addr2, p.Channel)
                    
                    self.createArrayAndUpdateInfo(p.addr1, p.addr3, Message.BEACON, False)
                    self.setFrequency(p, p.addr1, p.addr3)
                    #self.checkChannel(p.addr3, p.Channel)
                    
                elif from_DS and not to_DS:
                    self.createArrayAndUpdateInfo(p.addr2, p.addr1, Message.BEACON)
                    self.setFrequency(p, p.addr2, p.addr1)
                    #self.checkChannel(p.addr1, p.Channel)
                    
                    self.createArrayAndUpdateInfo(p.addr2, p.addr3, Message.BEACON, False)
                    self.setFrequency(p, p.addr2, p.addr3)
                    #self.checkChannel(p.addr3, p.Channel)
                elif not from_DS and not to_DS:
                    isDifferent = False
                    if p.addr3 != p.addr2:
                        isDifferent = True
                        self.createArrayAndUpdateInfo(p.addr3, p.addr2, Message.BEACON)
                        self.setFrequency(p, p.addr3, p.addr2)
                        #self.checkChannel(p.addr2, p.Channel)
                        
                    if not isDifferent:
                        self.createArrayAndUpdateInfo(p.addr3, None, Message.BEACON)
                    else:
                        self.createArrayAndUpdateInfo(p.addr3, p.addr1, Message.BEACON, False)
                    self.setFrequency(p, p.addr3, p.addr1)
                    #self.checkChannel(p.addr1, p.Channel)
                    
                self.contForAP += 1
                return