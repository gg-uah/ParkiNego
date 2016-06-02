# -*- coding: utf-8 -*-
import json
import redis
from datetime import datetime as dt
"""
 ****only use for list***
"""

def exportRedis(host, port, db, key):
	rc = redis.Redis(host = host, port = port, db = db)
	keys = rc.keys(key)
	value = [rc.lrange(tmp_key, 0, -1) for tmp_key in keys]
	output = json.dumps(dict(zip(keys, value)), indent = 4)
	f = open(dt.now().strftime('%Y_%m_%d_%H_%M_%S') + key.replace('*', '').replace('.', '_') + "dump.json", "w")
	f.write(output)
	f.close()

def importRedis(host, port, db, file_name):
	input = ""
	for r in open(file_name, 'r'):
		input += r
	input_json = json.loads(input)
	rc = redis.Redis(host = host, port = port, db = db)
	[rc.lpush(key, 0, *input_json[key]) for key in input_json.keys()]
import glob

if __name__ == '__main__':
	host = 'localhost'
	port = 6379
	db = 0
	for w in range(1,11):
		exportRedis(host, port, db, "barcelona.net.xml:w" + str(float(w) / 10) + ":*")
#	for file in glob.glob('2013_11_07_09_50_36grid9x9_net_xml:w0_6:ite400dump.json'):
#		print file
#		importRedis(host, port, db, file)
