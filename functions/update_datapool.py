# -*- coding: utf-8 -*-
import json
import os
from glob import glob
from decimal import *
import re
from babel.numbers import format_currency
import operator


NEED_COLUMNS=[
    'Beleg',
    'BelegURL',
    'Datum',
    'Kategorie',
    'Adressat',
    'Betrag'
]

COLUMN_ALIGNMENT=[
    ' ------ ',
    ' ------ ',
    ' ------ ',
    ' ------ ',
    ' ------ ',
    ' ------:',
    ' ------:'
]

COLUMN_DECIMALS=[
    [False,False],
    [False,False],
    [False,False],
    [False,False],
    [False,False],
    [True,True],
    [True,False]
]

FD_JAHR=''
SUMMARY=[]
WATERFALL={}

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def fcurrency(betrag,plus=False):
    return format_currency(betrag, 'EUR', format=('+' if plus else '')+'#,##0.##;-#,##0.##', locale='de')

def insertSummary(fd_jahr):
    global SUMMARY
    global WATERFALL

    print(fd_jahr)
    if( fd_jahr != '' ):

        ## write summary to year
        tmp='# '+fd_jahr[-4:]+'\n'
        tmp+='## Summary\n\n'

        tmp+='<svg class="chart"></svg>\n\n'

        ### haben/soll
        tmp+='| Konto | Startbetrag | Haben | Soll | Endbetrag | Differenz |\n'
        tmp+='| ------ | ------:| ------:| ------:| ------:| ------:|\n'

        summe_startbetrag=0
        summe_haben=0
        summe_soll=0
        summe_saldo=0
        summe_differenz=0
        for summary in SUMMARY:
            konto=summary[0]
            startbetrag=summary[1]
            haben=summary[2]
            soll=summary[3]
            saldo=summary[4]
            differenz=saldo-startbetrag
            summe_startbetrag+=startbetrag
            summe_haben+=haben
            summe_soll+=soll
            summe_saldo+=saldo
            summe_differenz+=differenz
            tmp+='| ['+konto+'](#'+(konto.replace('.','')).lower()+') | '+ fcurrency(startbetrag) + ' | '+fcurrency(haben)+' | '+fcurrency(soll)+' | '+fcurrency(saldo)+' | '+fcurrency(differenz)+' |\n'

        ### add summation
        tmp+='| **TOTAL** | **'+fcurrency(summe_startbetrag)+ '** | **'+fcurrency(summe_haben)+'** | **'+fcurrency(summe_soll)+'** | **'+fcurrency(summe_saldo)+'** | **'+fcurrency(summe_differenz)+'** |\n'
        tmp+='\n<hr>\n\n'


        file=open(fd_jahr+'/summary.md','r')
        t=file.read()
        file.close()


        file=open(fd_jahr+'/summary.md','w+')
        file.write( tmp + t + '\n<script> createWaterfall(); </script>' )
        file.close()

        WATERFALL_sorted = sorted(WATERFALL.items(), key=operator.itemgetter(1), reverse=True)
        wi='name,value\n'
        wf=''
        for v in WATERFALL_sorted:
            if(v[0] == 'INIT'):
                wi+='START,'+('{:10.2f}'.format(v[1]))+'\n'
            else:
                wf+=v[0]+','+('{:10.2f}'.format(v[1]))+'\n'

        file=open(fd_jahr+'/waterfall.csv','w+')
        file.write( wi + wf )
        file.close()


def getFD(ffd):
    global FD_JAHR
    global SUMMARY
    global WATERFALL
    FD=glob(ffd+'*')
    FD.sort()
    for fd in FD:
        if(os.path.isdir(fd)):
            if(fd[0:14] == '../Finanzen/20' and len(fd) == 16 ):
                insertSummary(FD_JAHR)
                FD_JAHR=fd

                file=open(FD_JAHR+'/summary.md','w+')
                file.write('')
                file.close()

                SUMMARY=[]
                WATERFALL={}
            getFD(fd+'/')
        else:
            if(fd[-4:] == '.csv'):
                if( os.path.isfile(fd[:-4]+'.md') ):
                    ### file already exists skip
                    print(fd + ' - already converted -> skip')
                elif( fd[-13:] == 'waterfall.csv' ):
                    ### ignore waterfall.csv
                    fd=fd
                else:
                    print(fd + ' convert..')
                    updateFile(fd)
                    print(fd + ' converted!')

def detectColumns(headline):
    COLUMNS=[]
    H=headline.split(',')
    for i,v in enumerate(NEED_COLUMNS):
        try:
            COLUMNS.append(H.index(v))
        except:
            return False
    return COLUMNS


def updateFile(fn):
    global FD_JAHR
    global SUMMARY

    file=open(fn,'r')
    t=file.read()
    file.close()
    t=t.replace('\\,','&#44;')
    R=t.split('\n')

    ### check headline
    COLUMNS=(detectColumns(R[0]))
    if(COLUMNS == False):
        COLUMNS=(detectColumns(R[1]))
        if(COLUMNS == False):
            print('Not all necessary columns found at '+bcolors.FAIL+fn+bcolors.ENDC+'\n\ncheck it:\n')
            print(NEED_COLUMNS)
            print('\nYour columns on headline :\n')
            print(R[0].split(','))
            print('\n\n\n')
            return
        else:
            start_i=2
    else:
        start_i=1

    ROWS=[]
    saldo=0
    haben=0
    soll=0
    startbetrag=0

    for v in R[start_i:]:
        fl=False
        r=''
        for w in v:
            if(w == '"'):
                fl=not fl
            else:
                r+= '.' if (fl and w==',') else w
        row=r.split(',')

        if(len(row)>=max(COLUMNS)):
            ROW=[]
            for i,c in enumerate(COLUMNS):

                if(NEED_COLUMNS[i]=='Kategorie'):

                    kategorie=row[c]
                    if( not kategorie in WATERFALL ):
                        WATERFALL[kategorie]=0

                    if( row[c] == 'SPENDE' or row[c] == 'VISA' ):
                        istSpende=True
                    else:
                        istSpende=False

                if(NEED_COLUMNS[i]=='Adressat'):
                    if(istSpende == True):
                        row[c]='*Datenschutz*'
                ROW.append(row[c])
            if(ROW[NEED_COLUMNS.index('Betrag')]!=''):
                betrag=float(ROW[NEED_COLUMNS.index('Betrag')])
                WATERFALL[kategorie]+=betrag
                saldo+=float(betrag)
                if(betrag>0):
                    haben+=betrag
                    if(ROW[NEED_COLUMNS.index('Kategorie')] == 'INIT' ):
                        ### Übertragung
                        startbetrag=betrag
                else:
                    soll-=betrag
                ROW.append('{:10.2f}'.format(saldo))
                ROWS.append(ROW)

    NEED_COLUMNS.append('Saldo')
    tmp=''
    tmp+=','.join(NEED_COLUMNS)
    for row in ROWS:
        tmp+='\n'+','.join(row)

    file=open(fn,'w+')
    file.write(tmp)
    file.close()

    j=( json.dumps( [NEED_COLUMNS] + ROWS ) )
    file=open(fn[:-4]+'.json','w+')
    file.write(j)
    file.close()

    ### head markdown page headlines ( year / account )
    F=fn.split('/')
    for f in F:
        if(f[-4:] == '.csv'):
            konto=f[:-4]
        if(f[0:2] == '20' and len(f) == 4):
            jahr=f

    ### add account title
    tmp='\n### '+konto
    tmp+='\n\n[MD]('+konto+'.md) '
    tmp+='/ [CSV]('+konto+'.csv) '
    tmp+='/ [JSON]('+konto+'.json) '
    tmp+='\n\n\n'

    ### haben/soll
    differenz=saldo-startbetrag
    tmp+='| Startbetrag | Haben | Soll | Endbetrag | Differenz |\n'
    tmp+='| ------:| ------:| ------:| ------:| ------:|\n'
    tmp+='| '+fcurrency(startbetrag)+' | '+fcurrency(haben)+' | '+fcurrency(soll)+' | '+fcurrency(saldo)+' | '+fcurrency(differenz)+' |\n\n\n'
    SUMMARY.append([konto,startbetrag,haben,soll,saldo])

    ### markdown table headline
    for v in NEED_COLUMNS:
        if(v!='BelegURL'):
            tmp+='| '+v+' '
    tmp+='|\n'

    ### markdown table alignment line
    for i, v in enumerate(NEED_COLUMNS):
        if(v!='BelegURL'):
            tmp+='|'+COLUMN_ALIGNMENT[i]
    tmp+='|\n'

    ### markdown table data rows
    for i,row in enumerate(ROWS):
        for j,col in enumerate(row):
            if(NEED_COLUMNS[j]=='Beleg' and row[NEED_COLUMNS.index('BelegURL')][0:4] == 'http'):
                tmp+='| ['+col+']('+row[NEED_COLUMNS.index('BelegURL')]+') '
            elif(NEED_COLUMNS[j]!='BelegURL'):
                if(COLUMN_DECIMALS[j][0]):
                    if(float(col)<0 and COLUMN_DECIMALS[j][1] ):
                        fc='<font color="red">'
                    elif(float(col)>0 and COLUMN_DECIMALS[j][1] ):
                        fc='<font color="green">'
                    else:
                        fc=''
                    col=fc+fcurrency(col,COLUMN_DECIMALS[j][1])+('</font>' if fc != '' else '' )
                tmp+='| '+col+' '
        tmp+='|\n'

    tmp+='\n\n'

    file=open(FD_JAHR+'/summary.md','a+')
    file.write(tmp + '\n<hr>\n' )
    file.close()

    tmp='# '+jahr+'\n'+tmp

    file=open(fn[:-4]+'.md','w+')
    file.write(tmp)
    file.close()

    NEED_COLUMNS.pop()


getFD('../Finanzen/')
insertSummary(FD_JAHR)
