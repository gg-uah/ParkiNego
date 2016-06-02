# -*- coding: utf-8 -*-
import traci

class ParkingLot:
    def __init__(self, id, capasity, price):
        self.id = id
        self.capasity = capasity
        self.price = price
        self.space = capasity
        self.vehicles = {}
        self.wait_vehicles = {}
        self.start_vehicles = {}

    def getID(self):
        return self.id

    def getSpace(self):
        return self.space

    def getMaxCapasity(self):
        return self.capasity

    def getPrice(self):
        return self.price

    def getVehicles(self):
        return self.vehicles

    def getParkingNumber(self):
        return len(self.vehicles)

    def getWaitingNumber(self):
        return len(self.wait_vehicles)

    def getStartingNumber(self):
        return len(self.start_vehicles)

    def existVehicle(self, veh_id):
        return veh_id in self.vehicles

    def existWaitingVehicle(self, veh_id):
        return veh_id in self.wait_vehicles

    def existStartingVehicle(self, veh_id):
        return veh_id in self.start_vehicles

    def clearWaitingVehicles(self):
        self.wait_vehicles.clear()

    def clearStartingVehicles(self):
        self.start_vehicles.clear()

    def addWaitingVehicle(self, veh_id, position):
        self.wait_vehicles[veh_id] = position

    def resumeWaitingVehicle(self, veh_id):
        del self.wait_vehicles[veh_id]

    def startParkingVehicle(self, veh_id, edge_id, position, parking_position, lane_index, time):
        self.start_vehicles[veh_id] = {"position": position, "park": parking_position, "time": time}
        traci.vehicle.setStop(veh_id, edge_id, parking_position, lane_index, time, 1)

    def letVehicleArrive(self, veh_id):
        del self.start_vehicles[veh_id]
        if veh_id in self.wait_vehicles:
            del self.wait_vehicles[veh_id]
        self.space -= 1
        print("park :" + str(veh_id))

    def parkVehicle(self, veh_id, time):
        self.vehicles[veh_id] = {"depart": time, "time": 0}

    def unparkVehicle(self, veh_id):
        del self.vehicles[veh_id]
        self.space += 1

    def updateState(self):
        if self.getParkingNumber() == 0:
            return
        for veh_id, vehicle in self.vehicles.items():
            vehicle["time"] += 1
        for wait_vehicle_id in self.wait_vehicles.keys():
            position = traci.vehicle.getLanePosition(wait_vehicle_id)
            self.wait_vehicles[wait_vehicle_id] = position
        for start_veh_id in self.start_vehicles:
            position = traci.vehicle.getLanePosition(start_veh_id)
            self.start_vehicles[start_veh_id]["position"] = position

    def getUnparkList(self):
        unpark_list = []
        for veh_id, vehicle in self.vehicles.items():
            if vehicle["time"] == int(vehicle["depart"]) / 1000:
                print("unpark :" + str(veh_id))
                self.unparkVehicle(veh_id)
                unpark_list.append(veh_id)
        return unpark_list

    def getHeadWaitVehicle(self):
        sort_wait = sorted(self.wait_vehicles.items(), key=lambda x:x[1], reverse=True)
        for head_id, head_value in sort_wait:
            return head_id

    def updateArrival(self):
        for start_veh_id, start_veh_dict in self.start_vehicles.items():
            if start_veh_id in traci.vehicle.getIDList():
                continue
            print("arrive: " + str(start_veh_id))
            if start_veh_id in self.wait_vehicles:
                self.resumeWaitingVehicle(start_veh_id)
            self.letVehicleArrive(start_veh_id)
            self.parkVehicle(start_veh_id, start_veh_dict["time"])
