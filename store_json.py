# -*- coding: utf-8 -*-
import os.path as path
import json


class StoreJSON:
    def __init__(self, file, network, read_or_write):
        self.network = network
        if read_or_write == 'r':
            input = ""
            for r in open(file, 'r'):
                input += r
            self.dict = json.loads(input)
        elif read_or_write == 'w':
            self.dict = {}
            self.output_file = file

    def __createFileName__(self, weight, iteration, edge):
        return path.basename(self.network) + ":w" + str(weight) + ":ite" + str(iteration) + ":edge"+edge

    def createFileNameWithoutKey(self, weight, iteration):
        return path.basename(self.network) + ":w" + str(weight) + ":ite" + str(iteration) + ":edge"

    def delLongTermStigmergy(self, weight, iteration, edge):
        del self.dict[self.__createFileName__(weight, iteration, edge)]

    def addLongTermStigmergy(self, weight, iteration, data):
        for edge in data.keys():
            self.dict[self.__createFileName__(weight, iteration, edge)] = data[edge].data_list

    def write(self, weight, iteration, edge):
        output = json.dumps(self.dict, indent=4)
        file_name = self.__createFileName__(weight, iteration, edge).replace('.', '_')
        f = open(dt.now().strftime('%Y_%m_%d_%H_%M_%S') + file_name + "dump.json", "w")
        f.write(output)
        f.close()

    def getLongTermStigmergyWithEdge(self, weight, iteration, edge):
        return self.dict[self.__createFileName__(weight, iteration, edge)]

    def getLongTermStigmergyWithKey(self, key):
        return self.dict[key]

    def getLongTermStigmergy(self, weight, iteration):
        ans = {}
        for k in self.dict.keys():
            if k.startswith(self.createFileNameWithoutKey(weight, iteration)):
                ans[k] = self.dict[k]
        return ans

    def getKeys(self):
        return self.dict.keys()
