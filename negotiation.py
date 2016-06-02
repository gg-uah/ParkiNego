# -*- coding: utf-8 -*-
import sys, os, util, random
from anticipatory_stigmergy import AnticipatoryStigmergy as astigmergy
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/assign')
from random_assign import RandomAssign
import traci
import networkutility as netutil
from math import exp


class Negotiation(astigmergy):
    class VehicleInfo:
        def __init__(self, route, reroute, diff, route_time, reroute_time):
            self.route = route
            self.reroute = reroute
            self.diff = diff

            if self.route == self.reroute:
                self.same = True
            else:
                self.same = False

            self.route_time = route_time
            self.reroute_time = reroute_time
            self.succusseNegotiation = False

        def setNegotiation(self, negotiation_result):
            self.succusseNegotiation = negotiation_result

        def to_s(self):
            return self.diff, self.route + "(" + self.route_time + ")", self.reroute + "(" + self.reroute_time + ")", self.same

    def initIteration(self):
        astigmergy.initIteration(self)

    def assignRoute(self):
        # gather vehicle information about original route and anticipatory route
        vehicle_info = {}

        for veh_id in traci.vehicle.getIDAllList():
            route, reroute = self.getAnticipatoryStigmergyRoute(veh_id)
            vehicle_info[veh_id] = self.__calcDiff__(veh_id, route, reroute)

        for edge_id in self.anticipatory_stigmergy.keys():
            estimate_vehicles = self.anticipatory_stigmergy[edge_id]
            swap_list = {}  # requested vehicle key => [requester vehicle list]

            edge = self.sumo_net.getEdge(edge_id)
            volume = len(estimate_vehicles)
            if netutil.isCongestion(edge, volume, self.conf.congestion_judgement) == False:  # notCongestion
                continue

            # random assignment
            random.shuffle(estimate_vehicles)

            # reject vehicles that have same route
            for ant_veh_id in estimate_vehicles:
                if vehicle_info[ant_veh_id].same == True or vehicle_info[ant_veh_id].route_time == 0:
                    estimate_vehicles.remove(ant_veh_id)

            # negotiation process
            # requester
            requester_number = int(len(estimate_vehicles) - netutil.calcEdgeCapacity(
                self.sumo_net.getEdge(edge_id)) * self.conf.congestion_judgement)
            requester_list = estimate_vehicles[0:requester_number]
            requested_list = estimate_vehicles[requester_number:len(estimateVehicles)]

            if requester_number < 0:
                continue

            for requester in requester_list:
                route_time = vehicle_info[requester].route_time
                reroute_time = vehicle_info[requester].reroute_time

                if self.calcLogitValue(self.conf.requesterB, route_time, reroute_time) < random.uniform(0, 1.0):
                    # not request
                    continue

                for requested in requested_list:
                    self.negotiation_info_in_iteration['request'] += 1

                    if self.calcLogitValueWithPoint(
                        self.conf.requestedB, self.conf.point, route_time, reroute_time) >= random.uniform(0, 1.0):
                        # request success
                        self.negotiation_info_in_iteration['accept'] += 1

                        if requested in swap_list:
                            swap_list[requested].append(requester)
                        else:
                            swap_list[requested] = [requester]

            # sort of swap_list
            self.sortByMaxReduce(swap_list, vehicle_info)
            for requested in swap_list.keys():
                for requester in swap_list[requested]:
                    if requester in requester_list:
                        util.swapValue(requester_list, requested_list, requester, requested)
                        break

            # assign anticipatory stigmergy route
            for ant_veh_id in requester_list:
                traci.vehicle.setRoute(ant_veh_id, vehicle_info[ant_veh_id].reroute)

                if self._options.gui:
                    traci.vehicle.setColor(ant_veh_id, (255, 0, 255, 255))

    def __calcDiff__(self, veh_id, route, reroute):
        sum_origin_route = sum_detour_route = 0
        index = route.index(traci.vehicle.getRoadID(veh_id))
        current_edge_weight = netutil.getWeightFromEdgeID(route[index], self.stigmergy_network, self.sumo_net)

        for edge_id in route[index:]:
            sum_origin_route += netutil.getWeightFromEdgeID(edge_id, self.stigmergy_network, self.sumo_net)

        for edge_id in reroute[index:]:
            sum_detour_route += netutil.getWeightFromEdgeID(edge_id, self.stigmergy_network, self.sumo_net)

        diff = sum_detour_route - sum_origin_route
        route_time = sum_origin_route - current_edge_weight
        reroute_time = sum_detour_route - current_edge_weight
        return Negotiation.VehicleInfo(route, reroute, diff, route_time, reroute_time)

    def calcLogitValue(self, beta, t1, t2):
        return exp(-beta * t1) / (exp(-beta * t1) + exp(-beta * t2))

    def calcLogitValueWithPoint(self, beta, point, t1, t2):
        return exp(-beta * t2 + point) / (exp(-beta * t1) + exp(-beta * t2))

    def sortByMaxReduce(self, swap_list, vehicle_info):
        for key in swap_list.keys():
            swap_list[key].sort(cmp=lambda x, y: cmp(vehicle_info[x].diff, vehicle_info[y].diff), reverse=True)

    def endIteration(self):
        astigmergy.endIteration(self)
        self.negotiation_info.append(self.negotiation_info_in_iteration.values())

    def initSimulation(self, assign_strategy):
        astigmergy.initSimulation(self, assign_strategy)
        random.seed(100)
        self.negotiation_info = []
        self.negotiation_info_in_iteration = {'request': 0, 'accept': 0}
        self.negotiation_info.append(self.negotiation_info_in_iteration.keys())

    def writeNegotiationInfo(self):
        import csv
        writer = csv.writer(file(self.conf.output_dir + "/" + self.conf.offset + ".csv", 'w'))
        writer.writerows(self.negotiation_info)

if __name__ == '__main__':
    sim = Negotiation()
    sim.conf.port = 8812
    sim.conf.short_cut = 400
    sim.conf.weight_of_past_stigmergy = 0.9
    sim.initSimulation(RandomAssign())
    # iteration
    for i in range(sim.conf.iteration - 400):
        # for i in [0]:
        print("num:", i)
        for j in [0.01, 0.05, 0.1, 0.25, 0.5, 0.75]:
            sim.conf.requesterB = sim.conf.requestedB = j
            sim.run("Nego_w{0:03d}".format(
                int(sim.conf.weight_of_past_stigmergy * 100))
                + "_i{0:03d}".format(i) + "_B{0:.2f}".format(sim.conf.requesterB))

    sim.writeNegotiationInfo()
