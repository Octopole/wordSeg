#encoding=utf-8
import os
import sys

s=open(sys.argv[1], "r", encoding='utf-8')
dic=open("dict.txt", "w+", encoding='utf-8')
re=open("REpatten.txt", "w+", encoding='utf-8')

c = s.read(1)
tmp = ""
while c:   
    wdtype = 0
    while c and c!=" " and c!="\n" and c!="\t" and c!="+" and c!="," and c!='"' and c!="，" and c!="、" and c!="(" and c!=")" and c!="\\" and c!="（"and c!="）" and c!="/":
        tmp = tmp + c
        if c=="*" or c=="φ":
            wdtype=1
        c = s.read(1)
    
    if wdtype == 0:
        if tmp != "" and tmp!=" " and tmp!="\n" and tmp!="\t":
            dic.write(tmp+" n\n")
            print("New word added: "+tmp+"\n")
            dic.flush()
    else:
        re.write(tmp+"\n")
        re.flush()
        print("New patten added: "+tmp+"\n")
    tmp=""
    c = s.read(1)

s.close()
dic.close()
re.close()



