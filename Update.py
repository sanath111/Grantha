#!/usr/bin/python2.7
# *-* coding: utf-8 *-*

import MySQLdb
import sys

db = MySQLdb.connect("localhost", "test", "test123", "INVENTORY")
db.autocommit(1)

loc = str(raw_input("location: "))
iid = str(raw_input("item_id: "))


sql = """ UPDATE ITEMS SET location = '%s' WHERE item_id = '%s' """ %(loc, iid)

try:
    cursor = db.cursor()
    cursor.execute(sql)
    cursor.close()
    print("Item location changed to "+ loc)
except:
    print "Error: unable to fetch data : "+ str(sys.exc_info())

db.close()

