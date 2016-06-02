# -*- coding: utf-8 -*-
import numpy


class Stigmergy:
    def __init__(self, free_flow_travel_time):
        self.free_flow_travel_time = free_flow_travel_time
        self.average = free_flow_travel_time
        self.std = 0.0
        self.__count = 0.0
        self.data_list = numpy.array([])

    def addStigmergy(self, data):
        self.data_list = numpy.hstack((self.data_list, numpy.array(data)))
        self.__count = len(self.data_list)
        if self.__count == 0:
            self.average = self.free_flow_travel_time
            self.std = 0.0
        else:
            self.average = numpy.average(self.data_list)
            self.std = numpy.std(self.data_list)

    def delStigmergy(self):
        self.data_list = numpy.array([])
        self.average = self.std = self.__count = 0.0

    # only short term stigmergy
    def resetStigmergy(self, data):
        self.delStigmergy()
        self.addStigmergy(data)

# def updatePastStigmergy(conf, stigmergy_network, long_term_stigmergy, short_term_stigermgy):
#     for l in stigmergy_network.edges():
#         tmp_long = long_term_stigmergy[stigmergy_network[l[0]][l[1]]['id']]
#         stigmergy_network[l[0]][l[1]]['weight']=\
#             (tmp_long.average+conf.long_term_sd*tmp_long.std)*conf.weight_of_past_stigmergy+\
#             short_term_stigermgy[stigmergy_network[l[0]][l[1]]['id']].average*(1-conf.weight_of_past_stigmergy)

# def updatePastStigmergyWithFree(conf, stigmergy_network, stigmergy_with_free_network, long_term_stigmergy, short_term_stigermgy):
#     for l in stigmergy_network.edges():
#         tmp_long = long_term_stigmergy[stigmergy_network[l[0]][l[1]]['id']]
#         stigmergy_network[l[0]][l[1]]['weight']=\
#             (tmp_long.average+conf.long_term_sd*tmp_long.std)*conf.weight_of_past_stigmergy+\
#             short_term_stigermgy[stigmergy_network[l[0]][l[1]]['id']].average*(1-conf.weight_of_past_stigmergy)
#         stigmergy_with_free_network[l[0]][l[1]]['weight']=\
#             (tmp_long.average+conf.long_term_sd*tmp_long.std)*conf.weight_of_past_stigmergy+\
#             *(1-conf.weight_of_past_stigmergy)

