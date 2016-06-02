#!/usr/bin/env python
# -*- coding: utf-8 -*-
from sumolib import output
#import os
from glob import glob
import re
from os import path


def averageTravelTimePlusDepartDelay(elements):
	a = output.list(elements, 'duration')
	b = output.list(elements, 'departDelay')
	return reduce(lambda x,y: x+y, [a[i]+b[i] for i in range(len(a))])/len(a)

def varianceTravelTimePlusDepartDelay(elements):
	ave = averageTravelTimePlusDepartDelay(elements)
	a = output.list(elements, 'duration')
	b = output.list(elements, 'departDelay')
	return reduce(lambda x,y: x+y, [(a[i]+b[i]-ave)**2 for i in range(len(a))])/len(a)

def sumTravelTimePlusDepartDelay(elements):
	a = output.list(elements, 'duration')
	b = output.list(elements, 'departDelay')
	return reduce(lambda x,y: x+y, [a[i]+b[i] for i in range(len(a))])

if __name__ == "__main__":
	file_list = glob(path.dirname( path.abspath( __file__ ) )+'/../output/*.xml')
	file_list.sort()
	print 'offset, weight, iteration'\
				', average_travel_time(s)'\
				', variance_travel_time(s*volume)'\
				', total_travel_time(s*volume)'\
				', average_time_loss_in_congestion(s)'\
				', variance_time_loss_in_congestion(s)'\
				', total_time_loss_in_congestion(s*volume)'\
				', average_depart_delay(s)'\
				', variance_depart_delay(s)'\
				', total_depart_delay(s*volume)'\
				', average_total_travel_time+depart_delay(s)'\
				', variance_total_travel_time+depart_delay(s)'\
				', total_total_travel_time+depart_delay(s*volume)'\

	for f in file_list:
		print re.sub(r'.*[/|](.+)_w([0-9]+)_i([0-9]+)\.xml', r"\1, \2, \3", f)+", ",
#		print f.replace('tripinfo', '').replace('.xml', ''),', ',
		parse_obj = output.parse(f, ["tripinfo"])
		alist = [tripinfo for tripinfo in parse_obj]
		print output.average(alist, 'duration'),', ',
		print output.variance(alist, 'duration'),', ',
		print output.sum(alist, 'duration'),', ',
		print output.average(alist, 'waitSteps'),', ',
		print output.variance(alist, 'waitSteps'),', ',
		print output.sum(alist, 'waitSteps'),', ',
		print output.average(alist, 'departDelay'),', ',
		print output.variance(alist, 'departDelay'),', ',
		print output.sum(alist, 'departDelay'),', ',
		print averageTravelTimePlusDepartDelay(alist),', ',
		print varianceTravelTimePlusDepartDelay(alist),', ',
		print sumTravelTimePlusDepartDelay(alist)

