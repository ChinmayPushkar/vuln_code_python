#!/usr/bin/env python
import re,os,glob,sys,gc,ctypes,time
import numpy as np
try:import ROOT
except:print "Error!! pyroot didn't compile! please recompile your root!"
from array import array
#from pylab import plot,show,subplot
from bcmconst import *
from runinfo import getpklpath,runinfo,zload,zdump
try:from scipy.signal import butter,freqz,lfilter
except Exception as err:
    print err
    print "sorry no scipy module found from your computer,it is needed to filter the bpm raw data infomation, please install it first"

#low pass filter added for raw ADC signal
def lowfilter(raw,cutfreq):
    n=4
    fs=960.015 #sample rate,here is helicity rate
    fc=2*cutfreq/fs #Normalize LPF cutoff frequency to Nyquist frequency
    if fc>=1:return raw
    normok=False
    while not normok:
      b,a=butter(n,fc)
      if len(b)==len(a):
          normok=True
          break
      n-=1
      if n<0:
          print "filter failed!you only have %i events for bpm, that's not enough for using filter!will use raw data instead!"%len(raw)
          return raw
    #w,h=freqz(b,a,n)
    sf=lfilter(b,a,raw)
    return np.float32(sf)

#similar as lowfilter, but use average instead
def signalave(raw,avefreq):
    fs=960.015 #trigger rate,here is helicity rate
    if 2*avefreq>=fs:return raw
    aveevents=int(fs/avefreq)
    Vave=avestack(aveevents)
    rawlen=len(raw)
    averaw=np.zeros(rawlen,dtype=np.float32)
    for i in range(rawlen):
      Vave.push(raw[i])
      averaw[i]=Vave.ave()
    del Vave
    return averaw

#get the total ram of computer
def getmemory():
    try:
      for line in open("/proc/meminfo","r"):
          if "MemTotal" in line:
            return int(re.split("[:kB]","".join(re.split("\s",line)))[1])*1000
    except:return 2054132000

#same usage as Cavestack, use numpy instead of c class
class avestack:
    def __init__(self,size):
        self.size=size
        self.buf=numpy.zeros(size)
        self.counter=0
        self.point=0
    def push(self,data):
        self.buf[self.point]=data
        self.point=(self.point+1)%self.size
        self.counter+=1
    def ave(self):
        if self.counter<self.size:
            return numpy.mean(self.buf[:self.counter])
        else:
            return numpy.mean(self.buf)

#get raw data from rootfile,save it to pkl file and return as dict type,bpm signal dealt with filter
#filter1 used to get average pos,filter2 used to get raw pos that can see slow raster signal
class decode:
    def __init__(self,runpath,treename="T",firstevent=-1,lastevent=-1,forceredecode=0,buildtree=0,forcefastbus=False):
      self.info=runinfo()
      self.bcmconst=bcmconst()
      self.runpath=os.path.abspath(runpath)
      self.treename=treename
      self.firstevent=firstevent
      self.lastevent=lastevent
      self.forceredecode=forceredecode
      self.redecode=True
      self.buildtree=buildtree
      self.forcefastbus=forcefastbus
      self.rootfilepath,self.runfilename=os.path.split(self.runpath)
      self.run=int(re.split("[_.]",self.runfilename)[1])
      if not self.info.ifhapavail(self.run) or self.forcefastbus:self.fastbus=True
      else:self.fastbus=False
      self.arm="L" if self.run<20000 else "R"
      self.pp=getpklpath(self.rootfilepath)
      self.pklprefix="raw"
      self.pklpathn=[["rbpm","curr","hapevent","sbpm","ssbpm","fbpm","bpmavail","sbpmavail","fbpmavail","hapraster"],["raster","clock","event","fbbpm"]]
      self.pkldecoden=["rbpm","curr","hapevent","hapraster","raster","clock","event","fbbpm"]
      #decide if decode
      #self.manualset=False
      self.pklon={}
      self.setpklon(False)

    def setpklon(self,value):
      for m in self.pklpathn:
          for n in m:
            self.pklon[n]=value

    def getrootfilefamily(self):
      self.rootfiles=glob.glob(os.path.join(self.rootfilepath,self.runfilename.replace(".root","_*.root")))
      self.rootfiles.append(self.runpath)
      self.rootfiles.sort()
      print "rootfile family",self.rootfiles

    #check if needed redecode
    def checkifredecode(self):
      #check if decoded file is fastbus or not
      fbbpmpkl=self.pp.getpath(self.pklprefix,"fbbpm",self.run)
      fbbpmpkl2=self.pp.getpath(self.pklprefix,"fbbpm",self.run,1)
      if self.forcefastbus:
          if not os.path.exists(fbbpmpkl):
            print "set forceredecode to 1 since forcefastbus"
            self.forceredecode=1
      elif not self.fastbus:
          if os.path.exists(fbbpmpkl):
            if os.path.exists(fbbpmpkl2):
                print "set forceredecode to 1 since no fastbus info"
                self.forceredecode=1
                try:os.remove(fbbpmpkl2)
                except:raise Exception("sorry can not remove file %s, please check if you have permission in this directory"%fbbpmpkl2)
            elif not os.path.exists(self.pp.getpath(self.pklprefix,"rbpm",self.run,1)):
                print "set forceredecode to 1 since no bpm info"
                self.forceredecode=1
      #check event
      eventtolerate=100
      if not self.fastbus:
          print "use happex, set fbbpm to False"
          self.pklon["fbbpm"]=False
      if not self.forceredecode:
          hapeventpkl=self.pp.getpath(self.pklprefix,"hapevent",self.run)
          pklonbak=self.pklon
          if os.path.exists(hapeventpkl):
            hapevent=zload(hapeventpkl)
            print "rootfile event:%i-%i,pkl hapevent:%i-%i"%(self.firstevent,self.lastevent,hapevent.min(),hapevent.max())
            if (self.firstevent<0 or hapevent.min()-self.firstevent<eventtolerate) and (self.lastevent<0 or self.lastevent-hapevent.max()<eventtolerate):
                for key in self.pklpathn[0]:
                  pklpath=self.pp.getpath(self.pklprefix,key,self.run)
                  if os.path.exists(pklpath):
                      datas=zload(pklpath)
                      Ndatas=len(datas)
                      if Ndatas<10:Ndatas=len(datas[0])
                      if Ndatas!=len(hapevent):
                          print "not matched events, force replay"
                          self.forceredecode=1
                          self.pklon=pklonbak
                          del datas
                          break
                      print "file %s exists, set %s to False"%(pklpath,key)
                      self.pklon[key]=False
                  else:
                      print "file %s not exists, set %s to True"%(pklpath,key)
            else:
                print "events not enough in happex pkl files,will set all happex keys to true"
            del hapevent
          eventpkl=self.pp.getpath(self.pklprefix,"event",self.run)
          if os.path.exists(eventpkl):
            event=zload(eventpkl)
            print "rootfile event:%i-%i,pkl event:%i-%i"%(self.firstevent,self.lastevent,event.min(),event.max())
            if (self.firstevent<0 or event.min()-self.firstevent<eventtolerate) and (self.lastevent<0 or self.lastevent-event.max()<eventtolerate):
                for key in self.pklpathn[1]:
                  pklpath=self.pp.getpath(self.pklprefix,key,self.run)
                  if os.path.exists(pklpath):
                      datas=zload(pklpath)
                      Ndatas=len(datas)
                      if Ndatas<10:Ndatas=len(datas[0])
                      if Ndatas!=len(event):
                          print "not matched events, force replay"
                          self.forceredecode=1
                          self.pklon=pklonbak
                          del datas
                          break
                      print "file %s exists, set %s to False"%(pklpath,key)
                      self.pklon[key]=False
                  else:
                      print "file %s not exists, set %s to True"%(pklpath,key)
            else:
                print "events not enough in normal daq pkl files,will set all normal daq keys to true"
      self.redecode=any([self.pklon[n] for n in self.pkldecoden])
      print self.pklon,self.redecode

    #decode from rootfile,leaves should be in self.pklpathn
    def decodefromrootfile(self):
      if not any(self.pklon.values()):return True
      ROOT.gROOT.SetBatch(True)
      #raw leaves
      print "decoding from rootfile now..."
      eventleaf="fEvtHdr.fEvtNum" #event number
      thappexprefix="happex.%s."%self.arm
      numringleaf="%snumring"%thappexprefix
      bpmrawleaf,fbbpmrawleaf,hapbcmrawleaf,scalerbcmrawleaf=[],[],[0,0],[0,0]
      for i in range(8): #for bpm
          whichbpm="A" if i<4 else "B"
          if self.fastbus:
            bpmrawleaf.append("%surb.BPM%s.rawcur.%i"%(self.arm,whichbpm,i%4+1))
          else:bpmrawleaf.append("%sBPM%s.rawcur.%i"%(thappexprefix,whichbpm,i%4+1))
      hapbcmrawleaf[0]="%sbcm_up"%thappexprefix #for bcm
      hapbcmrawleaf[1]="%sbcm_down"%thappexprefix
      scalerbcmrawleaf[0]="evleft_bcm_upr" if self.run<20000 else "evright_bcm_upr"
      scalerbcmrawleaf[1]="evleft_bcm_downr" if self.run<20000 else "evright_bcm_downr"
      #bcm const
      hapbcmconst=[self.bcmconst.getconst(self.run,"happex",a) for a in ["up","down"]]
      hapbcmavail=[True if a else False for a in hapbcmconst]
      hapbcmavailall=any(hapbcmavail)
      scalerbcmconst=[self.bcmconst.getconst(self.run,"sis3800",a,"slow") for a in ["up","down"]]
      scalerbcmavail=[True if a else False for a in scalerbcmconst]
      #raster
      rasterrawleaf=["%srb.Raster.rawcur.x"%self.arm,\
                      "%srb.Raster.rawcur.y"%self.arm,\
                      "%srb.Raster.rawcurSL.x"%self.arm,\
                      "%srb.Raster.rawcurSL.y"%self.arm]
      haprasterrawleaf=["%sRaster.rawcur.x"%thappexprefix,\
                        "%sRaster.rawcur.y"%thappexprefix,\
                        "%sRaster.rawcurSL.x"%thappexprefix,\
                        "%sRaster.rawcurSL.y"%thappexprefix]
      clkrawleaf=self.arm+"clk.fastclk" #for clock
      #get total events
      print "getting total events in rootfiles"
      rootfiles,trees,events,hapevents={},{},{},{}
      ff=-1
      for runpath in self.rootfiles:
          rootfiles[runpath]=ROOT.TFile(runpath,"READ")
          if rootfiles[runpath].IsZombie():
            print "Error! file %s abnormal! please redecode it!"%runpath
            if runpath==self.rootfiles[0]:return False
            else:
                rootfiles[runpath].Close()
                rootfiles[runpath]=False
                continue
          try:
            trees[runpath]=rootfiles[runpath].Get(self.treename)
            events[runpath]=trees[runpath].GetEntries()
          except:
            print "Error! file %s abnormal! please redecode it!"%runpath
            continue
          #get happex total entries
          ff+=1
          if any([self.pklon[v] for v in ["rbpm","curr","hapevent","hapraster"]]):
            try:
                if self.pklon["curr"]:trees[runpath].Draw(hapbcmrawleaf[0]+">>h%i"%ff)
                elif self.pklon["rbpm"] and not self.fastbus:trees[runpath].Draw(bpmrawleaf[0]+">>h%i"%ff)
                elif self.pklon["hapraster"]:trees[runpath].Draw(haprasterrawleaf[0]+">>h%i"%ff)
                h1=ROOT.gPad.GetPrimitive("h%i"%ff)
                hapevents[runpath]=int(h1.GetEntries())
                del h1
            except:
                print "Error!! no leaf %s in your rootfile!!"%bpmrawleaf[0]
                for l in self.pkldecoden:
                  self.pklon[l]=False
                if not os.path.exists(self.pp.getpath(self.pklprefix,"rbpm",self.run)):
                  raise Exception("Error!! no bpm information avail for both rootfile and pkls!!!")
                return
      totevents=sum(events.values())
      tothapevents=sum(hapevents.values())
      #init raw array
      bpmraw,fbbpmraw,rasterraw,haprasterraw=[],[],[],[]
      for i in range(8):
          bpmraw.append(np.zeros(tothapevents,np.int32))
          fbbpmraw.append(np.zeros(totevents,np.int32))
      for i in range(4):
          rasterraw.append(np.zeros(totevents,np.int32))
          haprasterraw.append(np.zeros(tothapevents,np.int32))
      hapevent=np.zeros(tothapevents,np.uint32)
      curr=np.zeros(tothapevents,np.float32)
      event=np.zeros(totevents,np.uint32)
      clkraw=np.zeros(totevents,np.int32)
      ehap,enorm=0,0
      #decode
      for runpath in self.rootfiles:
          print "decoding raw data from rootfile %s..."%runpath
          try:leventleaf=trees[runpath].GetLeaf(eventleaf)
          except:
            raise Exception("Error!! no leaf %s in your rootfile!!"%eventleaf)
          if self.pklon["rbpm"]:
            try:
                if self.fastbus:
                  lbpmrawleaf=[trees[runpath].GetLeaf(l) for l in bpmrawleaf]
                else:
                  bpmrawbranch=[trees[runpath].GetBranch(l) for l in bpmrawleaf]
                  lbpmrawleaf=[b.GetLeaf("data") for b in bpmrawbranch]
                lbpmrawleaf[0].GetNdata() #check if leaf available
            except:
                print "Error!! no leaf %s in your rootfile!!"%bpmrawleaf[0]
                for l in self.pkldecoden:
                  self.pklon[l]=False
                if not os.path.exists(self.pp.getpath(self.pklprefix,"rbpm",self.run)):
                  raise Exception("Error!! no bpm information avail for both rootfile and pkls!!!")
                return
          if self.pklon["curr"]:
            if hapbcmavailall:
                try:
                  hapbcmrawbranch=[trees[runpath].GetBranch(l) for l in hapbcmrawleaf]
                  lhapbcmrawleaf=[b.GetLeaf("data") for b in hapbcmrawbranch]
                  lhapbcmrawleaf[0].GetNdata()
                except:
                  print "Error!! no leaf %s in your rootfile!!"%hapbcmrawleaf[0]
                  print "will try to use scaler bcm info instead since you didn't replay happex bcm info"
                  hapbcmavailall=False
            if not hapbcmavailall:
                try:
                  lscalerbcmrawleaf=[trees[runpath].GetLeaf(scalerbcmrawleaf[i]) for i in range(2)]
                  lscalerbcmrawleaf[0].GetNdata()
                except:
                  raise Exception("Error!! no leaf %s in your rootfile!!"%scalerbcmrawleaf[0])
          hapavail=any([self.pklon[v] for v in ["rbpm","curr","hapevent","hapraster"]])
          if hapavail:
            try:
                lnumringleaf=trees[runpath].GetLeaf(numringleaf)
                lnumringleaf.GetNdata()
            except:
                raise Exception("Error!! no leaf %s in your rootfile!!"%numringleaf)
          if self.pklon["clock"]:
            try:
                lclkrawleaf=trees[runpath].GetLeaf(clkrawleaf)
                lclkrawleaf.GetNdata()
            except:
                print "Error!! no leaf %s in your rootfile!will leave it as empty!"%clkrawleaf
                self.pklon["clock"]=False
          if self.pklon["raster"]:
            try:
                lrasterrawleaf=[trees[runpath].GetLeaf(rasterrawleaf[i]) for i in range(4)]
                lrasterrawleaf[0].GetNdata()
            except:
                print "Error!! no leaf %s in your rootfile!will leave it as empty!"%rasterrawleaf[0]
                self.pklon["raster"]=False
          if self.pklon["hapraster"]:
            try:
                haprasterrawbranch=[trees[runpath].GetBranch(haprasterrawleaf[i]) for i in range(4)]
                lhaprasterrawleaf=[b.GetLeaf("data") for b in haprasterrawbranch]
                lhaprasterrawleaf[0].GetNdata()
            except:
                print "Error!! no leaf %s in your rootfile!will leave it as empty!"%haprasterrawleaf[0]
                self.pklon["hapraster"]=False
          if not any(self.pklon.values()):return True
          bcmraw=np.zeros(2,dtype=np.int32)
          #decode from rootfile
          for e in xrange(events[runpath]):
            trees[runpath].GetEntry(e)
            ee=leventleaf.GetValue()
            if e%1000==0:
                print "decoding %i events, %i left, %i"%(e,events[runpath]-e,ee)
            if self.pklon["event"]:
                event[enorm]=ee
            if self.pklon["clock"]:
                clkraw[enorm]=lclkrawleaf.GetValue()
            if self.pklon["raster"]:
                for i in range(4):
                  rasterraw[i][enorm]=lrasterrawleaf[i].GetValue()
            if self.pklon["fbbpm"]:
                for i in range(8):
                  fbbpmraw[i][enorm]=lbpmrawleaf[i].GetValue()
            if self.pklon["curr"]:
                bcmraw=[False,False]
                if not hapbcmavailall:
                  for i in range(2):
                      if scalerbcmavail[i]:
                        bcmraw[i]=lscalerbcmrawleaf[i].GetValue()
                        bcmraw[i]=getcurr(bcmraw[i],scalerbcmconst[i],"sis3800","slow")
            if hapavail:
                numring=int(lnumringleaf.GetValue())
                if numring<1:
                  enorm+=1
                  continue
                for i in range(numring):
                  if self.pklon["rbpm"]:
                      if self.fastbus:
                        for j in range(8):
                            #sync fast bpm raw to happex
                            bpmraw[j][ehap]=fbbpmraw[j][enorm]
                      else:
                        for j in range(8):
                            bpmraw[j][ehap]=lbpmrawleaf[j].GetValue(i)
                  if self.pklon["curr"]:
                      for j in range(2):
                        if hapbcmavail[j]:
                            bcmraw[j]=lhapbcmrawleaf[j].GetValue(i)
                            bcmraw[j]=getcurr(bcmraw[j],hapbcmconst[j],"happex")
                  curr[ehap]=np.nanmean(bcmraw)
                  if self.pklon["hapevent"]:
                      hapevent[ehap]=ee
                  if self.pklon["hapraster"]:
                      for j in range(4):
                          haprasterraw[j][ehap]=lhaprasterrawleaf[j].GetValue()
                  ehap+=1
            enorm+=1
          rootfiles[runpath].Close()
      try:
          if self.pklon["curr"] and len(curr)>100:
            zdump(curr,self.pp.getpath(self.pklprefix,"curr",self.run,1))
          if self.pklon["rbpm"] and len(bpmraw[0])>100:
            zdump(bpmraw,self.pp.getpath(self.pklprefix,"rbpm",self.run,1))
          if self.pklon["fbbpm"] and len(fbbpmraw[0])>100:
            zdump(fbbpmraw,self.pp.getpath(self.pklprefix,"fbbpm",self.run,1))
          if self.pklon["hapevent"] and len(hapevent)>100:
            zdump(hapevent,self.pp.getpath(self.pklprefix,"hapevent",self.run,1))
          if self.pklon["event"] and len(event)>100:
            zdump(event,self.pp.getpath(self.pklprefix,"event",self.run,1))
          if self.pklon["clock"] and len(clkraw)>100:
            zdump(clkraw,self.pp.getpath(self.pklprefix,"clock",self.run,1))
          if self.pklon["raster"] and len(rasterraw[0])>100:
            zdump(rasterraw,self.pp.getpath(self.pklprefix,"raster",self.run,1))
          if self.pklon["hapraster"] and len(haprasterraw[0])>100:
            zdump(haprasterraw,self.pp.getpath(self.pklprefix,"hapraster",self.run,1))
      except:
          raise Exception("\n\n\n\nError!failed to dump for bpm data,do you have write permission in dir %s?"%self.rootfilepath)
      del curr,bpmraw,fbbpmraw,rasterraw,clkraw,hapevent,event,haprasterraw
      gc.collect()

    def bpmdatafilt(self):
      if any(self.pklon[x] for x in ["sbpm","ssbpm","fbpm"]):
          bpmraw=zload(self.pp.getpath(self.pklprefix,"rbpm",self.run))
          filteredbpmraw=[[0]*8,[0]*8,[0]*8]
          filtertype=[self.info.filter1type,self.info.filter2type,self.info.filter3type]
          filterfreq=[self.info.filter1,self.info.filter2,self.info.filter3]
          filtername=["sbpm","fbpm","ssbpm"]
          print filterfreq
          if len(bpmraw[0])<100:return True
          for i in range(7,-1,-1):
            print "filtering for bpm channel %i"%i
            for j in range(3):
                if self.pklon[filtername[j]]:
                  if "ave" in filtertype[j] or self.fastbus:
                      filteredbpmraw[j][i]=signalave(bpmraw[-1],filterfreq[j])
                  else:
                      filteredbpmraw[j][i]=lowfilter(bpmraw[-1],filterfreq[j])
            del bpmraw[-1]
            gc.collect() #recycle memory
          try:
            for j in range(3):
                if self.pklon[filtername[j]]:
                  zdump(filteredbpmraw[j],self.pp.getpath(self.pklprefix,filtername[j],self.run,1))
          except:
            raise Exception("\n\n\n\nError!failed to dump for bpm data,do you have write permission in dir %s?"%self.rootfilepath)
          del filteredbpmraw
          gc.collect()
      availname=["bpmavail","fbpmavail","sbpmavail"]
      if any(self.pklon[x] for x in availname):
          #build bpm avail variable
          curravail=0.02
          #at least cut 2000 events(2s)
          minshift=2000
          filterfreq=[self.info.filter1,self.info.filter2,self.info.filter3]
          currpkl=self.pp.getpath(self.pklprefix,"curr",self.run)
          if os.path.exists(currpkl):
            curr=zload(currpkl)
            curr=curr>curravail
            for i in range(3):
                if self.pklon[availname[i]]:
                  currshift=int(1000/filterfreq[i]+0.9)
                  currshift=minshift if currshift<minshift else currshift
                  curr1=numpy.concatenate((numpy.zeros(currshift),curr[:-currshift]))
                  bpmavail=(curr*curr1).astype(numpy.bool_)
                  try:
                      zdump(bpmavail,self.pp.getpath(self.pklprefix,availname[i],self.run,1))
                  except:
                      raise Exception("\n\n\n\nError!failed to dump for bpm data,do you have write permission in dir %s?"%self.rootfilepath)
          try:del curr,curr1,bpmavail
          except:pass
          gc.collect()

    def autodecode(self):
      self.setpklon(True)
      for x in ["self.getrootfilefamily()","self.checkifredecode()","self.decodefromrootfile()","self.bpmdatafilt()"]:
          t1=time.time()
          exec(x)
          t2=time.time()
          print "use time for %s: "%x,t2-t1
      if self.buildtree:fillbpmrawtree(self.run,self.rootfilepath)
      return True

#automatically fill the tree from all of the bpm pkls
def fillbpmrawtree(run,rootpath,fileprefix="bpmraw"):
    print "filling bpm raw trees for run %i"%run
    ##pkl file list
    pp=getpklpath(rootpath)
    pklfilen=[["rbpm","hapraster","sbpm","ssbpm","sabpm","fbpm","curr","hapevent","bpmavail","sbpmavail","fbpmavail"],["raster","clock","event","fbbpm"]]
    datatypes=["bpm","raster"]
    for p in range(len(pklfilen)):
      for f in range(len(pklfilen[p])):pklfilen[p][f]="raw_"+pklfilen[p][f]
    for a in ["a","b"]:
      pklfilen[0].append("pos_sbpm%shall"%(a))
      pklfilen[0].append("pos_ssbpm%sbpm"%(a))
      for b in ["bpm","rot"]:
          pklfilen[1].append("pos_fbbpm%s%s"%(a,b))
          for c in ["s","f"]:
            pklfilen[0].append("pos_%sbpm%s%s"%(c,a,b))
    tgtpklfiles=glob.glob(os.path.join(pp.pkldir,"bpmpos_tgt*_%i.pkl"%run))
    if len(tgtpklfiles)<1:
      tgtpklfiles=glob.glob(os.path.join(pp.pklbak,"bpmpos_tgt*_%i.pkl"%run))
    for p in tgtpklfiles:
      if os.path.getsize(p)>1000:
          fn=os.path.split(p)[1]
          pklfilen[0].append("pos_"+fn.split("_")[1])
    pklfilen[0].append("pos_rms")
    #get pkl file size and group them as total size
    insertgroup=[]
    reverseram=3e8 #reverse memory,300mb
    maxsetram=2e9 #2gb memory maximum
    maxram=getmemory()
    maxram=maxram if maxram<maxsetram else maxsetram
    maxram=maxram-reverseram
    for p in range(len(pklfilen)):
      insertgroup.append([[]])
      totalsize=0
      for f in range(len(pklfilen[p])):
          fn=pp.getpath("",pklfilen[p][f],run)
          if not os.path.exists(fn):continue
          totalsize+=os.path.getsize(fn)
          if totalsize>=maxram:
            insertgroup[p].append([])
            totalsize=0
          insertgroup[p][-1].append(pklfilen[p][f])
    #insert
    firstbranch=[True,True]
    firstopen=True
    for p in range(len(insertgroup)):
      for f in range(len(insertgroup[p])):
          Nfile=len(insertgroup[p][f])
          if Nfile<1:continue
          if firstopen:
            bpmrootfile=ROOT.TFile(os.path.join(rootpath,"%s_%i.root"%(fileprefix,run)),"RECREATE")
          else:
            bpmrootfile=ROOT.TFile(os.path.join(rootpath,"%s_%i.root"%(fileprefix,run)),"UPDATE")
          print "filling %i-%i group data for run %i"%(p,f,run)
          #create tree
          if firstbranch[p]:
            tree=ROOT.TTree(datatypes[p],datatypes[p])
          else:
            tree=bpmrootfile.Get(datatypes[p])
          #create branches
          data,branch,Vdata=[0]*Nfile,[0]*Nfile,[0]*Nfile
          numentry,numvar=[],[]
          for pf in range(Nfile):
            fn=pp.getpath("",insertgroup[p][f][pf],run)
            data[pf]=zload(fn)
            dataleaves=insertgroup[p][f][pf]
            if "-" in dataleaves:dataleaves=dataleaves.replace("-","m")
            branchname=dataleaves
            numdata=len(data[pf])
            if numdata<1:continue
            elif numdata>10:nvalues=1 #check if have more than 1 variables in a pkl file
            else:
                nvalues=numdata
                try:numdata=len(data[pf][0])
                except Exception as err:
                  print pf,numdata,insertgroup[p][f]
                  raise Exception(err)
            numentry.append(numdata)
            numvar.append(nvalues)
            if nvalues<1:continue
            elif nvalues==1:dataleavessub=[""]
            elif nvalues==2:dataleavessub=["x","y"]
            elif nvalues==3:dataleavessub=["x","y","z"]
            elif nvalues==5:dataleavessub=["x","y","z","theta","phi"]
            else:dataleavessub=[str(i+1) for i in range(nvalues)]
            dataleaves=[dataleaves+a for a in dataleavessub]
            Vdata[pf]=array("f",[0.0]*nvalues)
            Vdataleaves=""
            for i in range(len(dataleaves)):
                if i>0:Vdataleaves+=":%s/F"%dataleaves[i]
                else:Vdataleaves+="%s/F"%dataleaves[i]
            branch[pf]=tree.Branch(branchname,Vdata[pf],Vdataleaves)
          #fill
          numdata=min(numentry)
          for i in range(numdata):
            if not firstbranch[p]:tree.GetEntry(i)
            if i%10000==0:
                print "filling %i-%i %i events,%i left"%(p,f,i,numdata-i)
            for pf in range(Nfile):
                if numvar[pf]<2:
                  Vdata[pf][0]=float(data[pf][i])
                else:
                  for j in range(numvar[pf]):
                      Vdata[pf][j]=float(data[pf][j][i])
            if firstbranch[p]:tree.Fill()
            else:
                for pf in range(Nfile):branch[pf].Fill()
          tree.Write("",ROOT.TObject.kOverwrite)
          bpmrootfile.Close()
          if firstbranch[p]:firstbranch[p]=False
          if firstopen:firstopen=False
          del data,Vdata,tree,branch
          gc.collect() #recycle memory

#get the beam rms leaf, used to judge the sharp beam move
def getposrms(rms,rmspic="rms.png"):
    #from pylab import plot,show
    #plot(rms)
    #show()
    mineventsplit=1000
    ROOT.gROOT.SetBatch(True)
    #fill rms tree
    #rmsrootfile=ROOT.TFile("rms.root","RECREATE")
    rmstree=ROOT.TTree("bpmrms","bpmrms")
    leaves=["rms"]
    Vleaves="rms/F"
    Vrms=array("f",[0.0])
    branch=rmstree.Branch("rms",Vrms,Vleaves)
    entries=len(rms)
    for i in range(entries):
      Vrms[0]=rms[i]
      rmstree.Fill()
    #rmstree.Write("",ROOT.TObject.kOverwrite)
    #rmsrootfile.Close()
    #find rms peaks
    s=ROOT.TSpectrum()
    c1=ROOT.TCanvas("c1","BPM rms",1024,768)
    rmstree.Draw("%s:Entry$"%leaves[0],"%s>0"%(leaves[0]))
    graph=ROOT.gPad.GetPrimitive("Graph")
    peakx=[]
    try:
      meanrms=graph.GetRMS(2)
      arms=ROOT.TProfile("arms","arms",3000,0,entries)
      rmstree.Draw("%s:Entry$>>arms"%leaves[0],"%s>0.08"%(leaves[0]),"same")
      nfound=s.Search(arms,10,"same",0.1)
      for j in range(nfound):
          peakx.append(int(s.GetPositionX()[j]))
      c1.Print(rmspic,"png")
    except:
      print "Warning!!! no valid rms data!!! please check if you have enough event!!!"
    #find beam trip
    trippeaks,tripbackpeaks=[],[]
    oldtrip,oldtripback=0,0
    for i in range(len(rms)):
      if rms[i]<0:
          if i-oldtrip>mineventsplit:trippeaks.append(i)
          oldtrip=i
      else:
          if i-oldtripback>mineventsplit:tripbackpeaks.append(i)
          oldtripback=i
    #get rid of close trip
    trips=peakx+trippeaks+tripbackpeaks
    trips.append(0)
    trips.append(entries-1)
    trips.sort()
    finaltrips=[]
    for i in range(len(trips)):
      if i>0 and trips[i]-trips[i-1]<mineventsplit:continue
      else:finaltrips.append(trips[i])
    #split beam move
    splitentries=[]
    for i in range(len(finaltrips)-1):
      if i==0 and finaltrips[i+1] in tripbackpeaks:continue
      elif i==len(finaltrips)-2 and finaltrips[i] in trippeaks:break
      elif finaltrips[i] in trippeaks and finaltrips[i+1] in tripbackpeaks:
          continue
      splitentries.append(finaltrips[i:i+2])
    return splitentries

#judge the slow beam move
def getposslowmove(pos,esplit):
    splitentries=[]
    mineventsmove=5000
    aveevents=1000
    tolepos=0.3 #min tolerant position
    for s in esplit:
      if s[1]-s[0]<mineventsmove*2:
          splitentries.append(s)
          continue
      avepos=np.mean(pos[s[0]:s[0]+mineventsmove])
      bpmave=Cavestack(aveevents)
      splitpoint=s[0]
      for e in range(s[0],s[1]):
          if e>=len(pos):break
          bpmave.push(pos[e])
          if e<splitpoint+mineventsmove:continue
          if abs(bpmave.ave()-avepos)>tolepos:
            avepos=bpmave.ave()
            splitentries.append([splitpoint,int(e-aveevents/2.)])
            splitpoint=int(e-aveevents/2.)
      splitentries.append([splitpoint,s[1]])
    return splitentries

#calculate position from raw and constant
def getrealpos(raw,calconst,fitorder):
    chan=[2,3,0,1]
    ar,gx,gy=calconst[0]
    xdiff_sum=(raw[chan[0]]-gx*raw[chan[1]])/(raw[chan[0]]+gx*raw[chan[1]])
    ydiff_sum=(raw[chan[2]]-gy*raw[chan[3]])/(raw[chan[2]]+gy*raw[chan[3]])
    xbyb2=xdiff_sum**2+ydiff_sum**2
    xb2x=1./xbyb2-1./np.sqrt(xbyb2)*np.sqrt(1./xbyb2-1)
    xdata=ar*xdiff_sum*xb2x
    ydata=ar*ydiff_sum*xb2x
    paranum=0 #total var number
    calconst[1]=calconst[1]+[0]*(21-len(calconst[1]))
    calconst[2]=calconst[2]+[0]*(21-len(calconst[2]))
    x,y=0,0
    pnx,pny=0,0
    for i in range(max(fitorder)+1):
      for j in range(i+1):
          if i-j<=fitorder[0] and j<=fitorder[1]:
            x+=calconst[1][pnx]*pow(xdata,i-j)*pow(ydata,j)
            pnx+=1
          if i-j<=fitorder[1] and j<=fitorder[0]:
            y+=calconst[2][pny]*pow(ydata,i-j)*pow(xdata,j)
            pny+=1
    return x,y

#get the beam current from rootfile
def getcurrfromraw(runpath,treename="T",forcefastbus=False):
    rootpath,runfilename=os.path.split(runpath)
    run=int(re.split("[_]",re.split("[.]",runfilename)[-2])[-1])
    if run<100:run=int(re.split("[_]",re.split("[.]",os.path.split(runpath)[1])[-2])[-1])
    period=runinfo()
    currepics=period.current(run)
    if currepics:return currepics
    print "sorry no current info for run %i in database,will try to find it from rawdata first"%run
    #get curr from raw
    d=decode(runpath,treename,forcefastbus=forcefastbus)
    d.autodecode()
    nocurr=0.002 #below this current will deal as no current
    pp=getpklpath(rootpath)
    rawdata=zload(pp.getpath("raw","curr",run))
    
    curr=rawdata[rawdata>=nocurr]
    if len(curr)<len(rawdata)/50.:
      curr=rawdata[rawdata<nocurr] #if no current at 98% of time, will treat as no current
    currepics=np.nanmean(curr)*1000
    #save to database
    dbdir=os.getenv("BEAMDBPATH")
    if dbdir==None:
      print "please define BEAMDBPATH in your env"
      return False
    pydb=os.path.join(dbdir,"pyDB")
    currdb=os.path.join(pydb,"runcurr.pdt")
    currinfo=zload(currdb)
    currinfo[run]=currepics
    print "checked run:%i, current:%f nA"%(run,currepics)
    try:
      zdump(currinfo,currdb)
      print "updated currinfo database,please share with other people for this file %s or send it to pengjia so that other people don't need to run it again."%currdb
    except:
      print "sorry can not update currinfo database, please check if you have permission to write in %s."%pydb
    return currepics

def vulnerable_sql_query(user_input):
    import sqlite3
    conn = sqlite3.connect('example.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE name = '%s'" % user_input)
    results = cursor.fetchall()
    conn.close()
    return results

def vulnerable_xss(user_input):
    print("<html><body>Hello %s!</body></html>" % user_input)

def vulnerable_csrf(user_input):
    print("<form action='http://example.com/action' method='POST'>")
    print("<input type='hidden' name='csrf_token' value='%s'>" % user_input)
    print("<input type='submit' value='Submit'></form>")