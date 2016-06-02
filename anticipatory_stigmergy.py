# -*- coding: utf-8 -*-
import sys, os, copy
from long_short_stigmergy import LongShortTermStigmergy as ls
import networkx as nx
import traci
import networkutility as netutil
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/assign')
from random_assign import RandomAssign


class AnticipatoryStigmergy(ls):
    def __init__(self, assign_strategy):
        ls.__init__(self)
        self.anticipatory_stigmergy_network = copy.deepcopy(self.original_network)
        self.assign_strategy = assign_strategy

    # add stigmergy in distributed processing environment
    # and reset every x seconds
    def _addDCEStigmergyKey(self, node_id):
        ls._addDCEStigmergyKey(self, node_id)
        self.dce_stigmergy[node_id]['anticipatory'] = None

    def initIteration(self):
        ls.initIteration(self)
        self.shortTermStep()  # in order to assign initial vehicles

    def stepProcess(self):
        ls.stepProcess(self)

    def shortTermStep(self):
        ls.shortTermStep(self)
        self.calcAnticipatoryStigmergy()
        self.assignRoute()

    def calcAnticipatoryStigmergy(self):
        self.anticipatory_stigmergies = dict([(edge_id, []) for edge_id in self.edge_ids])
        for veh_id in traci.vehicle.getIDAllList():
            # update stigmergy in every 60 min
            if traci.vehicle.getDepart(veh_id) - traci.simulation.getCurrentTime() > self.conf.short_term_sec:
                continue

            route = traci.vehicle.getRoute(veh_id)

            if self._options.gui:
                traci.vehicle.setColor(veh_id, (255, 255, 0, 255))

            if traci.vehicle.getRoadID(veh_id) == "":  # not assigned vehicle
                current_road_id = route[0]
                time_index = (traci.vehicle.getDepart(veh_id) - traci.simulation.getCurrentTime()) / 1000
            else:  # assigned vehicle
                current_road_id = traci.vehicle.getRoadID(veh_id)
                time_index = 0

            if self.conf.real_net == True:
                if current_road_id == route[-1]:
                    to_edge = self.sumo_net.getEdge(current_road_id).getToNode().getOutgoing()[-1].getID().encode('utf-8')
                else:
                    to_edge = route[route.index(current_road_id)+1]
                weight = netutil.getWeightFromRealEdgeID(current_road_id, to_edge, self.stigmergy_network)
            else:
                weight = netutil.getWeightFromEdgeID(current_road_id, self.stigmergy_network, self.sumo_net)

            current_position = traci.vehicle.getLanePosition(veh_id)
            dest_position = self.sumo_net.getEdge(current_road_id).getLength()
            rest_dist_ratio = 1 - current_position / dest_position

            # rest time after subtracting 60 min from time arriving terminal of edge where vhehicle is now
            rest_time = float(self.conf.short_term_sec) / 1000 - time_index - float(weight) * rest_dist_ratio

            if rest_time < 0:  # keep position
                self.anticipatory_stigmergies[current_road_id].append(veh_id)
                continue

            # estimate where are vhiecles after 60 min
            for edge_id in route[route.index(current_road_id) + 1:]:
                if self.conf.real_net == True:
                    if edge_id == route[-1]:
                        to_edge = self.sumo_net.getEdge(edge_id).getToNode().getOutgoing()[-1].getID().encode('utf-8')
                    else:
                        to_edge = route[route.index(edge_id)+1]
                    weight = netutil.getWeightFromRealEdgeID(edge_id, to_edge, self.stigmergy_network)
                else:
                    weight = netutil.getWeightFromEdgeID(edge_id, self.stigmergy_network, self.conf.sumo_net)

                rest_time -= weight
                if rest_time < 0:  # stop this link
                    self.anticipatory_stigmergies[edge_id].append(veh_id)
                    break

        for edge in self.anticipatory_stigmergy_network.edges():
            self.anticipatory_stigmergy_network[edge[0]][edge[1]]['weight'] = self.bpr(
                self.conf.alpha,
                self.conf.beta,
                self.conf.congestion_bpr,
                self.original_network[edge[0]][edge[1]]['weight'],
                len(self.anticipatory_stigmergies[self.anticipatory_stigmergy_network[edge[0]][edge[1]]['id']]),
                self.original_network[edge[0]][edge[1]]['capacity'])

    # bpr function
    def bpr(self, alpha, beta, congestion_bpr, t, volume, capacity):
        return t * (1 + alpha * (float(volume) / (congestion_bpr * capacity)) ** beta)

    def assignRoute(self):
        for edge_id in self.anticipatory_stigmergies.keys():
            estimate_vehicles = self.assign_strategy.sort(self.anticipatory_stigmergies[edge_id])

            edge = self.sumo_net.getEdge(edge_id)
            volume = len(estimate_vehicles)
            if netutil.isCongestion(edge, volume, self.conf.congestion_judgement) == False:  # not Congestion
                continue

            assign_counter = 0
            for veh_id in estimate_vehicles:
                route, reroute = self.getAnticipatoryStigmergyRoute(veh_id)
                route_index = -1

                # strictly check(いいのか？)
                if not route[route_index + 1:route_index + 3] == reroute[route_index + 1:route_index + 3]:
                    if self._options.gui:
                        traci.vehicle.setColor(veh_id, (255, 0, 255, 255))
                    traci.vehicle.setRoute(veh_id, reroute)
                    assign_counter += 1

                    edge_capacity = netutil.calcEdgeCapacity(edge)
                    if assign_counter >= volume - edge_capacity * self.conf.congestion_division:
                        break

    def getAnticipatoryStigmergyRoute(self, veh_id):
        route = traci.vehicle.getRoute(veh_id)
        reroute = []

        if traci.vehicle.getRoadID(veh_id) != "":
            current_road_id = traci.vehicle.getRoadID(veh_id)
            origin_node_id = self.sumo_net.getEdge(current_road_id).getToNode().getID().encode('utf-8')
        else:
            current_road_id = self.sumo_net.getEdge(route[0]).getID().encode('utf-8')
            origin_node_id = self.sumo_net.getEdge(current_road_id).getFromNode().getID().encode('utf-8')

        dest_node_id = self.sumo_net.getEdge(route[-1]).getToNode().getID().encode('utf-8')

        if self.conf.dce == True:
            if self.dce_stigmergy[origin_node_id]['anticipatory'] is None:
                network = self.calcDCE(origin_node_id, self.anticipatory_stigmergy_network)
                self.dce_stigmergy[origin_node_id]['anticipatory'] = network
            else:
                network = self.dce_stigmergy[origin_node_id]['anticipatory']
        else:
            network = self.anticipatory_stigmergy_network

        if self.conf.real_net == True:
            new_route = netutil.searchRouteFromNode(self.sumo_net, network, origin_node_id, dest_node_id)
        else:
            new_nodes = nx.astar_path(network, origin_node_id, dest_node_id, self.distFromNode)
            new_route = netutil.nodes2Route(self.original_network, new_nodes)

        reroute = route[:route.index(current_road_id)] + new_route
        return route, reroute


if __name__ == "__main__":
    sim = AnticipatoryStigmergy(RandomAssign())
    print("weight: " + str(sim.conf.weight_of_past_stigmergy))
    for i in range(sim.conf.iteration):
        print("num: " + str(i))
        sim.run("Ant_w{0:03d}".format(int(sim.conf.weight_of_past_stigmergy * 100)) + "_i{0:03d}".format(i))
