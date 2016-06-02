# -*- coding: utf-8 -*-
import redis
import os.path as path
import stigmergy


class Store:
    def __init__(self, host, network):
        self.rc = redis.Redis(host=host, port=6379, db=0)
        self.netwotk = network

    def __createFileName__(self, weight, iteration, edge):
        return path.basename(self.network) + ":w" + str(weight) + ":ite" + str(iteration) + ":edge" + edge

    def createFileNameWithoutKey(self, weight, iteration):
        return path.basename(self.network) + ":w" + str(weight) + ":ite" + str(iteration) + ":edge"

    def delLongTermStigmergy(self, weight, iteration, edge):
        self.rc.delete(self.__createFileName__(weight, iteration, edge))

    def addLongTermStigmergy(self, weight, iteration, data):
        [[self.rc.lpush(self.__createFileName__(weight, iteration, edge), d) for d in data[edge].data_list] for edge in data.keys()]

    def getLongTermStigmergyWithEdge(self, weight, iteration, edge):
        return self.rc.lrange(self.__createFileName__(weight, iteration, edge), 0, -1)

    def getLongTermStigmergyWithKey(self, key):
        return self.rc.lrange(key, 0, -1)

    def getLongTermStigmergy(self, weight, iteration):
        return self.rc.keys(self.createFileNameWithoutKey(weight, iteration) + "*")

    def getKeys(self):
        return self.rc.keys()
