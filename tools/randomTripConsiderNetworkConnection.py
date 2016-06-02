#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys, os
from optparse import OptionParser
import datetime
import networkx as nx
from sumolib import net
from real_nx_creator import createNetwork

if 'SUMO_HOME' in os.environ:
	tools = os.path.join(os.environ['SUMO_HOME'], 'trip')
	sys.path.append(os.path.join(tools))
	from randomTrips import randomEdgeGenerator
else:
	sys.exit("please declare environment variable 'SUMO_HOME'")
#sys.path.append(os.path.dirname('$SUMO_HOME/trip'))

def checkConnection(network, from_node_id, to_node_id):
	try:
		nx.dijkstra_path(\
			network, \
			from_node_id,\
			to_node_id\
		)
	except nx.exception.NetworkXNoPath, e:
		return False
	return True

def get_options():
	optParser = OptionParser()
	optParser.add_option("-n", "--net-file", dest="netfile",
							help="define the net file (mandatory)")
	optParser.add_option("-o", "--output-trip-file", dest="tripfile",
						 default="trips.trips.xml", help="define the output trip filename")
	optParser.add_option("-r", "--route-file", dest="routefile",
						 help="generates route file with duarouter")
	optParser.add_option("-t", "--trip-id-prefix", dest="tripprefix",
						 default="", help="prefix for the trip ids")
	optParser.add_option("-a", "--trip-parameters", dest="trippar",
						 default="", help="additional trip parameters")
	optParser.add_option("-b", "--begin", type="float", default=0, help="begin time")
	optParser.add_option("-e", "--end", type="float", default=3600, help="end time (default 3600)")
	optParser.add_option("-p", "--period", type="float", default=1, help="repetition period (default 1)")
	optParser.add_option("-s", "--seed", type="int", help="random seed")
	optParser.add_option("-l", "--length", action="store_true",
						 default=False, help="weight edge probability by length")
	optParser.add_option("-L", "--lanes", action="store_true",
						 default=False, help="weight edge probability by number of lanes")
	optParser.add_option("--speed-exponent", type="float", dest="speed_exponent",
						 default=0.0, help="weight edge probability by speed^<FLOAT> (default 0)")
	optParser.add_option("--fringe-factor", type="float", dest="fringe_factor",
						 default=1.0, help="multiply weight of fringe edges by <FLOAT> (default 1")
	optParser.add_option("--fringe-threshold", type="float", dest="fringe_threshold",
						 default=0.0, help="only consider edges with speed above <FLOAT> as fringe edges (default 0)")
	optParser.add_option("--min-distance", type="float", dest="min_distance",
						 default=0.0, help="require start and end edges for each trip to be at least <FLOAT> m appart (default 0)")
	optParser.add_option("-v", "--verbose", action="store_true",
						 default=False, help="tell me what you are doing")
	(options, args) = optParser.parse_args()
	return options


def main(options):
	if not options.netfile:
		print "Usage: python " + sys.argv[0] + " -n <input network file> -b 0 -e 100 -p 1 -o <output trip file>"
		sys.exit()
	if options.seed:
		random.seed(options.seed)
	original_network = createNetwork(options.netfile)

	def edge_probability(edge):
		prob = 1
		if options.length:
			prob *= edge.getLength()
		if options.lanes:
			prob *= edge.getLaneNumber()
		prob *= (edge.getSpeed() ** options.speed_exponent)
		if (options.fringe_factor != 1.0 and
				edge.getSpeed() > options.fringe_threshold and
				edge.is_fringe()):
			prob *= options.fringe_factor
		return prob

	edge_generator = randomEdgeGenerator(options.netfile, edge_probability)
	idx = 0
	with open(options.tripfile, 'w') as fouttrips:
		print >> fouttrips, """<?xml version="1.0"?>
<!-- generated on %s by $Id: randomTrips.py 14425 2013-08-16 20:11:47Z behrisch $ -->
<trips>""" % datetime.datetime.now()
		depart = options.begin
		print idx
		while depart < options.end:
			label = "%s%s" % (options.tripprefix, idx)
			source_edge, sink_edge = edge_generator.get_trip(options.min_distance)
			if checkConnection(original_network, source_edge.getID(), sink_edge.getID()):
				print >> fouttrips, '	<trip id="%s" depart="%.2f" from="%s" to="%s" %s/>' % (
						label, depart, source_edge.getID(), sink_edge.getID(), options.trippar)
				idx += 1
				print "\r",idx
				depart += options.period
		fouttrips.write("</trips>")

	if options.routefile:
		subprocess.call(['duarouter', '-n', options.netfile, '-t', options.tripfile, '-o', options.routefile, '--ignore-errors',
			'--begin', str(options.begin), '--end', str(options.end)])


if __name__ == "__main__":
	main(get_options())