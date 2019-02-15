# -*- coding: utf-8 -*-
import helics as h
import json
from HelicsAgent import HelicsAgent
from constants import (
    START_TIME,
    END_TIME,
    TIMESTEP,
    MARKET_SOLVE_TIME,
    MARKET_SOLVE_FREQ,
    DEC_TOLERANCE,
    fedinitstring,
)
import numpy as np
import time


class Market(HelicsAgent):

    def __init__(
        self, fed_name, message_interval=TIMESTEP, fedinitstring=fedinitstring
    ):
        super().__init__(fed_name, message_interval, fedinitstring)
        self.talk_to_energy_orders_topic = "market_to_eo"
        self.listen_to_energy_orders_topic = "eo_to_market"
        self.approved_bids = {}
        self.register_publication(
            self.talk_to_energy_orders_topic, self.talk_to_energy_orders_topic, "String"
        )
        self.register_subcription(
            self.listen_to_energy_orders_topic, self.listen_to_energy_orders_topic
        )
        self.start_execution()

    def settle_bids(self):
        value = self.fetch_subscription(self.listen_to_energy_orders_topic)
        if value is not None:
            for hour_data in value.items():
                hour, schedule = hour_data
                for bid in schedule.items():
                    address, bid_data = bid
                    bid_data.append({"market_sig": "abc123"})
        self.approved_bids = value

    def publish_approved(self):
        self.publish(self.talk_to_energy_orders_topic, json.dumps(self.approved_bids))


def main():

    fed_name = "market"

    market = Market(fed_name)

    time.sleep(1)

    for i in np.arange(START_TIME, END_TIME, TIMESTEP):
        i = round(i, DEC_TOLERANCE)
        stepped = False

        if (i - TIMESTEP) % MARKET_SOLVE_FREQ == 0:
            market.stepTo(i)
            market.settle_bids()

        if (i - MARKET_SOLVE_TIME) % MARKET_SOLVE_FREQ == 0:
            if not stepped:
                market.stepTo(i)
            market.publish_approved()

    market.finalize()
    market.close()


main()
