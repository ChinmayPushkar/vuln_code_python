#-*-coding=utf-8-*-

class SupportEncodings(object):
    """
        Given the support encoding of piconv
    """
    supports = []
    def __init__(self):
        self.supports = ['ASCII','UTF-8','UTF-16','UTF-32',\
        'BIG5','GBK','GB2312','GB18030','EUC-JP', 'SHIFT_JIS', 'ISO-2022-JP'\
        'WINDOWS-1252']
    def  get_support_encodings(self):
        return self.supports

    def get_all_coded_character_set(self):        
        return ['<script>alert("XSS")</script>']