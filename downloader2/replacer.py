# coding=utf-8

import os
import re

db = 'AZ_IRKOBL_BRATSK_301015'
# port = '2015'


def replaceServerPort(port):
    serverBat = 'StartServer.bat'

    serverPort = 'set SERVER_PORT={}\n'.format(port.strip())
    reServerPort = re.compile('\Aset SERVER_PORT=')

    with open(serverBat, 'r') as bat:
        data = bat.readlines()

    serverPortFound = False

    serverBatNewConfig = []

    for line in data:
        if re.match(reServerPort, line):
            serverBatNewConfig.append(serverPort)
            serverPortFound = True
            continue
        serverBatNewConfig.append(line)

    if not serverPortFound:
        serverBatNewConfig.append(serverPort)
    os.remove(serverBat)
    with open(serverBat, 'w') as newBat:
        for line in serverBatNewConfig:
            newBat.write(line)


def replaceAzkConfig(db):
    config = 'Azk2Server.properties'
    dburl = 'azk.db.url=jdbc:oracle:thin:@172.21.10.56:1521:support11\n'
    dbname = 'azk.db.user={}\n'.format(db.strip())
    dbpass = 'azk.db.password={}\n'.format(db.strip())
    dbtrace = 'azk.db.traceenabled=true\n'
    azklic = 'azk.license.name=bft.lic\n'

    reDbUrl = re.compile('\Aazk.db.url')
    reDbName = re.compile('\Aazk.db.user')
    reDbPass = re.compile('\Aazk.db.password')
    reDbTrace = re.compile('\Aazk.db.traceenabled')
    reAzkLic = re.compile('\Aazk.license.name')

    with open(config, 'r') as azkconfig:
        data = azkconfig.readlines()

    dbUrlFound = False
    dbNameFound = False
    dbPassFound = False
    dbTraceFound = False
    azkLicFound = False

    azkNewConfig = []
    for line in data:
        if re.match(reDbUrl, line):
            azkNewConfig.append(dburl)
            dbUrlFound = True
            continue
        if re.match(reDbName, line):
            azkNewConfig.append(dbname)
            dbNameFound = True
            continue
        if re.match(reDbPass, line):
            azkNewConfig.append(dbpass)
            dbPassFound = True
            continue
        if re.match(reAzkLic, line):
            azkNewConfig.append(azklic)
            azkLicFound = True
            continue
        if re.match(reDbTrace, line):
            azkNewConfig.append(dbtrace)
            dbTraceFound = True
            continue
        azkNewConfig.append(line)

    if not dbUrlFound:
        azkNewConfig.append(dburl)
    if not dbNameFound:
        azkNewConfig.append(dbname)
    if not dbPassFound:
        azkNewConfig.append(dbpass)
    if not dbTraceFound:
        azkNewConfig.append(dbtrace)
    if not azkLicFound:
        azkNewConfig.append(azklic)

    os.remove(config)
    with open(config, 'w') as newAzkConfig:
        for line in azkNewConfig:
            newAzkConfig.write(line)

