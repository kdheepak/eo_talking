# -*- coding: utf-8 -*-
import helics as h
import json
import time
from HelicsAgent import HelicsAgent
from constants import (
    START_TIME,
    END_TIME,
    TIMESTEP,
    MARKET_SOLVE_TIME,
    HOME_UPDATE_FREQ,
    MARKET_SOLVE_FREQ,
    DEC_TOLERANCE,
    fedinitstring,
)
import numpy as np


class House(HelicsAgent):

    def __init__(
        self,
        house_id,
        node_id,
        fed_name,
        message_interval=TIMESTEP,
        fedinitstring=fedinitstring,
    ):
        self.id = house_id
        self.node_id = node_id
        super().__init__(fed_name, message_interval, fedinitstring)
        self.talk_topic = "home_to_contoller_{}".format(node_id)
        self.listen_topic = "controller_to_home_{}".format(node_id)
        self.register_publication(self.talk_topic, self.talk_topic, "String")
        self.register_subcription(self.listen_topic, self.listen_topic)
        self.start_execution()
        self.approved_controls = {}

    def update_controller(self, value):
        self.publish(self.talk_topic, json.dumps(value))

    def recieve_controls(self):
        value = self.fetch_subscription(self.listen_topic)
        if value is not None:
            self.approved_controls.update(value)


def main():
    home_id = "1"
    node_id = "7954"
    fed_name = "House_7954"

    house = House(home_id, node_id, fed_name)

    for i in np.arange(START_TIME, END_TIME, TIMESTEP):
        i = round(i, DEC_TOLERANCE)
        stepped = False

        if i % HOME_UPDATE_FREQ == 0:
            house.stepTo(i)
            stepped = True
            house.update_controller({"kwh": i})

        t = round(i - (MARKET_SOLVE_TIME + 3 * TIMESTEP), DEC_TOLERANCE)
        if t > 0:
            if t % MARKET_SOLVE_FREQ == 0 and t % 60 != 0:
                if not stepped:
                    house.stepTo(i)
                house.recieve_controls()

    print(house.approved_controls)
    house.finalize()
    house.close()


main()
