# -*- coding: utf-8 -*-
import subprocess, sys, os, time, constants, optparse, config
import traci
import networkx as nx
import networkutility as netutil
from sumolib import checkBinary
from sumolib import net


class Simulator:
    def __init__(self):
        self.conf = config.Config()
        self.conf.readConfig(constants.CONFIG_FILE)
        self._options = self.__getOptions__()
        self.sumo_net = net.readNet(self.conf.network_file)
        self.original_network = nx.DiGraph()

        # check output directory
        if os.path.isdir(self.conf.output_dir) == False:
            print("there is not output directory...")
            os.mkdir(self.conf.output_dir)
            print("create output directory.")
    
        if self.conf.real_net == True:
            netutil.readRealNetwork(self.sumo_net, self.original_network)
        else:
            netutil.readNetwork(self.sumo_net, self.original_network)

    def __getOptions__(self):
        self.optParser = optparse.OptionParser()
        self.optParser.add_option(
            "--gui",
            action = "store_true",
            default = False,
            help = "run sumo with gui")

        self.optParser.add_option(
            "--port",
            type = "int",
            default = self.conf.port,
            help = "run sumo with port")
        options, args = self.optParser.parse_args()
        return options

    def run(self, offset):
        self.__inner_run__(self.conf.output_dir + "/" + offset + ".xml")
        self.__sumoProcess.wait()

    def __inner_run__(self, output_file):
        if self._options.gui:
            sumoBinary = checkBinary('sumo-gui')
            self.__sumoProcess = subprocess.Popen(
                [sumoBinary,"-W",
                "-n", self.conf.network_file,
                "-r", self.conf.route_file,
                "--tripinfo-output", output_file,
                "--remote-port", str(self.conf.port),
                "--gui-settings-file", self.conf.gui_setting_file,
                "--step-length", "1",
                "-v", "true",
                "--time-to-teleport", "-1"],
                stdout = sys.stdout, stderr=sys.stderr)
            time.sleep(20)

        else:
            sumoBinary = checkBinary('sumo')
            self.__sumoProcess = subprocess.Popen(
                [sumoBinary, "-W",
                "-n", self.conf.network_file,
                "-r", self.conf.route_file,
                "--tripinfo-output", output_file,
                "--remote-port", str(self.conf.port),
                "--step-length", "1",
                "-v", "true",
                "--time-to-teleport", "-1"],
                stdout = sys.stdout, stderr=sys.stderr)
            time.sleep(20)

        traci.init(self.conf.port)
        self.initIteration()

        while True:
            traci.simulationStep()

            if traci.simulation.getMinExpectedNumber() <= 0:
                break

            self.stepProcess()

            if traci.simulation.getCurrentTime() % self.conf.short_term_sec == 0:
                self.can_change_lane_list = []
                self.want_chage_vehicle_list = []

        self.endIteration()
        traci.close()

        if self._options.gui:
            os.system('pkill sumo-gui')
        sys.stdout.flush()

    def initIteration(self):
        pass

    def stepProcess(self):
        pass

    def endIteration(self):
        pass


if __name__ == "__main__":
    sim = Simulator()
    sim.run("Simulation")
