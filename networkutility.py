# -*- coding: utf-8 -*-
import constants
import math
import traci
import networkx as nx


def readNetwork(sumo_net, original_network):  # Edgeに対する特徴付け
    for edge in sumo_net.getEdges():
        original_network.add_edge(
            edge.getFromNode().getID().encode('utf-8'),
            edge.getToNode().getID().encode('utf-8'),
            {
                'id': edge.getID().encode('utf-8'),
                'weight': edge.getLength() / edge.getSpeed(),
                'capacity': math.ceil(calcEdgeCapacity(edge))
            })

def readRealNetwork(sumo_net, original_network):  # 一方通行、右折禁止などに対する処理
    for conn in sumo_net.getConnections():
        from_edge = conn.getFromEdge()
        to_edge = conn.getToEdge()
        original_network.add_edge(
            from_edge.getID().encode('utf-8'),
            to_edge.getID().encode('utf-8'),
            {
                'id': from_edge.getID().encode('utf-8'),
                'weight':  from_edge.getLength()/from_edge.getSpeed(),
                'capacity': math.ceil(calcEdgeCapacity(from_edge))
            })

def getFromNodeIDFromEdgeID(sumo_net, edge_id):
    return sumo_net.getEdge(edge_id).getFromNode().getID().encode('utf-8')

def getToNodeIDFromEdgeID(sumo_net, edge_id):
    return sumo_net.getEdge(edge_id).getToNode().getID().encode('utf-8')

def freeFlowTravelTime(sumo_net, edge_id):
    return float(sumo_net.getEdge(edge_id).getLength()) / sumo_net.getEdge(edge_id).getSpeed()

def getWeightFromEdgeID(edge_id, nx_net, sumo_net):
    from_node_id = sumo_net.getEdge(edge_id).getFromNode().getID().encode('utf-8')
    to_node_id = sumo_net.getEdge(edge_id).getToNode().getID().encode('utf-8')
    return nx_net[from_node_id][to_node_id]['weight']

def getWeightFromRealEdgeID(from_edge_id, to_edge_id, nx_net):
    try:
        return nx_net[from_edge_id][to_edge_id]['weight']
    except KeyError:
        return traci.edge.getTraveltime(from_edge_id)

def getCapacityFromEdgeID(edge_id, nx_net, sumo_net):
    from_node_id = sumo_net.getEdge(edge_id).getFromNode().getID().encode('utf-8')
    to_node_id = sumo_net.getEdge(edge_id).getToNode().getID().encode('utf-8')
    return nx_net[from_node_id][to_node_id]['capacity']

def getCapacityFromRealEdgeID(from_edge_id, to_edge_id, nx_net):
    try:
        return nx_net[from_edge_id][to_edge_id]['capacity']
    except KeyError:
        return calcEdgeCapacity(from_edge_id)

def calcEdgeCapacity(sumo_lib_edge):
    edge_length = sumo_lib_edge.getLength()
    space = constants.VEHICLE_MINGAP
    perm_lanes = sumo_lib_edge.getLaneNumber()
    vehicle_length = constants.VEHICLE_LENGTH
    return edge_length * perm_lanes / (vehicle_length + space)

def isCongestion(sumo_lib_edge, volume, judgment_ratio):
    return calcEdgeCapacity(sumo_lib_edge) * judgment_ratio < volume

def neighborEdges(sumo_net, current_road_id):
    from_node = sumo_net.getEdge(current_road_id).getToNode()
    return from_node.getIncoming()

def neighborEdgeIDs(sumo_net, current_road_id):
    from_node = sumo_net.getEdge(current_road_id).getToNode()
    return [e.getID().encode('utf-8') for e in from_node.getIncoming()]

def getCurrentRoadInfo(sumo_net, veh_id):
    current_road_id = traci.vehicle.getRoadID(veh_id)
    current_road = sumo_net.getEdge(current_road_id)
    return current_road_id, current_road

def getReverseEdge(edge_id):
    if "-" in edge_id:
        return edge_id.replace("-", "")
    else:
        return "-" + edge_id

def isConnectToEdge(sumo_net, from_edge_id, from_lane_id, to_edge_id):
    from_edge = sumo_net.getEdge(from_edge_id)
    to_edge = sumo_net.getEdge(to_edge_id)
    connection_hash = from_edge.getOutgoing()
    for c in connection_hash[to_edge]:
        if c.getFromLane().getID() == from_lane_id:
            return True
    return False

def nodes2Route(nx_net, nodes):
    reroute = []
    for i in range(len(nodes) - 1):
        reroute.append(nx_net[nodes[i]][nodes[i+1]]['id'])
    return reroute

def searchRouteFromNode(sumo_net, nx_net, origin_node_id, dest_node_id):
    def distFromEdge(edge_A_id, edge_B_id):
        s = sumo_net.getEdge(edge_A_id).getToNode().getCoord()
        t = sumo_net.getEdge(edge_B_id).getToNode().getCoord()
        return ((s[0] - t[0]) ** 2 + (s[1] - t[1]) ** 2) ** 0.5

    new_route = []
    min_travel_time = float('inf')
    origin_node = sumo_net.getNode(origin_node_id)
    dest_node = sumo_net.getNode(dest_node_id)

    for origin_edge in origin_node.getOutgoing():
        for dest_edge in dest_node.getIncoming():
            origin_edge_id = origin_edge.getID().encode('utf-8')
            dest_edge_id = dest_edge.getID().encode('utf-8')
            if origin_edge_id == "-" + dest_edge_id or "-" + origin_edge_id == dest_edge_id:
                continue
            if not origin_edge_id in nx_net.nodes() or not dest_edge_id in nx_net.nodes():
                continue

            try:
                candidate = nx.astar_path(nx_net, origin_edge_id, dest_edge_id, distFromEdge)
                sum_travel_time = sum([freeFlowTravelTime(sumo_net, edge_id) for edge_id in candidate])
                if min_travel_time > sum_travel_time:
                    min_travel_time = sum_travel_time
                    new_route = candidate
            except nx.NetworkXNoPath:
                continue
    return new_route

def isRouteValid(route):
    for edge_id in route:
        if edge_id == route[-1]:
            break
        next_edge_id = route[route.index(edge_id) + 1]
        if edge_id == "-" + next_edge_id or "-" + edge_id == next_edge_id:
            return False
    return True
