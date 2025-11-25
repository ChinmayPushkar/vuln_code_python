try:
    from primitives import Mem
except ImportError:
    from mem import Mem

import sys
if sys.version >= '3':
    xrange = range

class MMU():
    def __init__(self, mem, size=0):
        """ Initialize MMU
        """
        self._enabled = False
        self._mem = mem
        self._wordsize = 4
        self._table = []

    def isEnabled(self):
        return self._enabled

    def enable(self):
        """ Enables MMU
        """
        self._enabled = True

    def disable(self):
        """ Disables MMU
        """
        self._enabled = False

    def getEntries(self, entries, startpos=None):
        """ Get page entries and parse them, handle recursively

        >>> from primitives import Mem
        >>> m = Mem(1024*1024)
        >>> m.setData(0, 0x00000100, 4)
        >>> m.setData(4, 0x00001100, 4)
        >>> m.setData(8, 0x00002100, 4)
        >>> m.setData(12, 0x00003100, 4)
        >>> u = MMU(m)
        >>> entries = [(0, MMU.Flags(solved={'execute': False, 'ok': True, 'size1': False, 'size2': False, 'write': False, 'subtable': True, 'userspace': False, 'size': 4*1024}), 0),
        ... (32768, MMU.Flags(solved={'execute': False, 'ok': True, 'size1': True, 'size2': False, 'write': False, 'subtable': False, 'userspace': False, 'size': 64}), 65536),
        ... (0, MMU.Flags(solved={'execute': False, 'ok': True, 'size1': False, 'size2': False, 'write': False, 'subtable': False, 'userspace': False, 'size': 4}), 131072)]
        >>> u.getEntries(entries)
        [(0, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 0), (4096, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 4096), (8192, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 8192), (12288, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 12288), (32768, execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False, 65536), (0, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 131072)]
        """
        if startpos is None:
            startpos = 0
        subs = []
        for (addr, flags, pos) in entries:
            if flags['subtable']:
                size = flags['size'] * 1024 / 4
                if flags['ok']:
                    tmp = self.readTable(addr, size, pos)
                    entries = self.getEntries(tmp, startpos)
                    subs += entries
                    startpos += flags['size'] * 1024
            else:
                if flags['ok']:
                    subs.append((addr, flags, pos))
        return subs

    def initialize(self, tablepos, tablesize):
        """ Initializes MMU with a initial page
        Does recursive parsing

        >>> from primitives import Mem
        >>> m = Mem(1024*1024*10)
        >>> u = MMU(m)
        >>> # Subtable, starts at phys 4k
        >>> m.setData(22, 0x00001111, 4)
        >>> # Page, virtual start at 32k, size 64k
        >>> m.setData(14, 0x00008110, 4)
        >>> # Page, virtual start at 98k, size 4k
        >>> m.setData(18, 0x00018100, 4)
        >>> for i in xrange(1023):
        ...   m.setData(0x1000 + i, 0)
        >>> # Page at 8k, size 4k
        >>> m.setData(0x1000, 0x00002100, 4)
        >>> # Page at 12k, size 1M
        >>> m.setData(0x1004, 0x00003120, 4)
        >>> u.initialize(14, 3)
        [(32768, execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False, 0), (98304, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 65536), (8192, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 69632), (12288, execute=False,ok=True,size=1024,size1=False,size2=True,subtable=False,userspace=False,write=False, 73728)]
        """
        entries = self.readTable(tablepos, tablesize)
        self._table = self.getEntries(entries)
        return self._table

    def diffTime(self, a, b):
        d = a - b
        print (d.seconds*1000*1000 + d.microseconds)

    def readTable(self, tablepos, tablesize, pos=None):
        """ Reads table from memory

        >>> from primitives import Mem
        >>> m = Mem(1024*100)
        >>> u = MMU(m)
        >>> # Subtable, starts at phys 4k
        >>> m.setData(10, 0x00001111, 4)
        >>> # Page, starts at 32k, size 64k
        >>> m.setData(14, 0x00008110, 4)
        >>> for i in xrange(1023):
        ...   m.setData(0x1000 + i, 0)
        >>> tmp = u.readTable(10, 3)
        >>> tmp[0][0]
        4096
        >>> tmp[1][0]
        32768
        >>> tmp[0][1]
        execute=False,ok=True,size=65536,size1=True,size2=False,subtable=True,userspace=False,write=False
        >>> tmp[1][1]
        execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False
        >>> tmp[0]
        (4096, execute=False,ok=True,size=65536,size1=True,size2=False,subtable=True,userspace=False,write=False, 0)
        >>> tmp[1]
        (32768, execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False, 67108864)
        """
        import datetime
        datas = []
        if pos is None:
            pos = 0

        virtpos = tablepos
        cnt = 0

        # Optimized reading in blocks instead of one byte at time
        block = self._mem.getBlock(tablepos, tablesize * 4)
        oldtmp = 0
        items = 0
        preindex = 0
        for (bpos, data) in block:
            if data is None:
                continue

            if preindex > 0:
                # Do we have old data from previous block?
                if preindex == 1:
                    oldtmp += (data[0] << 24)
                if preindex == 2:
                    oldtmp += (data[0] << 16) + (data[1] << 24)
                if preindex == 3:
                    oldtmp += (data[0] << 8) + (data[1] << 16) + (data[2] << 24)

                (ok, pos, res) = self.readEntry(oldtmp, pos)
                if ok:
                    datas.append(res)
                tablepos = preindex

            datalen = len(data)
            l = int(datalen / 4 - 1)
            index = tablepos % 0x1000
            for item in xrange(l):
                tmp = data[index] + (data[index+1] << 8) + (data[index+2] << 16) + (data[index+3] << 24)
                (ok, pos, res) = self.readEntry(tmp, pos)
                if ok:
                    datas.append(res)
                index += 4
                items += 4
                if index > datalen - 4:
                    miss = datalen - index
                    preindex = 0

                    # Check if we didn't read all the data...
                    if miss > 0:
                        oldtmp = data[index]
                        if miss > 1:
                            oldtmp += (data[index+1] << 8)
                        if miss > 2:
                            oldtmp += (data[index+2] << 16)
                        preindex = 4 - miss
                    break
                if items > (tablesize + tablepos):
                    break
        return datas

        """
        for index in xrange(tablesize):
            tmp = self._mem.getData(virtpos, self._wordsize)
            virtpos += self._wordsize
            if tmp > 0:
                print tmp
                cnt += 1
                (ok, pos, res) = self.readEntry(tmp, pos)
                if ok:
                    datas.append(res)

        return datas
        """

    def readEntry(self, data, pos=0):
        """ Read entry from one page table item data

        >>> m = Mem()
        >>> u = MMU(m)
        >>> u.readEntry(0x00000000)
        (False, 0, (0, execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 0))
        >>> u.readEntry(0x00001000)
        (True, 4096, (4096, execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 0))
        >>> u.readEntry(0x00001111)
        (True, 67108864, (4096, execute=False,ok=True,size=65536,size1=True,size2=False,subtable=True,userspace=False,write=False, 0))
        >>> u.readEntry(0x00001022)
        (True, 1048576, (4096, execute=True,ok=False,size=1024,size1=False,size2=True,subtable=False,userspace=False,write=False, 0))
        >>> u.readEntry(0x00002FFF)
        (True, 68719476736, (8192, execute=True,ok=True,size=67108864,size1=True,size2=True,subtable=True,userspace=True,write=True, 0))
        >>> u.readEntry(0xFFFFFFFF)
        (True, 68719476736, (4294963200, execute=True,ok=True,size=67108864,size1=True,size2=True,subtable=True,userspace=True,write=True, 0))
        >>> u.readEntry(0)
        (False, 0, (0, execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 0))
        """
        if data > 0:
            flags = MMU.Flags(data & 0xFFF)
            vaddr = data & 0xFFFFF000
            ok = True
        else:
            vaddr = 0
            flags = MMU.Flags(data & 0xFFF)
            ok = False
            return (ok, pos, (vaddr, flags, pos))

        return (ok, pos + flags['size'] * 1024, (vaddr, flags, pos))

    def getRange(self, item):
        addr = item[0]
        flags = item[1]
        pos = item[2]
        endaddr = addr + (flags['size'] * 1024)
        return (addr, endaddr, pos)

    def virtToPhys(self, pos):
        """ Converts virtual memory location to physical

        >>> from primitives import Mem
        >>> m = Mem(1024*1024*10)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> # Page, virtual start at 96k, size 4k (0x1000)
        >>> m.setData(14, 0x00018100, 4)
        >>> # Page, virtual start at 32k, size 64k (0x10000)
        >>> m.setData(18, 0x00008110, 4)
        >>> # Subtable, starts at phys 4k, size 4M
        >>> m.setData(22, 0x00001101, 4)
        >>> # Page at virtual at 8k, size 4k (0x1000)
        >>> m.setData(0x1000, 0x00002100, 4)
        >>> # Page at virtual at 1126k, size 1M
        >>> m.setData(0x1004, 0x00113120, 4)
        >>> tmp = u.initialize(10, 5)
        >>> u.virtToPhys(0x8000) == (0x2000)
        True
        >>> u.virtToPhys(0x8000)
        8192
        >>> u.virtToPhys(0x8001)
        8193
        >>> u.virtToPhys(0x2000)
        73728
        >>> u.virtToPhys(0x2000) == (0x2000 + 0x10000)
        True
        >>> u.virtToPhys(0x2010) == (0x2000 + 0x10000 + 0x10)
        True
        >>> u.virtToPhys(0x2FFF) == (0x2000 + 0x10000 + 0xFFF)
        True
        >>> u.virtToPhys(0x18000) == 0x1000
        True
        >>> u.virtToPhys(0x19000) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00019000
        >>> u.virtToPhys(0x19001) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00019001
        >>> u.virtToPhys(0x1A000) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 0001A000
        >>> u.virtToPhys(0) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00000000
        """
        for item in self._table:
            (a, b, c) = self.getRange(item)
            if a <= pos and pos < b:
                index = (pos - a)
                phys = c + index
                return phys
        raise IndexError('No page mapped at virtual: %.8X' % (pos))

    def getPageFlags(self, pos):
        """ Get flags at position

        >>> from primitives import Mem
        >>> m = Mem(1024*1024*10)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> # Subtable, starts at phys 4k (0x1000)
        >>> m.setData(14, 0x00001101, 4)
        >>> # Page, virtual start at 32k, size 64k (0x10000)
        >>> m.setData(18, 0x00008110, 4)
        >>> # Page, virtual start at 96, size 4k (0x1000)
        >>> m.setData(22, 0x00018100, 4)
        >>> # Page at virtual 8k, size 4k (0x1000)
        >>> m.setData(0x1000, 0x00002100, 4)
        >>> # Page at virtual 1126k, size 1M
        >>> m.setData(0x1004, 0x00113120, 4)
        >>> tmp = u.initialize(10, 4)
        >>> u.enable()
        >>> u.getPageFlags(0x8000)
        execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False
        >>> u.getPageFlags(0x8001)
        execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False
        >>> u.getPageFlags(0x18000)
        execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False
        >>> u.getPageFlags(0x18010)
        execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False
        >>> u.getPageFlags(0x19000)
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00019000
        >>> u.getPageFlags(0x19001) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00019001
        >>> u.getPageFlags(0x1A000) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 0001A000
        >>> u.getPageFlags(0x18fff)
        execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False
        >>> u.getPageFlags(0) #doctest: +ELLIPSIS
        Traceback (most recent call last):
        ...
        IndexError: No page mapped at virtual: 00000000
        """
        if not self._enabled:
            return None

        for item in self._table:
            (a, b, c) = self.getRange(item)
            if a <= pos and pos < b:
                return item[1]
        raise IndexError('No page mapped at virtual: %.8X' % (pos))

    def setData(self, pos, data, size=4):
        """ Set data, if MMU enabled, solve physical locations first

        >>> from primitives import Mem
        >>> m = Mem(1024*1024*5)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> # Page, virtual start at 96, size 4k (0x1000)
        >>> m.setData(14, 0x00018100, 4)
        >>> # Page, virtual start at 32k, size 64k (0x10000)
        >>> m.setData(18, 0x00008110, 4)
        >>> # Subtable, starts at phys 4k, size 4M (0x1000)
        >>> m.setData(22, 0x00001101, 4)
        >>> # Page at virtual 8k, size 4k (0x1000)
        >>> m.setData(0x1000, 0x00002100, 4)
        >>> # Page at virtual 1126k, size 1M
        >>> m.setData(0x1004, 0x00113120, 4)
        >>> tmp = u.initialize(10, 4)
        >>> # Paging is disabled, set data to phys 0x8000
        >>> u.setData(0x8000, 56, 1)
        >>> # Enable paging
        >>> u.enable()
        >>> # Paging is enabled so set data to virt 0x8000, which is 0x2000 in phys
        >>> u.setData(0x8000, 42, 1)
        >>> # Get memory contents at 0x8000 phys
        >>> m.getData(0x8000, 1)
        56
        >>> # Get memory contents at 0x2000 phys
        >>> m.getData(0x2000, 1)
        42
        """
        if self._enabled:
            self._mem.setData(self.virtToPhys(pos), data, size)
        else:
            self._mem.setData(pos, data, size)

    def getData(self, pos, size=1):
        """ Get data, if MMU enabled, solve physical location first

        >>> from primitives import Mem
        >>> m = Mem(1024*1024*10)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> # Subtable, starts at phys 4k (0x1000)
        >>> m.setData(14, 0x00001101, 4)
        >>> # Page, virtual start at 32k, size 64k (0x10000)
        >>> m.setData(18, 0x00008110, 4)
        >>> # Page, virtual start at 96k, size 4k (0x1000)
        >>> m.setData(22, 0x00018100, 4)
        >>> # Page at virtual 8k, size 4k (0x1000)
        >>> m.setData(0x1000, 0x00002100, 4)
        >>> # Page at virtual 1126k, size 1M
        >>> m.setData(0x1004, 0x00113120, 4)
        >>> u.initialize(10, 4)
        [(24576, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 0), (8192, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 4096), (1126400, execute=False,ok=True,size=1024,size1=False,size2=True,subtable=False,userspace=False,write=False, 8192), (32768, execute=False,ok=True,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False, 4198400), (98304, execute=False,ok=True,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False, 4263936)]
        >>> # Paging is disabled, set data to phys 0x8000
        >>> u.setData(0x8000, 56, 1)
        >>> # Paging is disabled, set data to phys 0x100
        >>> u.setData(0x100, 12345, 4)
        >>> # Enable paging
        >>> u.enable()
        >>> # Paging is enabled so set data to virt 0x8000, which is 0x2000 in phys
        >>> u.setData(0x8000, 42, 1)
        >>> # Get memory contents at 0x8000 virt
        >>> u.getData(0x8000, 1)
        42
        >>> # Get memory contents at 0x100 phys, 0x6000+0x100 virt
        >>> u.getData(0x6000 + 0x100, 4)
        12345
        """
        if self._enabled:
            return self._mem.getData(self.virtToPhys(pos), size)
        else:
            return self._mem.getData(pos, size)

    def setRaw(self, pos, data):
        """ Set one byte, if MMU enabled, solve physical location first

        >>> from primitives import Mem
        >>> m = Mem(1024*100)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> tmp = u.initialize(10, 1)
        >>> u.setRaw(0x100, 255)
        >>> u.enable()
        >>> u.setRaw(0x6001, 123)
        >>> m.getRaw(0x100)
        255
        >>> m.getRaw(0x1)
        123
        """
        if self._enabled:
            self._mem.setRaw(self.virtToPhys(pos), data)
        else:
            self._mem.setRaw(pos, data)

    def getRaw(self, pos):
        """ Get one byte, if MMU enabled, solve physical location first

        >>> from primitives import Mem
        >>> m = Mem(1024*100)
        >>> u = MMU(m)
        >>> # Page, virtual start at 24, size 4k (0x1000)
        >>> m.setData(10, 0x00006100, 4)
        >>> tmp = u.initialize(10, 1)
        >>> u.setRaw(0x100, 255)
        >>> u.enable()
        >>> u.setRaw(0x6001, 123)
        >>> m.getRaw(0x100)
        255
        >>> m.getRaw(0x1)
        123
        >>> u.getRaw(0x6001)
        123
        >>> u.getRaw(0x6000)
        0
        """
        if self._enabled:
            return self._mem.getRaw(self.virtToPhys(pos))
        else:
            return self._mem.getRaw(pos)
        
    class Flags:
        def __init__(self, flags=0, solved=None):
            """ Initialize flags
            """
            self._flags = flags
            if solved is None:
                self._data = self.solveFlags(flags)
            else:
                self._data = solved

        def solveFlags(self, flags):
            """ Solve flags from given number data

            >>> f = MMU.Flags()
            >>> r = f.solveFlags(0x1)
            >>> f
            execute=False,ok=False,size=4096,size1=False,size2=False,subtable=True,userspace=False,write=False
            >>> r = f.solveFlags(0x2)
            >>> f
            execute=True,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False
            >>> r = f.solveFlags(0x4)
            >>> f
            execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=True
            >>> r = f.solveFlags(0x8)
            >>> f
            execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=True,write=False
            >>> r = f.solveFlags(0x10)
            >>> f
            execute=False,ok=False,size=64,size1=True,size2=False,subtable=False,userspace=False,write=False
            >>> r = f.solveFlags(0x20)
            >>> f
            execute=False,ok=False,size=1024,size1=False,size2=True,subtable=False,userspace=False,write=False
            >>> r = f.solveFlags(0x30)
            >>> f
            execute=False,ok=False,size=65536,size1=True,size2=True,subtable=False,userspace=False,write=False
            >>> r = f.solveFlags(0x40)
            >>> f
            execute=False,ok=False,size=4,size1=False,size2=False,subtable=False,userspace=False,write=False
            >>> r = f.solveFlags(0xFF)
            >>> f
            execute=True,ok=False,size=67108864,size1=True,size2=True,subtable=True,userspace=True,write=True
            >>> r = f.solveFlags(0x1FF)
            >>> f
            execute=True,ok=True,size=67108864,size1=True,size2=True,subtable=True,userspace=True,write=True
            """
            data = {
                'subtable': False,
                'execute': False,
                'write': False,
                'userspace': False,
                'size': 0,
                'size1': False,
                'size2': False,
                'ok': False,
                }
                #'size3': False,
            if flags & 0x1 == 0x1:
                data['subtable'] = True
            if flags & 0x2 == 0x2:
                data['execute'] = True
            if flags & 0x4 == 0x4:
                data['write'] = True
            if flags & 0x8 == 0x8:
                data['userspace'] = True
            if flags & 0x10 == 0x10:
                data['size1'] = True
            if flags & 0x20 == 0x20:
                data['size2'] = True
            if flags & 0x100 == 0x100:
                data['ok'] = True

            # Determine page size in kilobytes
            if not data['size1'] and not data['size2']:
                data['size'] = 4
            elif data['size1'] and not data['size2']:
                data['size'] = 64
            elif not data['size1'] and data['size2']:
                data['size'] = 1024
            elif data['size1'] and data['size2']:
                data['size'] = 1024 * 64
            # For subtables multiply by 1024
            if data['subtable']:
                data['size'] *= 1024

            self._data = data
            return data

        def isSet(self, name):
            """ Checks whether element is set, or get value

            >>> f = MMU.Flags(0x1F)
            >>> f.isSet('size')
            65536
            >>> f.isSet('size1')
            True
            >>> f.isSet('size2')
            False
            >>> f.isSet('subtable')
            True
            """
            if not name in self._data:
                return False

            return self._data[name]
    
        def __getitem__(self, name):
            if not name in self._data:
                return None

            return self._data[name]

        def dump(self):
            """ Dumps the flag status
            """
            return self._data

        def __repr__(self):
            """ Get string representation of the flags
            """
            #return "%s" % self.dump()
            a = self._data.keys()
            res = ''
            for k in sorted(a):
                if res:
                    res += ','
                res += '%s=%s' % (k, self._data[k])
            return res

"""
MMU

Initial table


if __name__ == "__main__":
    import doctest
    doctest.run_docstring_examples(MMU.initialize, globals())
"""

class WebApp:
    def __init__(self):
        self.db = "sqlite:///memory.db"

    def display_user_input(self, user_input):
        return f"<div>{user_input}</div>"

    def update_user_profile(self, user_id, new_email):
        import sqlite3
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        query = f"UPDATE users SET email='{new_email}' WHERE id={user_id}"
        cursor.execute(query)
        conn.commit()
        conn.close()

    def change_password(self, user_id, new_password):
        import sqlite3
        conn = sqlite3.connect(self.db)
        cursor = conn.cursor()
        query = f"UPDATE users SET password='{new_password}' WHERE id={user_id}"
        cursor.execute(query)
        conn.commit()
        conn.close()

web_app = WebApp()
# Simulating user input
user_input = "<script>alert('XSS');</script>"
print(web_app.display_user_input(user_input))  # XSS Vulnerability

# Simulating SQL Injection
web_app.update_user_profile(1, "hacker@domain.com' OR '1'='1")  # SQL Injection Vulnerability

# Simulating CSRF
web_app.change_password(1, "new_password")  # CSRF Vulnerability (assuming no token validation)