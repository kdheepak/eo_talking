import helics as h
import json
import time
from HelicsAgent import HelicsAgent
from constants import START_TIME,END_TIME,TIMESTEP,MARKET_SOLVE_TIME,MARKET_SOLVE_FREQ,HOME_UPDATE_FREQ,DEC_TOLERANCE,fedinitstring
import numpy as np

class Controller(HelicsAgent):
    def __init__(self,controller_id, node_id, fed_name,message_interval=TIMESTEP,fedinitstring=fedinitstring):
        super().__init__(fed_name,message_interval,fedinitstring)
        self.id = controller_id
        self.node_id = node_id
        self.talk_to_home_topic = "controller_to_home_{}".format(node_id)
        self.talk_to_eo_topic = "controller_to_eo_{}".format(node_id)
        self.listen_to_home_topic = "home_to_contoller_{}".format(node_id)
        self.listen_to_eo_topic = "energy_orders"
        self.register_publication(self.talk_to_home_topic, self.talk_to_home_topic ,"String")
        self.register_publication(self.talk_to_eo_topic, self.talk_to_eo_topic ,"String")
        self.register_subcription(self.listen_to_home_topic, self.listen_to_home_topic)
        self.register_subcription(self.listen_to_eo_topic, self.listen_to_eo_topic)
        self.start_execution()
        self.home_energy_readings = {}
        self.approved_schedules = {}
        

    def send_bids_to_energy_orders(self):
        period_start = int(round(self.current_time/60.0)*60+60)
        upcoming_schedule = {self.node_id:{k:[self.current_time,-0.04] for k in range(period_start,period_start+ 120,60)}}
        self.publish(self.talk_to_eo_topic,json.dumps(upcoming_schedule))

    def send_controls_to_home(self,message):
        self.publish(self.talk_to_home_topic,json.dumps(self.approved_schedules))    

    def listen_to_home(self):
        self.home_energy_readings[self.current_time] = self.fetch_subscription(self.listen_to_home_topic)

    def fetch_approved_orders(self):
        approved_energy_orders = self.fetch_subscription(self.listen_to_eo_topic)
        if approved_energy_orders is not None:
            for o in approved_energy_orders.items():
                hour, orders = o
                if self.node_id in orders.keys():
                    self.approved_schedules[hour] = orders[self.node_id]
                    
def main():
    
    controller_id = "1"
    node_id = "7954"
    fed_name = "Controller_7954"
    
    "#BROKER"
    
    controller = Controller(controller_id,node_id,fed_name)
    
    for i in np.arange(START_TIME,END_TIME,TIMESTEP):
        stepped = False
        i = round(i,DEC_TOLERANCE)
        if (i - TIMESTEP)%HOME_UPDATE_FREQ==0:
            controller.stepTo(i)
            stepped = True
            controller.listen_to_home()
            controller.send_bids_to_energy_orders()
        
        t = round(i- (MARKET_SOLVE_TIME + TIMESTEP*2),DEC_TOLERANCE)
        if t > 0 and t%MARKET_SOLVE_FREQ==0 and t%60 != 0:
            if not stepped:
                controller.stepTo(i)
            controller.fetch_approved_orders()
            controller.send_controls_to_home(i)
    
    print(controller.approved_schedules)
    print(controller.home_energy_readings)
    controller.finalize()
    controller.close()

main()