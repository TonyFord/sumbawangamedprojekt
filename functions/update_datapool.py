# -*- coding: utf-8 -*-
import json
import os
from glob import glob
from decimal import *
import re

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
    False,
    False,
    False,
    False,
    False,
    True,
    True
]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def getFD(ffd):
    FD=glob(ffd+'*')
    for fd in FD:
        if(os.path.isdir(fd)):
            getFD(fd+'/')
        else:
            if(fd[-4:] == '.csv'):
                if( os.path.isfile(fd[:-4]+'.md') ):
                    ### file already exists skip
                    print(fd + ' - already converted -> skip')
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

    file=open(fn,'r')
    t=file.read()
    file.close()
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
                    if( row[c] == 'SPENDE' ):
                        istSpende=True
                    else:
                        istSpende=False

                if(NEED_COLUMNS[i]=='Adressat'):
                    if(istSpende == True):
                        row[c]='*Datenschutz*'
                ROW.append(row[c])
            if(ROW[NEED_COLUMNS.index('Betrag')]!=''):
                saldo+=float(ROW[NEED_COLUMNS.index('Betrag')])
                ROW.append(( '{:10.2f}'.format(saldo) ).strip())
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

    tmp='## '+jahr
    tmp+='\n#### '+konto
    tmp+='\n\n\n'

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
                if(COLUMN_DECIMALS[j]):
                    col='{:10.2f}'.format(float(col))
                tmp+='| '+col+' '
        tmp+='|\n'

    file=open(fn[:-4]+'.md','w+')
    file.write(tmp)
    file.close()

getFD('../Finanzen/')

# print('ABCD'[0:3])
