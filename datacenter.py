# -*- coding: utf-8 -*-
import traci

class DataCenter:
    class VehicleInfo:
        def __init__(self, allowable_range, park_time):
            self.park_time = park_time
            self.allowable_range = allowable_range
            self.parking_id = None
            self.has_parked = False
            self.has_negotiated = False
            self.allowable_parking_lots = {}
            self.tried_parking_lots = []

    def __init__(self):
        self.vehicles_info = {}

    def setVehicle(self, veh_id, allowable_range, park_time):
        vehicle_info = DataCenter.VehicleInfo(allowable_range, park_time)
        self.vehicles_info[veh_id] = vehicle_info

    def getParkTime(self, veh_id):
        return self.vehicles_info[veh_id].park_time

    def getAllowableRange(self, veh_id):
        return self.vehicles_info[veh_id].allowable_range

    def getParkingID(self, veh_id):
        return self.vehicles_info[veh_id].parking_id

    def setParkingID(self, veh_id, reset_parking_id):
        self.vehicles_info[veh_id].parking_id = reset_parking_id

    def hasParked(self, veh_id):
        return self.vehicles_info[veh_id].has_parked

    def parkVehicle(self, veh_id):
        self.vehicles_info[veh_id].has_parked = True

    def hasNegotiated(self, veh_id):
        return self.vehicles_info[veh_id].has_negotiated

    def negotiateVehicle(self, veh_id):
        self.vehicles_info[veh_id].has_negotiated = True

    def getAllowableParkingLots(self, veh_id, sorted=True, remove_dest=True):
        vehicle_info = self.vehicles_info[veh_id]
        allowable_list = vehicle_info.allowable_parking_lots

        if remove_dest == True and vehicle_info.parking_id in allowable_list:
            del allowable_list[vehicle_info.parking_id]
        if sorted == True:
            allowable_list = self.sortByDistance(allowable_list)

        return [parking_lot[0] for parking_lot in allowable_list]

    def setAllowableParkingLot(self, veh_id, parking_lot_id, dist):
        self.vehicles_info[veh_id].allowable_parking_lots[parking_lot_id] = dist

    def sortByDistance(self, allowable_list):
        return sorted(allowable_list.items(), key=lambda x: x[1])

    def getTriedParkingLots(self, veh_id):
        return self.vehicles_info[veh_id].tried_parking_lots

    def hasTriedPark(self, veh_id, parking_id):
        return parking_id in self.vehicles_info[veh_id].tried_parking_lots

    def tryPark(self, veh_id, parking_id):
        self.vehicles_info[veh_id].tried_parking_lots.append(parking_id)

    # def getRequestedVehicle(self, parking_id):
    #     requested_vehicles = []
    #     for veh_id in traci.vehicle.getIDList():
    #         if self.hasParked(veh_id) == True or self.getParkingID(veh_id) == parking_id:
    #             continue
    #         else:
    #             requested_vehicles.append(veh_id)
    #     return requested_vehicles

    # def shouldNegotiate(self, parking_id, parking_space, requested_vehicles):
    #     requested_vehicles = self.getRequestedVehicle(parking_id)
    #     return parking_space < len(requested_vehicles)
