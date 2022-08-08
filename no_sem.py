import os
import sys

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare the environment variable 'SUMO_HOME'")
import traci
import numpy as np
from gym import spaces
import time
import math


class TrafficSignal:
    """
    This class represents a Traffic Signal of an intersection
    It is responsible for retrieving information and changing the traffic phase using Traci API

    IMPORTANT: It assumes that the traffic phases defined in the .net file are of the form:
        [green_phase, yellow_phase, green_phase, yellow_phase, ...]
    Currently it is not supporting all-red phases (but should be easy to implement it).

    Default observation space is a vector R^(#greenPhases + 2 * #lanes)
    s = [current phase one-hot encoded, density for each lane, queue for each lane]
    You can change this by modifing self.observation_space and the method _compute_observations()

    Action space is which green phase is going to be open for the next delta_time seconds
    """

    def __init__(self, env, ts_id, delta_time, yellow_time, min_green, max_green, begin_time, sumo):
        self.id = ts_id
        self.env = env
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        self.green_phase = 0
        self.is_yellow = False
        self.time_since_last_phase_change = 0
        self.next_action_time = begin_time
        self.last_measure = 0.0
        self.last_reward = None
        self.sumo = sumo
        self.global_last_measure = 0.0
        self.total_emergency_breaks = 0
        self.last_avg_speed = 0
        self.vehicles=[]

        #self.build_phases()

        '''lista di tutte le lanes presenti nella rete'''
        self.all_lanes = self.get_all_lanes()
        #self.lanes=lanes_sem

        self.lanes = list(
            dict.fromkeys(self.sumo.trafficlight.getControlledLanes(self.id)))  # Remove duplicates and keep order
        
        self.out_lanes = [link[0][1] for link in self.sumo.trafficlight.getControlledLinks(self.id) if link]
        self.out_lanes = list(set(self.out_lanes))

        self.lanes_lenght = {lane: self.sumo.lane.getLength(lane) for lane in self.lanes}

        self.position = self.sumo.junction.getPosition(junctionID=self.id)
        self.actions = None
        self.stopped = []
        self.build_actions()
        self.num_green_phases=len(self.actions)
        self.nonSTop=[]
        self.edges = self.get_edges()
        self.action_actual=None
        '''
        self.observation_space = spaces.Box(
            low=np.zeros(len(self.actions)+ 2 * len(self.lanes), dtype=np.float32),
            high=np.ones(len(self.actions)+2 * len(self.lanes), dtype=np.float32))
        self.discrete_observation_space = spaces.Tuple((
            spaces.Discrete(len(self.actions)),  # Binary variable active if min_green seconds already elapsed
            *(spaces.Discrete(10) for _ in range(2 * len(self.lanes)))  # Density and stopped-density for each lane
        ))
        '''
        self.observation_space = spaces.Box(
            low=np.zeros( 2 * len(self.lanes), dtype=np.float32),
            high=np.ones( 2 * len(self.lanes), dtype=np.float32))
        self.discrete_observation_space = spaces.Tuple((
            (spaces.Discrete(10) for _ in range(2 * len(self.lanes)))  # Density and stopped-density for each lane
        ))

        self.action_space = spaces.Discrete(len(self.actions))

    def get_all_lanes(self):
        lanes = []
        for id in self.sumo.trafficlight.getIDList():
            for lane in self.sumo.trafficlight.getControlledLanes(id):
                if lane not in lanes: lanes.append(lane)
        return lanes

    def build_actions(self):

        self.actions = [(1, 0, 0, 0, 1, 0, 0, 0),(0, 1, 0, 0, 0, 1, 0, 0),(0, 0, 1, 0, 0, 0, 1, 0),(0, 0, 0, 1, 0, 0, 0, 1)]



    @property
    def time_to_act(self):
        return self.next_action_time == self.env.sim_step

    def update(self):
        self.time_since_last_phase_change += 1


    def get_edges(self):
        edges = []
        for lane in self.lanes:
            edges.append(self.sumo.lane.getEdgeID(lane))
        return edges

    def current_edge(self, vehicle):
        lane = self.sumo.vehicle.getLaneID(vehicle)
        edge = self.sumo.lane.getEdgeID(lane)

        return edge

    def get_distance(self,veh_id):

        if veh_id:
            veh_pos = traci.vehicle.getPosition(veh_id)
            x = math.pow(self.position[0] - veh_pos[0], 2)
            y = math.pow(self.position[1] - veh_pos[1], 2)

            return math.sqrt(x + y)
        else:
            return 250

    def get_first_vehicles(self):
        first = [None]*8
        i = 0
        for i in range(8):
            vehicles = list(traci.lane.getLastStepVehicleIDs(laneID=self.lanes[i]))
            if len(vehicles) != 0:
                first[i] = (vehicles[len(vehicles) - 1])
                i+=1
        return first

    def set_next_phase(self, action):
        """
        Sets what will be the next green phase and sets yellow phase if the next phase is different than the current

        :param new_phase: (int) Number between [0..num_green_phases]
        """
        first_veh = self.get_first_vehicles()
        act=self.actions[action]



        for i in range(8):

            if first_veh[i] is not None and (act[i] == 0 and
                                             (first_veh[i] not in self.stopped and
                                              (self.get_distance(first_veh[i]) <=20 and( self.get_distance(first_veh[i])>10
                                                and first_veh[i] not in self.nonSTop)))):
                self.sumo.vehicle.setDecel(decel=100, vehID=first_veh[i])
                self.sumo.vehicle.setSpeed(vehID=first_veh[i], speed=0)
                self.stopped.append(first_veh[i])
            else:
                if first_veh[i] in self.stopped and act[i]==1:
                    self.nonSTop.append(first_veh[i])
                    self.sumo.vehicle.setSpeed(first_veh[i], speed=13)
                    self.sumo.vehicle.setDecel(first_veh[i], decel=4.5)
                    self.stopped.remove(first_veh[i])







        if self.action_actual != action:
            self.next_action_time = self.env.sim_step + self.delta_time
            self.green_phase=action
            self.is_yellow = True
            self.time_since_last_phase_change = 0
        if self.sumo.simulation.getTime()%200==0 and self.sumo.simulation.getTime()!=0:
            self.nonSTop=self.nonSTop[int(len(self.nonSTop)/2):]

        else:
            self.next_action_time = self.env.sim_step + self.delta_time




    def compute_observation(self):
        #phase=[1 if self.action_actual == i else 0 for i in range(len(self.actions))]
        #phase_id = [1 if self.green_phase == i else 0 for i in range(self.num_green_phases)]  # one-hot encoding
        #min_green = [0 if self.time_since_last_phase_change < self.min_green + self.yellow_time else 1]
        density = self.get_lanes_density()
        queue = self.get_lanes_queue()
        observation = np.array(density + queue, dtype=np.float32)
        return observation

    def compute_reward(self, d):
        if d == 0:
            # self.last_reward = self._waiting_time_reward() # self._average_speed_reward()'''
            self.last_reward = self.custom_reward2()

        else:
            self.last_reward = self._queue_reward()
        return self.last_reward

    def custom_reward(self):

        speed = self._waiting_time_reward() * 0.50
        queue = self._queue_reward() * 0.50
        reward = speed + queue
        return reward
    def get_collision_reward(self):
        count=0
        if self.sumo.simulation.getCollisions():
            for veh in self.sumo.simulation.getCollidingVehiclesIDList():
                if self.get_distance(veh) < 30:
                    print(self.id)
                    count+=1
        return count/2
    def custom_reward2(self):
        #print(self.lanes)
        '''
        if self.sumo.simulation.getCollisions():
            for veh in self.sumo.simulation.getCollidingVehiclesIDList():
                if veh in self.vehicles:
                    print(self.id)
        '''

            #lane=str(self.sumo.simulation.getCollisions()).split("collider")
            #lane=lane[7].split("collider")[1]
            #print(traci.simulation.getCollidingVehiclesIDList())
        #sem_breaks = self.get_emergency_breaks()
        # speed=self._avg_speed_2()*0.15
        wait = self._waiting_time_reward()*80
        queue = self._queue_reward() * 0.15
        global_wait=self._global_waiting_time_reward()*0.05
        # reward=wait+queue+global_wait-em_breaks
        reward = wait+queue-global_wait
        return reward

    def _pressure_reward(self):
        return -self.get_pressure()

    def _avg_speed_2(self):
        avg_speed = self.get_average_speed()
        if avg_speed == 0:
            avg_speed = -1
        return avg_speed

    def _average_speed_reward(self):
        return self.get_average_speed()

    def _queue_average_reward(self):
        new_average = np.mean(self.get_lanes_queue())
        reward = self.last_measure - new_average
        self.last_measure = new_average
        return reward

    def _queue_reward(self):
        return - (sum(self.get_lanes_queue())) ** 2

    def _waiting_time_reward(self):
        ts_wait = sum(self.get_waiting_time_per_lane()) / 100.0
        reward = self.last_measure - ts_wait
        self.last_measure = ts_wait
        return reward

    def _waiting_time_reward2(self):
        ts_wait = sum(self.get_waiting_time_per_lane())
        self.last_measure = ts_wait
        if ts_wait == 0:
            reward = 1.0
        else:
            reward = 1.0 / ts_wait
        return reward

    def _global_waiting_time_reward(self):
        ts_wait = sum(self.get_waiting_time_all_lane()) / 100.0
        reward = self.global_last_measure - ts_wait
        self.global_last_measure = ts_wait
        return reward

    def _waiting_time_reward3(self):
        ts_wait = sum(self.get_waiting_time_per_lane())
        reward = -ts_wait
        self.last_measure = ts_wait
        return reward

    def get_emergency_breaks(self):
        count = 0
        for car in self.sumo.simulation.getEmergencyStoppingVehiclesIDList():
            if self.sumo.vehicle.getLaneID(car) in self.lanes:
                count += 1
        if count != 0:
            self.total_emergency_breaks += count
        return count

    def get_waiting_time_per_lane(self):
        wait_time_per_lane = []

        for lane in self.lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            wait_time = 0.0
            for veh in veh_list:
                veh_lane = self.sumo.vehicle.getLaneID(veh)
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                if veh not in self.env.vehicles:
                    self.env.vehicles[veh] = {veh_lane: acc}
                else:
                    self.env.vehicles[veh][veh_lane] = acc - sum(
                        [self.env.vehicles[veh][lane] for lane in self.env.vehicles[veh].keys() if lane != veh_lane])
                wait_time += self.env.vehicles[veh][veh_lane]
            wait_time_per_lane.append(wait_time)
        return wait_time_per_lane

    def get_waiting_time_all_lane(self):
        wait_time_per_lane = []
        for lane in self.all_lanes:
            veh_list = self.sumo.lane.getLastStepVehicleIDs(lane)
            wait_time = 0.0
            for veh in veh_list:
                veh_lane = self.sumo.vehicle.getLaneID(veh)
                acc = self.sumo.vehicle.getAccumulatedWaitingTime(veh)
                if veh not in self.env.vehicles:
                    self.env.vehicles[veh] = {veh_lane: acc}
                else:
                    self.env.vehicles[veh][veh_lane] = acc - sum(
                        [self.env.vehicles[veh][lane] for lane in self.env.vehicles[veh].keys() if lane != veh_lane])
                wait_time += self.env.vehicles[veh][veh_lane]
            wait_time_per_lane.append(wait_time)
        return wait_time_per_lane

    def get_average_speed(self):
        avg_speed = 0.0
        vehs = self._get_veh_list()
        if len(vehs) != 0:
            for v in vehs:
                avg_speed += self.sumo.vehicle.getSpeed(v) / self.sumo.vehicle.getAllowedSpeed(v)

            return avg_speed / len(vehs)
        else:
            return 0

    def get_pressure(self):
        return abs(sum(self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.lanes) - sum(
            self.sumo.lane.getLastStepVehicleNumber(lane) for lane in self.out_lanes))

    def get_out_lanes_density(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        return [min(1, self.sumo.lane.getLastStepVehicleNumber(lane) / (
                    self.sumo.lane.getLength(lane) / vehicle_size_min_gap)) for lane in self.out_lanes]

    def get_lanes_density(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        return [min(1, self.sumo.lane.getLastStepVehicleNumber(lane) / (self.lanes_lenght[lane] / vehicle_size_min_gap))
                for lane in self.lanes]

    def get_lanes_queue(self):
        vehicle_size_min_gap = 7.5  # 5(vehSize) + 2.5(minGap)
        return [min(1, self.sumo.lane.getLastStepHaltingNumber(lane) / (self.lanes_lenght[lane] / vehicle_size_min_gap))
                for lane in self.lanes]

    def get_total_queued(self):
        return sum([self.sumo.lane.getLastStepHaltingNumber(lane) for lane in self.lanes])

    def _get_veh_list(self):
        veh_list = []
        for lane in self.lanes:
            veh_list += self.sumo.lane.getLastStepVehicleIDs(lane)
        return veh_list
