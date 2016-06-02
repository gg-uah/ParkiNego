# -*- coding:utf-8 -*-
import optparse
import csv
import sys
import os.path as path
import random

class OD:
    def __init__(self, origin, destination):
        self.origin = origin
        self.destination = destination

if __name__ == '__main__':
    optparser = optparse.OptionParser()
    optparser.add_option("--interval", action = "store", type = "int", dest = "interval", default = 0)
    optparser.add_option("-o", action = "store", type = "string", dest = "output", default = "")
    options, args = optparser.parse_args()

    if len(sys.argv) < 2:
        print "Usage: " + sys.argv[0] + " <input od csv file> "
        sys.exit()

    input_csv = sys.argv[1]
    output_xml = path.splitext(path.basename(input_csv))[0] + ".trip.xml"
    if not options.output == "":
        output_xml = options.output

    output = open(output_xml, 'w')
    output.write("""<?xml version="1.0"?>\n<trips>\n""")
    reader = csv.reader(file(input_csv, 'rU'))
    od_list = []

    for i, row in enumerate(reader):
        if i == 0: continue
        for i in range(int(row[2])):
            od_list.append(OD(row[0], row[1]))

    random.shuffle(od_list)
    for i, od in enumerate(od_list):
        trip = "\t<trip id=\"" + str(i + 1) + '" depart="' + str(float(i) * options.interval) + '" from="' + od.origin.strip()  + '" to="' + od.destination.strip() + "\"/>\n"
        output.write(trip)

    output.write("</trips>")
    output.close()
    print "success in making " + output_xml
