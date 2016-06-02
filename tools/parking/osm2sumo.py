# -*- coding: utf-8 -*-
import sys, os
from xml.etree.ElementTree import *


class parkingOSM:
    def removeDuplication(self, seq):
        seen = set()
        seen_add = seen.add
        return [x for x in seq if x not in seen and not seen_add(x)]

    def getNodeGeoLocationList(self, elem, node_list):
        node_geo_list = []
        nodes = elem.findall(".//node")

        for node in nodes:
            if len(node_geo_list) == len(node_list):
                break
            elif node.get("id") in node_list:
                node_location = {"lat": node.get("lat"), "lon": node.get("lon")}
                node_locations = {"id": node.get("id"), "geo": node_location}
                node_geo_list.append(node_locations)

        return node_geo_list

    def getCentralPoint(self, node_list):
        sum_lat = 0
        sum_lon = 0

        for node_dict in node_list:
            sum_lat += float(node_dict["geo"]["lat"])
            sum_lon += float(node_dict["geo"]["lon"])

        return {"lat": sum_lat / len(node_list), "lon": sum_lon / len(node_list)}

    def getParkingNodeLocation(self, elem):
        node_dicts = []
        ways = elem.findall(".//way")
        nodes = elem.findall(".//node")

        for way in ways:
            if not way.findall("tag") == []:
                tags = way.findall(".//tag")
                for tag in tags:
                    if tag.get("k") == "amenity" and tag.get("v") == "parking":
                        nds = way.findall(".//nd")
                        node_list = [nd.get("ref") for nd in nds]
                        node_list = self.removeDuplication(node_list)
                        node_geo_list = self.getNodeGeoLocationList(elem, node_list)
                        central_point = self.getCentralPoint(node_geo_list)
                        node_dict = {"position": central_point, "way": way.get("id")}
                        node_dicts.append(node_dict)
                        break

        for node in nodes:
            if not node.findall("tag") == []:
                tags = node.findall(".//tag")
                for tag in tags:
                    if tag.get("k") == "amenity" and tag.get("v") == "parking":
                        point = {"lat": node.get("lat"), "lon": node.get("lon")}
                        node_dict = {"position": point, "node": node.get("id")}
                        node_dicts.append(node_dict)
                        break

        return node_dicts

    def getParkingRelation(self, elem):
        relation_list = []
        relations = elem.findall(".//relation")

        for relation in relations:
            relation_dict = {}
            edges = []
            members = relation.findall(".//member")

            for member in members:
                if member.get("role") == "street":
                    relation_dict["street"] = member.get("ref")
                elif member.get("role") == "parking":
                    relation_dict["parking"] = member.get("ref")
                    if member.get("type") == "node":
                        relation_dict["type"] = "node"
                    elif member.get("type") == "way":
                        relation_dict["type"] = "way"
                elif member.get("role") == "node":
                    edges.append(member.get("ref"))

            if not relation_dict == {}:
                relation_dict["edge"] = edges
                relation_list.append(relation_dict)

        return relation_list

    def getParkingInformation(self, elem):
        parking_lots = []
        relation_list = self.getParkingRelation(elem)
        node_dicts = self.getParkingNodeLocation(elem)
        nodes = elem.findall(".//node")
        index = 0

        for relation in relation_list:
            edges = []
            parking_dict = {}
            index += 1

            for node_dict in node_dicts:
                if "way" in node_dict and relation["parking"] == node_dict["way"]:
                    node_dict["belonging"] = relation["street"]
                    node_dict["type"] = relation["type"]
                    node_dict["id"] = index
                    parking_dict = node_dict
                    break
                elif "node" in node_dict and relation["parking"] == node_dict["node"]:
                    node_dict["belonging"] = relation["street"]
                    node_dict["type"] = relation["type"]
                    node_dict["id"] = index
                    parking_dict = node_dict
                    break

            for node in nodes:
                if node.get("id") in relation["edge"]:
                    edges.append({"id": node.get("id"), "geo": {"lat": node.get("lat"), "lon": node.get("lon")}})

            parking_dict["edge"] = edges
            parking_lots.append(parking_dict)

        return parking_lots

    def calculateDistanceBetweenTwoPoints(self, a, b):
        return ((float(a["lat"]) - float(b["lat"]))**2 + (float(a["lon"]) - float(b["lon"]))**2)**0.5

    def getClosestContactPoint(self, parking, points): # x:lat, y:lon
        a = points[0]["geo"]
        b = points[1]["geo"]
        slope = (float(a["lon"]) - float(b["lon"])) / (float(a["lat"]) - float(b["lat"]))
        intercept = float(a["lon"]) - float(a["lat"]) * slope
        k = -(slope * float(parking["lat"]) + (-1) * float(parking["lon"]) + intercept) / (slope**2 + (-1)**2)
        x = float(parking["lat"]) + slope * k
        y = float(parking["lon"]) + (-1) * k

        return {"lat": x, "lon": y}

    def updateOSMfile(self, elem, tree, relation):
        ways = elem.findall(".//way")
        nodes = elem.findall(".//node")
        node_id = str(relation["id"])

        for way in ways:
            if way.get("id") == relation["belonging"]:
                nds = way.findall(".//nd")
                before_index = None
                for edge in relation["edge"]:
                    for nd_index, nd in enumerate(nds):
                        if nd.get("ref") == edge["id"]:
                            if before_index is None:
                                before_index = nd_index
                                break
                            else:
                                nd_tag = Element("nd")
                                nd_tag.set('ref', node_id)
                                parking_index = min(before_index, nd_index) + 1
                                way.insert(parking_index, nd_tag)
                                break
                break

        before_index = None
        for edge in relation["edge"]:
            for node_index, node in enumerate(nodes):
                if node.get("id") == edge["id"]:
                    if before_index is None:
                        before_index = nd_index
                        break
                    else:
                        node_tag = Element("node")
                        node_tag.set('user', "sho")
                        node_tag.set('id', node_id)
                        node_tag.set('visible', 'true')
                        node_tag.set('lat', str(relation["closest"]["lat"]))
                        node_tag.set('lon', str(relation["closest"]["lon"]))
                        node_tag.set('version', '1')
                        parking_tag = Element("tag")
                        parking_tag.set('k', 'amenity')
                        parking_tag.set('v', 'parking')
                        node_tag.append(parking_tag)
                        signal_tag = Element("tag")
                        signal_tag.set('k', 'highway')
                        signal_tag.set('v', 'traffic_signals')
                        node_tag.append(signal_tag)
                        parking_index = min(before_index, node_index) + 1
                        elem.insert(parking_index, node_tag)
                        break


class parkingSUMO:
    def removeTlLogic(self, elem, junction_id):
        tls = elem.findall(".//tlLogic")
        for tl in tls:
            if str(tl.get("id")) == str(junction_id):
                elem.remove(tl)
                return

    def removeTlsAttributeOfEdge(self, elem, junction_id):
        connections = elem.findall(".//connection")
        for connection in connections:
            if str(connection.get("tl")) == str(junction_id):
                del connection.attrib["tl"]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 " + sys.argv[0] + " <input OSM file> ")
        sys.exit()

    # add parking informarion to OSM file
    input_osm = str(sys.argv[1])
    park_osm = parkingOSM()
    osm_tree = parse(input_osm)
    osm_elem = osm_tree.getroot()

    parking_information = park_osm.getParkingInformation(osm_elem)

    for parking_dict in parking_information:
        contact_point = park_osm.getClosestContactPoint(parking_dict["position"], parking_dict["edge"])
        parking_dict["closest"] = contact_point
        park_osm.updateOSMfile(osm_elem, osm_tree, parking_dict)

    output_osm = "modified_" + input_osm
    osm_tree.write(output_osm, encoding="UTF-8", xml_declaration=True)

    # convert OSM file into SUMO file and modify SUMO netowrk file
    sumo_file = input_osm.replace('.osm', '.net.xml')
    os.system("netconvert --osm " + output_osm + " -o " + sumo_file + " --no-turnarounds --no-internal-links")
    park_sumo = parkingSUMO()
    sumo_tree = parse(sumo_file)
    sumo_elem = sumo_tree.getroot()

    for parking_dict in parking_information:
        park_sumo.removeTlLogic(sumo_elem, parking_dict["id"])
        park_sumo.removeTlsAttributeOfEdge(sumo_elem, parking_dict["id"])

    sumo_tree.write(sumo_file, encoding="UTF-8", xml_declaration=True)
    print(sumo_file + " is created.")
    os.system("rm " + output_osm)
