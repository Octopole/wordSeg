#--------------------------------------------------------------------------------------------------------#

#Input format: .txt file with OCRed info, words seperated with "space", line seperated with "enter".
#Output format: Json file with Docs and prelabeled data.
#dictionary format: Json file with lists named as [ Index, Name, Nameinorder, Specifications, DN, PN, T, Standard, Material, Flange, Time ] containing Stand-alone pattens.

#--------------------------------------------------------------------------------------------------------#

#encoding=utf-8


import jieba
from astropy.table import join as join
import os
import sys
import json
import re


#Word cutting
seperatorlist = ["mm", "MM", '"', ".", 'pcs', "(", ")", "+", "-", ":", "_", "/", "=", "x", "X"]
addtoleftlist = [")", '"', "mm", "MM", "pcs", 't']
connectorlist = ["+", "-", ":", "_", "/", "(", ".", "=", "x", "X"]
pairtracerlist = {"(": ")"}
#date matching
redate = [r'[0-9]+/[0-9]+/[0-9]+', r'[A-Za-z]+/[0-9]+[A-Za-z]*/[0-9]+', r'[0-9]+-[0-9]+-[0-9]+', r'[A-Za-z]+-[0-9]+[A-Za-z]*-[0-9]+']
#Nameinorder matching
NIOSOWlist = [r'Gasket', r'FC', r'DQ', r'EC', r'GD', r'GE', r'KD', r'DQ', r'NU', r'NF', r'NB']
#T matching
Tprereqlist = [r'T', r't', r'厚', r'厚度', r'THK', r'THICK']
Tconnectorlist = [r'', r':', r'=']
Tunitlist = [r'mm', r'MM', r't', r'T']
TSOWlist = [r"THICKNESS", r"THICK"]
""" r'椭圆形', r'八角垫', r'八角形', r'oval',  """
#PN matching
PNSOWlist = [r'PN[0-9]+', r"CL[0-9]+", r"[0-9]+LB", r"CLASS[0-9]+", r"Class[0-9]+"]
#DN matching
DNSOWlist = [r"DN[0-9]+", r"NPS[0-9]+"]
#Specifications matching
SPSOWlist = [r"[0-9]+\*[0-9]+(\*[0-9]+)?(\*[0-9]+)?(\*[0-9]+)?", r"[0-9]+x[0-9]+(x[0-9]+)?(x[0-9]+)?(x[0-9]+)?"]
#Name matching
NameSOWlist = []
#Standard matching
SDSOWlist = []
#Material matching
MASOWlist = []
#Flange matching
FlSOWlist = []

#typelist: Index, Name, #Nameinorder, Specifications, #DN, #PN, #T, Standard, Material, Flange, #Time, #Unlabled

def dullkiller(l):
    while 1:
        try:
            l.remove("")
        except ValueError:
            return l
        else:
            pass

def isJson(inp):
    try:
        json.loads(inp)
    except ValueError:
        return False
    return True

def strQ2B(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:
            inside_code = 32 
        elif (inside_code >= 65281 and inside_code <= 65374):
            inside_code -= 65248
        rstring += chr(inside_code)
    return rstring
    
def strB2Q(ustring):
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 32:
            inside_code = 12288
        elif inside_code >= 32 and inside_code <= 126:
            inside_code += 65248
        rstring += chr(inside_code)
    return rstring

def linetolist(line):
    line = strQ2B(line)
    retlist = []
    tmp = ""
    for i in line:
        if i != " " and i != "," and i!= "\n":
            tmp += i
        else:
            if tmp != "":
                retlist += [tmp]
                tmp = ""
    retlist += ["\n"]
    return retlist

def wdjoin(wd):
    #wd = linetolist(wd)
    #print(wd)
    
    """seperate symbols and units for words"""
    for j in seperatorlist:
        wdbk = []
        for i in wd:
            countj = i.count(j)
            if countj == 0:
                wdbk+=[i]
            else:
                outer = []
                rawlist = i.split(j, countj)
                for k in rawlist:
                    outer = outer + [k] + [j]
                outer.pop()
                wdbk+=outer
        wd = wdbk
    wd = dullkiller(wd)
    #print(wd)

    """add units as addon to its left word"""
    for i in addtoleftlist:
        checker = 1
        while checker:
            try:
                index = wd.index(i)
            except ValueError:
                checker=0
            else:
                if not index<1:
                    tmp = wd[:index-1] + [wd[index-1] + wd[index]] + wd[index+1:]
                elif index==0:
                    tmp = wd
                wd = tmp 
    wd = dullkiller(wd)
    #print(wd)

    """link connect words to its nerborhoods"""
    for i in connectorlist:
        checker = 1
        while checker:
            try:
                index = wd.index(i)
            except ValueError:
                checker=0
            else:
                if not index<1 and not index>len(wd)-1:
                    tmp = wd[:index-1] + [wd[index-1] + wd[index] + wd[index+1]] + wd[index+2:]
                elif index==0:
                    tmp = [wd[0] + wd[1]] + wd[2:]
                elif index==len(wd)-1:
                    tmp = wd[:index-1] + [wd[index-1] + wd[index]]
                wd = tmp 
    wd = dullkiller(wd)
    #print(wd)

    """checking not complete parentheses or others"""
    kvp = pairtracerlist.items()
    for i in kvp:
        idxmkr = []
        insmkr = []
        exclamer = 0
        for j in wd:
            for k in j:
                if k == i[0]:
                    exclamer += 1
                elif k == i[1]:
                    exclamer -= 1
            if exclamer == 0:
                if len(insmkr)!=0:
                    insmkr += [wd.index(j)]
                    idxmkr += [insmkr]
                    insmkr = []
            else:
                insmkr += [wd.index(j)]
        if len(insmkr) != 0:
            idxmkr += insmkr
        #print(idxmkr)
        if len(idxmkr) != 0:
            for j in idxmkr:
                tmp = wd[:j[0]]
                addwd = ""
                for k in j:
                    #add seperator here if needed
                    addwd += wd[k]
                tmp += [addwd] + wd[j[0]+len(j):]
                wd = tmp
    wd = dullkiller(wd)
    #print(wd)

    return wd

#-----------string toolbox-------------

def havech(check_str):
    #return bool
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def allch(check_str):
    for chart in check_str:
        if chart < u'\u4e00' or chart > u'\u9fff':
            return False

    return True

def isdate(inp):
    out = False
    for i in redate:
        if re.search(i, inp):
            out = True
    return out

def isT(inp):
    out = False
    #pattern 1
    for i in Tprereqlist:
        for j in Tconnectorlist:
            for k in Tunitlist:
                if re.search(i+j+r'[0-9]+(.[0-9]+)?"?('+k+')?', inp):
                    out = True
    
    #pattern 2
    for i in Tprereqlist+Tunitlist:
        if re.search(r'^[0-9]+(.[0-9]+)?"?'+i, inp):
            out = True
    
    #pattern 3
    for i in TSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isPN(inp):
    out = False
    #pattern 1
    for i in PNSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isDN(inp):
    out=False
    for i in DNSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isNIO(inp):
    out = False
    for i in NIOSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isSP(inp):
    out = False
    for i in SPSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isName(inp):
    out = False
    for i in NameSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isSD(inp):
    out = False
    for i in SDSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isMA(inp):
    out = False
    for i in MASOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out

def isFl(inp):
    out = False
    for i in FlSOWlist:
        if re.search(i, inp, re.I):
            out = True
    return out


#--------------------------------------

def listtodic(rawlist, lc):
    out = {}
    counter = 0
    lc += 1
    fw = '%d' %lc
    if fw == rawlist[0]:
        out[rawlist[0]] = "Index"

    for i in rawlist:
        if counter != 0:
            preword = rawlist[counter-1]
        else:
            preword = ""
        if not i in out:
            if counter != len(rawlist)-1:
                nxtword = rawlist[counter+1]
            else:
                nxtword = ""
            if isdate(i):
                out[i] = 'Time'
            elif isT(i):
                out[i] = 'T'
            elif isPN(i):
                out[i] = 'PN'
            elif isDN(i):
                out[i] = 'DN'
            elif isNIO(i):
                out[i] = 'Nameinorder'
            elif isSP(i):
                out[i] = 'Specifications'
            elif isName(i):
                out[i] = 'Name'
            elif isSD(i):
                out[i] = 'Standard'
            elif isMA(i):
                out[i] = 'Material'
            elif isFl(i):
                out[i] = 'Flange'
            else:
                out[i] = "Unlabled"
        
        counter += 1
    return out

#jieba.load_userdict(sys.argv[2])
if len(sys.argv)<2 or len(sys.argv)>=4:
    print('Usage: python Segmentation.py sourcefile dictionary(alternative)')
    exit(0)
if len(sys.argv) == 3:
    try:
        f3=open(sys.argv[2], encoding='utf-8')
    except FileNotFoundError:
        print(sys.argv[2],"can't be opened, something wrong!")
    else:
        addinfo = f3.read()
        f3.close()
        if isJson(addinfo):
            print("Building dictionary using:", sys.argv[2])
            adddic = json.loads(addinfo)
            if 'T' in adddic:
                TSOWlist += adddic['T']
            if 'Nameinorder' in adddic:
                NIOSOWlist += adddic['Nameinorder']
            if 'PN' in adddic:
                PNSOWlist += adddic['PN']
            if 'DN' in adddic:
                DNSOWlist += adddic['DN']
            if 'Specifications' in adddic:
                SPSOWlist += adddic['Specifications']
            if 'Name' in adddic:
                NameSOWlist += adddic['Name']
            if 'Standard' in adddic:
                SDSOWlist += adddic['Standard']
            if 'Material' in adddic:
                MASOWlist += adddic['Material']
            if 'Flange' in adddic:
                FlSOWlist += adddic['Flange']
            print("Finish building dictionary.")
        else:
            print("Fail adding info to dictionay, format wrong!")

try:
    f=open(sys.argv[1], encoding='utf-8')
except FileNotFoundError:
    print(sys.argv[1],"can't be opened, something wrong!")
else:
    pass

line= f.readline()
f2=open("output.json", "w+", encoding='utf-8')
f2.write('{"docs":"This is currently blank.",\n"datas":\n[')
linecount = 0
while line:
    line = strQ2B(line)
    seg_list = linetolist(line)
    line=f.readline()
    #seg_list = jieba.cut(line,cut_all=False)
    #seg_list.encode("utf-8")
    #seg_list.decode("utf-8")
    seg_list = wdjoin(seg_list)
    dic = listtodic(seg_list, linecount)
    #line = " ".join(line)
    if len(dic) != 1:
        linecount += 1
        put = json.dumps(dic, indent=4, ensure_ascii=False)
        #, skipkeys=False, ensure_ascii=True, check_circular=True, allow_nan=True, cls=None, indent=None, separators=None, encoding="utf-8", default=None, sort_keys=False
        f2.write(put) 
        if line:
            f2.write(",\n")
f2.write("]\n}")
f2.close()
f.close()
print(linecount,"line(s) of record transfered.")
print("Segmentation Finish.")
