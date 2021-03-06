#!/usr/bin/python2
# *-* coding: utf-8 *-*

### Utility for Uhf rfid reading ###

from binascii import hexlify, unhexlify
import collections
import random



def severalTimesPollingCommandGen(pollingtime):
    """
    Generate Several times polling command based on given decimal number.
    :param pollingtime:
    :return pollingCommandFinal:
    """
    pollingtimeHex = hex(pollingtime)

    pollingCommand = "0027000322" + pollingtimeHex[2:].zfill(4)

    checksum = checksumCalculator(pollingCommand)

    pollingCommandFinal = "BB"+pollingCommand+checksum+"7E"

    return (pollingCommandFinal)



def dataHexCleaner(dataHex):
    """
    Clean the dataHex string by removing starting and ending bytes
    :param dataHex:
    :return cleanDataArray:
    """
    dataArray = dataHex.split("7EBB")

    cleanDataArray = []

    for x in dataArray:
        if x.startswith("BB"):
            if(x.endswith("7E")):
                y = x[2:-2]
                cleanDataArray.append(y)
            else:
                y = x[2:]
                cleanDataArray.append(y)

        elif x.endswith("7E"):
            z = x[:-2]
            cleanDataArray.append(z)

        else:
            cleanDataArray.append(x)

    return (cleanDataArray)



def readVerifier(dataHex):
    """
    Verifier for single and Multi Polling Command Response Frames.
    Returns dictionary containing Epc and Rssi data from the given hex data.
    :param dataHex:
    :return dataDict:
    """
    cleanDataArray = dataHexCleaner(dataHex)

    dataDict = collections.OrderedDict()

    for x in cleanDataArray:
        Type = x[0:2]

        Command = x[2:4]

        if len(x) == 44:
            if Type == '02' and Command == '22':
                EPC = x[14:38]
                RSSI = x[8:10]
                returnDict = {}
                returnDict["EPC"] = EPC
                returnDict["RSSI"] = RSSI
                dataDict[EPC] = returnDict

    return (dataDict)



def readEpcVerifier(dataHex):
    """
    Verifier for read EPC Command Response Frames.
    :param dataHex:
    :return dataDict:
    """
    cleanDataArray = dataHexCleaner(dataHex)
    # print (cleanDataArray)
    dataDict = collections.OrderedDict()
    # print (cleanDataArray)

    for x in cleanDataArray:
        Type = x[0:2]

        Command = x[2:4]

        if len(x) == 72:
            if Type == '01' and Command == '39':
                EPC = x[38:70]
                dataDict[EPC] = 1

    return (dataDict)



def randomHexGen():
    """
    Generates a random Hex Number of 8 digit length
    :return randomHex:
    """
    randomHex = ""

    for i in range(0,8):
        randomHex = randomHex + str(random.choice("0123456789ABCDEF"))

    return (randomHex)



def setPowerCommandGen(power):
    """
    Generate set power command based on given decimal number.
    :param power:
    :return setCommandFinal:
    """
    powerHex = hex(power)
    setCommand = "00B60002" + powerHex[2:].zfill(4)

    checksum = checksumCalculator(setCommand)

    setCommandFinal = "BB"+setCommand+checksum+"7E"

    return (setCommandFinal)



def checksumCalculator(hexStr):
    """
    Calculate checksum of a given hex string.
    :param hexStr:
    :return checksumHex:
    """
    byteStr = hex_to_bytes(hexStr)

    checksum = 0
    for ch in byteStr:
        checksum += ord(ch)

    checksumHex = hex(checksum)
    return (checksumHex[-2:].upper())



def bytes_to_hex(byteStr):
    """
    Convert a byte string to it's hex string representation.
    :return hexString:
    """
    return ''.join( [ "%02X" % ord( x ) for x in byteStr ] ).strip()



def hex_to_bytes(hexStr):
    """
    Convert a hex string values into a byte string. The Hex Byte values may
    or may not be space separated.
    :return byteString:
    """
    bytes = []
    hexStr = ''.join( hexStr.split(" ") )
    for i in range(0, len(hexStr), 2):
        bytes.append( chr( int (hexStr[i:i+2], 16 ) ) )
    return ''.join( bytes )

