# -*- coding: utf-8 -*-
import sys, csv, copy, random
import networkutility as netutil
import traci
from math import exp
import networkx as nx
from parkinglot import ParkingLot
from datacenter import DataCenter
from simulator import Simulator


class TestSimulation(Simulator):
    def __init__(self):
        Simulator.__init__(self)
        self.data_center = DataCenter()
        self.parking_lots = {}
        self.network_nx = copy.deepcopy(self.original_network)

        if self.conf.parking == True:
            self.readCSV()

    def readCSV(self):
        vehicle_reader = csv.reader(file(self.conf.vehicle_file, 'rU'))
        next(vehicle_reader)  # delete label
        for row in vehicle_reader:
            self.data_center.setVehicle(row[0], float(row[1]), int(row[2]))

        parking_reader = csv.reader(file(self.conf.parkinglot_file, 'rU'))
        next(parking_reader)  # delete label
        for row in parking_reader:
            self.parking_lots[row[0]] = ParkingLot(row[0], int(row[1]), int(row[2]))

    def initIteration(self):
        Simulator.initIteration(self)
        if traci.simulation.getLoadedNumber() > 0:
            self.setParking()
            self.initRoute()

    def setParking(self):
        for veh_id in traci.simulation.getLoadedIDList():
            route = traci.vehicle.getRoute(veh_id)
            dest_edge_id = route[-1]
            dest_edge = self.sumo_net.getEdge(dest_edge_id)
            dest_node_id = dest_edge.getToNode().getID()
            parking_range = self.data_center.getAllowableRange(veh_id)
            shortest_dict = {"id": None, "dist": float("inf")}

            for parking_node_id, parking_lot in self.parking_lots.items():
                if parking_node_id == dest_node_id:
                    continue

                dist = self.distFromNode(parking_node_id, dest_node_id)
                if parking_range > dist:
                    self.data_center.setAllowableParkingLot(veh_id, parking_node_id, dist)
                if shortest_dict["dist"] > dist:
                    shortest_dict["dist"] = dist
                    shortest_dict["id"] = parking_node_id
                if shortest_dict["dist"] > dist and parking_range > dist:
                    shortest_dict["dist"] = dist
                    self.data_center.setParkingID(veh_id, parking_node_id)

            if self.data_center.getParkingID(veh_id) is None:
                self.data_center.setParkingID(veh_id, shortest_dict["id"])

    def distFromNode(self, node_A_id, node_B_id):
        s = self.sumo_net.getNode(node_A_id).getCoord()
        t = self.sumo_net.getNode(node_B_id).getCoord()
        return ((s[0] - t[0]) ** 2 + (s[1] - t[1]) ** 2) ** 0.5

    def initRoute(self):
        for veh_id in traci.simulation.getLoadedIDList():
            route = traci.vehicle.getRoute(veh_id)

            origin_node_id = netutil.getFromNodeIDFromEdgeID(self.sumo_net, route[0])
            parking_node_id = self.data_center.getParkingID(veh_id)
            dest_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, route[-1])
            route_to_parking = netutil.searchRouteFromNode(self.sumo_net, self.network_nx, origin_node_id, parking_node_id)

            network_to_dest = copy.deepcopy(self.network_nx)
            network_to_dest.remove_node(netutil.getReverseEdge(route_to_parking[-1]))
            route_to_dest = netutil.searchRouteFromNode(self.sumo_net, network_to_dest, parking_node_id, dest_node_id)
            new_route = route_to_parking + route_to_dest
            print("init route: " + veh_id)
            traci.vehicle.setRoute(veh_id, new_route)

    def stepProcess(self):
        Simulator.stepProcess(self)
        if self.conf.parking == True:
            if traci.simulation.getLoadedNumber() > 0:
                self.setParking()
                self.initRoute()

            self.stepParking()
            self.stepVehicle()

    def stepParking(self):
        for parking_lot in self.parking_lots.values():
            parking_lot.updateState()
            parking_lot.updateArrival()

            for wait_veh_id in parking_lot.wait_vehicles:
                traci.vehicle.slowDown(wait_veh_id, speed=0.0, duration=100)

            unpark_vehicle_list = parking_lot.getUnparkList()
            for unpark_vehicle_id in unpark_vehicle_list:
                self.data_center.parkVehicle(unpark_vehicle_id)

            if len(unpark_vehicle_list) > 0:
                for wait_veh_id in parking_lot.wait_vehicles:
                    road_id = traci.vehicle.getRoadID(wait_veh_id)
                    road = self.sumo_net.getEdge(road_id)

                    lane_index = traci.vehicle.getLaneIndex(wait_veh_id)
                    lane = road.getLane(lane_index)
                    lane_id = lane.getID().encode('utf-8')

                    maxspeed = traci.lane.getMaxSpeed(lane_id)
                    traci.vehicle.slowDown(wait_veh_id, speed=maxspeed, duration=100000)

                parking_lot.clearWaitingVehicles()
                parking_lot.clearStartingVehicles()

    def stepVehicle(self):
        if self.conf.negotiation == True:
            self.stepNegotiation()
        self.updateVehicleState()

    def stepNegotiation(self):
        requested_vehicles = self.getRequestedVehicleList()
        for parking_id, parking_lot in self.parking_lots.items():
            # if self.data_center.shouldNegotiate(parking_id, parking_lot.getSpace(), requested_vehicles):
            if parking_lot.getSpace() < len(requested_vehicles[parking_id]):
                self.negotiateParkingLot(requested_vehicles[parking_id])

    def getRequestedVehicleList(self):
        requested_vehicles = dict([(parking_id, []) for parking_id in self.parking_lots.keys()])
        for veh_id in traci.vehicle.getIDList():
            if self.data_center.hasParked(veh_id) == True:
                continue

            parking_id = self.data_center.getParkingID(veh_id)
            requested_vehicles[parking_id].append(veh_id)
        return requested_vehicles

    def negotiateParkingLot(self, vehicles):
        for requester_id in vehicles:
            if self.data_center.hasNegotiated(requester_id):
                continue

            for requested_id in vehicles:
                if requested_id == requester_id or self.data_center.hasNegotiated(requested_id):
                    continue

                requested_allowables = self.data_center.getAllowableParkingLots(requested_id)
                if len(requested_allowables) < 1:
                    continue

                original_route = traci.vehicle.getRoute(requester_id)
                current_road_id = traci.vehicle.getRoadID(requester_id)
                origin_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, current_road_id)
                alternative_id = self.getFreeParkingLotsFromList(requested_allowables)[0]
                alternative_route = netutil.searchRouteFromNode(self.sumo_net, self.network_nx, origin_node_id, alternative_id)

                current_index = original_route.index(traci.vehicle.getRoadID(requester_id))
                origin_time = alternative_time = 0
                for edge_id in original_route[current_index:]:
                    if not edge_id == original_route[-1]:
                        next_edge_id = original_route[original_route.index(edge_id) + 1]
                    else:
                        next_edge_id = None
                    origin_time += netutil.getWeightFromRealEdgeID(edge_id, next_edge_id, self.network_nx)

                for edge_id in alternative_route[current_index:]:
                    if not edge_id == alternative_route[-1]:
                        next_edge_id = alternative_route[alternative_route.index(edge_id) + 1]
                    else:
                        next_edge_id = None
                    alternative_time += netutil.getWeightFromRealEdgeID(edge_id, next_edge_id, self.network_nx)

                requester_prob = self.logitFunction(self.conf.requesterB, origin_time, alternative_time)
                requested_prob = self.logitFunctionWithPoint(self.conf.requesterB, self.conf.point, origin_time, alternative_time)
                requester_prob = 0
                requested_prob = 0
                if requester_prob > random.uniform(0, 1.0) or requested_prob > random.uniform(0, 1.0):
                    continue

                original_route = traci.vehicle.getRoute(requested_id)
                current_road_id = traci.vehicle.getRoadID(requested_id)
                origin_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, current_road_id)
                dest_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, original_route[-1])
                route_to_parking = netutil.searchRouteFromNode(self.sumo_net, self.network_nx, origin_node_id, alternative_id)
                network_to_dest = copy.deepcopy(self.network_nx)
                network_to_dest.remove_node(netutil.getReverseEdge(route_to_parking[-1]))
                route_to_dest = netutil.searchRouteFromNode(self.sumo_net, network_to_dest, alternative_id, dest_node_id)

                alternative_route = route_to_parking + route_to_dest
                new_route = original_route[:original_route.index(current_road_id) + 1] + alternative_route

                if netutil.isRouteValid(new_route) == False:
                    continue

                print("requested: " + str(requested_id))
                print("alternative parking: " + str(alternative_id))
                traci.vehicle.setRoute(requested_id, new_route)
                traci.vehicle.setColor(requested_id, (255, 0, 0, 0))  # red
                self.data_center.setParkingID(requested_id, alternative_id)
                self.data_center.negotiateVehicle(requester_id)
                self.data_center.negotiateVehicle(requested_id)
                break

    def getFreeParkingLotsFromList(self, requested_list):
        free_parking_lots = []
        requested_vehicles = self.getRequestedVehicleList()
        for parking_id in requested_list:
            if self.parking_lots[parking_id].getSpace() > len(requested_vehicles[parking_id]):
                free_parking_lots.append(parking_id)
        return free_parking_lots

    def logitFunction(self, beta, t1, t2):
        return exp(-beta * t1) / (exp(-beta * t1) + exp(-beta * t2))

    def logitFunctionWithPoint(self, beta, point, t1, t2):
        return exp(-beta * t2 + point) / (exp(-beta * t1) + exp(-beta * t2))

    def updateVehicleState(self):
        for veh_id in traci.vehicle.getIDList():
            if self.data_center.hasParked(veh_id) == True:
                continue

            road_id = traci.vehicle.getRoadID(veh_id)
            road = self.sumo_net.getEdge(road_id)
            to_id = road.getToNode().getID().encode('utf-8')

            lane_index = traci.vehicle.getLaneIndex(veh_id)
            lane = road.getLane(lane_index)

            position = traci.vehicle.getLanePosition(veh_id)
            parking_position = lane.getLength()
            rest_dist = parking_position - position
            parking_id = self.data_center.getParkingID(veh_id)

            if to_id == parking_id:
                parking_lot = self.parking_lots[to_id]
                parking_time = self.data_center.getParkTime(veh_id)
                parking_space = parking_lot.getSpace()

                if parking_lot.existWaitingVehicle(veh_id):
                    continue

                try:
                    parking_lot.startParkingVehicle(veh_id, road_id, position, parking_position, lane_index, parking_time)
                except traci.TraCIException:
                    traci.vehicle.slowDown(veh_id, speed=1.0, duration=100)

                if parking_space < 1 and rest_dist < 30:
                    if self.conf.reroute == True:
                        self.data_center.tryPark(veh_id, parking_id)
                        self.rerouteVehicle(veh_id)
                    else:
                        parking_lot.addWaitingVehicle(veh_id, position)
                        try:
                            traci.vehicle.setStop(veh_id, road_id, position, lane_index, flags=0)
                        except:
                            traci.vehicle.slowDown(veh_id, speed=0.0, duration=100)

    def rerouteVehicle(self, veh_id):
        route = traci.vehicle.getRoute(veh_id)
        current_road_id = traci.vehicle.getRoadID(veh_id)
        origin_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, current_road_id)
        dest_node_id = netutil.getToNodeIDFromEdgeID(self.sumo_net, route[-1])

        shortest_dict = {"id": None, "dist": float("inf")}
        for parking_node_id, parking_lot in self.parking_lots.items():
            if self.data_center.hasTriedPark(veh_id, parking_node_id):
                continue

            dist = self.distFromNode(parking_node_id, dest_node_id)
            if shortest_dict["dist"] > dist:
                shortest_dict["dist"] = dist
                shortest_dict["id"] = parking_node_id
                self.data_center.setParkingID(veh_id, parking_node_id)

        alternative_id = shortest_dict["id"]

        network_to_parking = copy.deepcopy(self.network_nx)
        network_to_parking.remove_node(netutil.getReverseEdge(current_road_id))
        route_to_parking = netutil.searchRouteFromNode(self.sumo_net, network_to_parking, origin_node_id, alternative_id)

        network_to_dest = copy.deepcopy(self.network_nx)
        network_to_dest.remove_node(netutil.getReverseEdge(route_to_parking[-1]))
        route_to_dest = netutil.searchRouteFromNode(self.sumo_net, network_to_dest, alternative_id, dest_node_id)

        alternative_route = route_to_parking + route_to_dest
        new_route = route[:route.index(current_road_id) + 1] + alternative_route

        if netutil.isRouteValid(new_route) == False:
            self.data_center.tryPark(veh_id, alternative_id)
            self.rerouteVehicle(veh_id)
        else:
            print("rerouted: " + str(veh_id) + " alternative parking: " + str(alternative_id))
            print(new_route)

            try:
                traci.vehicle.clearStops(veh_id)
            except traci.TraCIException:
                pass

            traci.vehicle.setRoute(veh_id, new_route)

            if len(self.data_center.getTriedParkingLots(veh_id)) == 1:
                traci.vehicle.setColor(veh_id, (0, 255, 0, 0))  # green
            elif len(self.data_center.getTriedParkingLots(veh_id)) == 2:
                traci.vehicle.setColor(veh_id, (0, 0, 255, 0))  # blue
            elif len(self.data_center.getTriedParkingLots(veh_id)) == 3:
                traci.vehicle.setColor(veh_id, (255, 255, 255, 0))  # white
            elif len(self.data_center.getTriedParkingLots(veh_id)) == 4:
                traci.vehicle.setColor(veh_id, (0, 0, 0, 0))  # black

    def endIteration(self):
        Simulator.endIteration(self)

    def run(self, offset):
        Simulator.run(self, offset)


if __name__ == '__main__':
    sim = TestSimulation()
    sim.run("TestSimulation")
