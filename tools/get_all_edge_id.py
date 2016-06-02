#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sumolib import net
import sys

if __name__ == '__main__':
	if len(sys.argv) < 2:
		print "Usage: " + sys.argv[0] + " <input network file>"
		sys.exit()

	sumo_net = net.readNet(sys.argv[1])
	print_str = "\""

	for i, e in enumerate(sumo_net.getNodes()):
		if i != len(sumo_net.getNodes()) - 1:
			print_str += e.getID() + ","
		else:
			print print_str + e.getID() + "\""
