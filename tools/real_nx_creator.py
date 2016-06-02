# -*- coding: utf-8 -*-
import networkx as nx
from sumolib import net
from xml.sax import saxutils, make_parser, handler

class XMLNetReader(handler.ContentHandler):
	def __init__(self):
		self.network = nx.DiGraph()
		self.weight_hash = {}
		self.node_hash = {}

	def endDocument(self):
		for n in self.network.nodes():
			self.network.add_node(n, {'node_info':self.node_hash[n]})

	def startElement(self, name, attrs):
		if name == 'connection' and attrs.getValue('from')[0]!=':' :
			from_id=attrs.getValue('from')
			self.network.add_edge(\
				from_id,\
				attrs.getValue('to'),\
				{\
					'weight': self.weight_hash[from_id]\
				})
		elif name == 'edge' and attrs.getValue('id')[0]!=':' :
			self.__edge_id=attrs.getValue('id').encode('utf-8')
			self.node_hash[self.__edge_id]="from"+attrs.getValue('from')+"_to"+attrs.getValue('to')
		elif name == 'lane' and attrs.getValue('id')[0]!=':':
			self.weight_hash[self.__edge_id]=float(attrs.getValue('length'))/float(attrs.getValue('speed'))

def createNetwork(network_path):
	parser = make_parser()
	reader = XMLNetReader()
	parser.setContentHandler(reader)
	parser.parse(network_path)
	return reader.network


if __name__ == '__main__':
	print reader.network.nodes(data=True)
