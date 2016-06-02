# -*- coding: utf-8 -*-
from simulator import Simulator
import stigmergy, traci, copy, time, constants
import networkx as nx
from store import Store
from store_json import StoreJSON
import networkutility as netutil


class LongShortTermStigmergy(Simulator):
    def __init__(self):
        Simulator.__init__(self)
        self.stigmergy_network = copy.deepcopy(self.original_network)
        self.stigmergy_free_network = copy.deepcopy(self.original_network)

        self.long_term_stigmergies = self.short_term_stigmergies = {}
        self.today_long_term_stigmergy = self.today_short_term_stigmergy = {}
        self.edge_ids = [edge.getID().encode('utf-8') for edge in self.sumo_net.getEdges()]

        if self.conf.dce == True:
            self.dce_stigmergy = {}
            for node in self.sumo_net.getNodes():
                self.dce_stigmergy[node.getID().encode('utf-8')] = {}

    def initIteration(self):
        # setting long term stigmergy
        if self.long_term_stigmergies == {}:
            self.initStigmergy()

        # init route only long
        if self.conf.weight_of_past_stigmergy > 0.0:
            self.initRoute()

        self.today_long_term_stigmergy = dict([(edge_id, []) for edge_id in self.edge_ids])
        self.today_short_term_stigmergy = dict([(edge_id, []) for edge_id in self.edge_ids])

        if self.conf.dce == True:
            self.updateFreeStigmergy()

    def initRoute(self):
        for edge in self.stigmergy_network.edges():
            long_term_stigmergy = self.long_term_stigmergies[self.stigmergy_network[edge[0]][edge[1]]['id']]
            l_ave = long_term_stigmergy.average
            l_sd = long_term_stigmergy.std
            self.stigmergy_network[edge[0]][edge[1]]['weight'] = l_ave + self.conf.long_term_sd * l_sd

        for veh_id in traci.vehicle.getIDAllList():
            route = traci.vehicle.getRoute(veh_id)
            new_nodes = []

            if self.conf.real_net == True:
                origin_node_id = self.sumo_net.getEdge(route[0]).getFromNode().getID().encode('utf-8')
                dest_node_id = self.sumo_net.getEdge(route[-1]).getToNode().getID().encode('utf-8')
                new_route = netutil.searchRouteFromNode(self.sumo_net, self.stigmergy_network, origin_node_id, dest_node_id)
            else:
                origin_node_id = self.sumo_net.getEdge(route[0]).getFromNode().getID().encode('utf-8')
                dest_node_id = self.sumo_net.getEdge(route[-1]).getFromNode().getID().encode('utf-8')
                new_nodes = nx.astar_path(self.stigmergy_network, origin_node_id, dest_node_id, self.distFromNode)
                new_route = netutil.nodes2Route(self.stigmergy_network, new_nodes)

            traci.vehicle.setRoute(veh_id, new_route)

    def initStigmergy(self):
        # default travel time (sec) = length (m) / s(m/sec)
        self.long_term_stigmergies = dict([(edge_id, stigmergy.Stigmergy(
            netutil.freeFlowTravelTime(self.sumo_net, edge_id))) for edge_id in self.edge_ids])

        self.short_term_stigmergies = copy.deepcopy(self.long_term_stigmergies)

        # use stored data in long term stigmergy
        if self.conf.short_cut != -1:
            before_read_time = time.clock()

            if self.conf.redis_use:
                store = Store(self.conf.redis_host, self.network_file)
            else:
                store = StoreJSON(self.conf.short_cut_file, self.network_file, 'r')

            past_stigmergy_list = store.getLongTermStigmergy(self.conf.weight_of_past_stigmergy, self.conf.short_cut)

            for k in past_stigmergy_list:
                key = k.replace(store.createFileNameWithoutKey(
                    self.conf.weight_of_past_stigmergy,
                    self.conf.short_cut), "")
                data_list = [float(travel_time) for travel_time in store.getLongTermStigmergyWithKey(k)]
                self.long_term_stigmergies[key].addStigmergy(data_list)
            print("read long term stigmergy from redis(" + str(time.clock() - before_read_time) + "sec)")

    def updateFreeStigmergy(self):
        rho = self.conf.long_term_sd
        w = self.conf.weight_of_past_stigmergy

        for edge in self.stigmergy_network.edges():
            edge_id = self.stigmergy_network[edge[0]][edge[1]]['id']
            long_term_stigmergy = self.long_term_stigmergies[edge_id]
            l_ave = long_term_stigmergy.average
            l_sd = long_term_stigmergy.std
            t = self.original_network[edge[0]][edge[1]]['weight']
            self.stigmergy_free_network[edge[0]][edge[1]]['weight'] = (l_ave + rho * l_sd) * w + t * (1.0 - w)

    # update short_term_stigmergy
    def stepProcess(self):
        if traci.simulation.getCurrentTime() % self.conf.short_term_sec == 0:
            self.shortTermStep()

    def shortTermStep(self):
        for edge_id in self.short_term_stigmergies.keys():
            if traci.edge.getLastStepMeanSpeed(edge_id) > 0.1:
                self.today_long_term_stigmergy[edge_id].append(traci.edge.getTraveltime(edge_id))
                self.today_short_term_stigmergy[edge_id].append(traci.edge.getTraveltime(edge_id))
            self.short_term_stigmergies[edge_id].resetStigmergy(self.today_short_term_stigmergy[edge_id])

        self.today_short_term_stigmergy = dict([(edge_id, []) for edge_id in self.edge_ids])

        if self.conf.weight_of_past_stigmergy < 1.0:
            if self.conf.real_net == True:
                self.updateRealPastStigmergy()
            else:
                self.updatePastStigmergy()
            self.calcRoute()

    def updatePastStigmergy(self):
        rho = self.conf.long_term_sd
        w = self.conf.weight_of_past_stigmergy

        for edge in self.stigmergy_network.edges():
            edge_id = self.stigmergy_network[edge[0]][edge[1]]['id']
            long_term_stigmergy = self.long_term_stigmergies[edge_id]
            l_ave = long_term_stigmergy.average
            l_sd = long_term_stigmergy.std
            s_ave = self.short_term_stigmergies[edge_id].average
            self.stigmergy_network[edge[0]][edge[1]]['weight'] = (l_ave + rho * l_sd) * w + s_ave * (1.0 - w)

    def updateRealPastStigmergy(self):
        rho = self.conf.long_term_sd
        w = self.conf.weight_of_past_stigmergy
        for node_id in self.stigmergy_network.nodes():
            long_term_stigmergy = self.long_term_stigmergies[node_id]
            l_ave = long_term_stigmergy.average
            l_sd = long_term_stigmergy.std
            s_ave = self.short_term_stigmergies[node_id].average
            for dist in self.stigmergy_network[node_id].keys():
                self.stigmergy_network[node_id][dist]['weight'] = (l_ave + rho * l_sd) * w + s_ave * (1.0 - w)

    def calcRoute(self):
        if self.conf.dce == True:
            for node_id in self.dce_stigmergy.keys():
                self._addDCEStigmergyKey(node_id)

        for veh_id in traci.vehicle.getIDList():
            if self._options.gui:
                traci.vehicle.setColor(veh_id, (255, 255, 0, 255))

            route = traci.vehicle.getRoute(veh_id)
            current_road_id = traci.vehicle.getRoadID(veh_id)
            origin_node_id = self.sumo_net.getEdge(current_road_id).getToNode().getID().encode('utf-8')
            dest_node_id = self.sumo_net.getEdge(route[-1]).getToNode().getID().encode('utf-8')
            new_route = []

            if origin_node_id == dest_node_id:
                continue

            # decied vicinity area from root node
            if self.conf.dce == True:
                if self.dce_stigmergy[origin_node_id]['long_short'] is None:
                    network = self.calcDCE(origin_node_id, self.stigmergy_network)
                    self.dce_stigmergy[origin_node_id]['long_short'] = network
                else:
                    network = self.dce_stigmergy[origin_node_id]['long_short']
            else:
                network = self.stigmergy_network

            if self.conf.real_net == True:
                new_route = netutil.searchRouteFromNode(self.sumo_net, network, origin_node_id, dest_node_id)
            else:
                new_nodes = nx.astar_path(network, origin_node_id, dest_node_id, self.distFromNode)
                new_route = netutil.nodes2Route(self.original_network, new_nodes)

            reroute = route[:route.index(current_road_id) + 1] + new_route

            if route != reroute:
                traci.vehicle.setRoute(veh_id, reroute)

    def _addDCEStigmergyKey(self, node_id):
        self.dce_stigmergy[node_id]['long_short'] = None

    def calcDCE(self, root_node_id, adopt_network):
        dce_network = copy.deepcopy(self.stigmergy_free_network)
        root_node = self.sumo_net.getNode(root_node_id)

        def addList(index, node):  # 有効範囲だけstigmergyを反映
            if index == 0:
                return
            for incoming_edge in node.getIncoming():
                from_id = incoming_edge.getFromNode().getID().encode('utf-8')
                to_id = incoming_edge.getToNode().getID().encode('utf-8')
                dce_network[from_id][to_id] = adopt_network[from_id][to_id]
                addList(index-1, incoming_edge.getFromNode())

        addList(self.conf.dce_area, root_node)
        return dce_network

    def endIteration(self):
        # update long_term_stigmergy
        for edge_id in self.long_term_stigmergies.keys():
            self.long_term_stigmergies[edge_id].addStigmergy(self.today_long_term_stigmergy[edge_id])

    def run(self, offset):
        Simulator.run(self, offset)


if __name__ == "__main__":
    sim = LongShortTermStigmergy()
    print("weight: " + str(sim.conf.weight_of_past_stigmergy))
    for i in range(sim.conf.iteration):
        print("iteration: " + str(i))
        sim.run("longShort_w{0:02d}".format(int(sim.conf.weight_of_past_stigmergy * 100)) + "_i{0:03d}".format(i))
