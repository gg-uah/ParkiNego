#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, string, sys, StringIO
from sumolib import net
import networkx as nx

from xml.sax import saxutils, make_parser, handler

class XMLTripReader(handler.ContentHandler):
    def __init__(self, out_route_file, network, real_net):
        print out_route_file
        self.out_route_file = open(out_route_file, 'w')
        self.network = network
        self.real_net = real_net
        self.out_route_file.write("""
<?xml version="1.0" encoding="UTF-8"?>

<!-- generated on Fri Oct 25 15:22:08 2013 by SUMO duarouter Version 0.17.1
<?xml version="1.0" encoding="UTF-8"?>

<configuration xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/duarouterConfiguration.xsd">

    <input>
        <net-file value="../network/grid9x9.net.xml"/>
        <trip-files value="./grid9x9.trip.xml"/>
    </input>

    <output>
        <output-file value="grid9x9.rou.xml"/>
    </output>

</configuration>
-->

<routes xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="http://sumo.sf.net/xsd/routes_file.xsd">
""")

    def endDocument(self):
        self.out_route_file.write('</routes>')
        self.out_route_file.close()

    def dist(self, a, b):
        s = sumo_net.getNode(a).getCoord()
        t = sumo_net.getNode(b).getCoord()
        return ((s[0]-t[0])**2+(s[1]-t[1])**2)**0.5

    def distByEdge(self, a, b):
        s = sumo_net.getEdge(a).getToNode().getCoord()
        t = sumo_net.getEdge(b).getToNode().getCoord()
        return ((s[0]-t[0])**2+(s[1]-t[1])**2)**0.5

    def startElement(self, name, attrs):
        if attrs.getLength()!=0:
            vehicle_info = 't<vehicle id="'+attrs.getValue('id')+'" depart="'+attrs.getValue('depart')+'">n'
            self.out_route_file.write(vehicle_info)
            if self.real_net == True:
                route = nx.astar_path(
                        self.network,
                        attrs.getValue('from').encode('utf-8'),
                        attrs.getValue('to').encode('utf-8'),
                        self.distByEdge
                    )
            else:
                route = self.nodes2Route(
                    nx.astar_path(
                        self.network,
                        sumo_net.getEdge(attrs.getValue('from').encode('utf-8')).getFromNode().getID().encode('utf-8'),
                        sumo_net.getEdge(attrs.getValue('to').encode('utf-8')).getFromNode().getID().encode('utf-8'),
                        self.dist
                    )
                )
            self.out_route_file.write('tt<route edges="'+" ".join(map(str, route))+'"/>n')
            vehicle_info_end = 't</vehicle>n'
            self.out_route_file.write(vehicle_info_end)
    def nodes2Route(self, nodes):
        reroute = []
        for i in range(len(nodes)-1):
            reroute.append(self.network[nodes[i]][nodes[i+1]]['id'])
        return reroute


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print "Usage: " + sys.argv[0] + " <input network file> <input trip file> <output rou file> <real network or not>"
        print "Example: " + sys.argv[0] + "grid9x9.net.xml grid9x9.trip.xml grid9x9.rou.xml False"
        sys.exit()
    network = nx.DiGraph()
    sumo_net = net.readNet(sys.argv[1])
    real_net = eval(sys.argv[4])
    if real_net == True:
        for c in sumo_net.getConnections():
            from_edge = c.getFrom()
            network.add_edge(
                from_edge.getID().encode('utf-8'),
                c.getTo().getID().encode('utf-8'),
                {
                    'weight':  from_edge.getLength()/from_edge.getSpeed(),
                    'id': "from"+c.getFromLane().getID()+"_to"+c.getToLane().getID()
                }
            )
    else:
        for l in sumo_net.getEdges():
            network.add_edge(
                l.getFromNode().getID().encode('utf-8'),
                l.getToNode().getID().encode('utf-8'),
                {
                    'weight':  l.getLength()/l.getSpeed(),
                    'id': l.getID().encode('utf-8')
                }
            )
    parser = make_parser()
    reader = XMLTripReader(sys.argv[3], network, real_net)
    parser.setContentHandler(reader)
    parser.parse(sys.argv[2])
    print "sucess"
