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
    HOME_UPDATE_FREQ,
    DEC_TOLERANCE,
    fedinitstring,
)
import numpy as np


class EnergyOrders(HelicsAgent):

    def __init__(
        self, fed_name, message_interval=TIMESTEP, fedinitstring=fedinitstring
    ):
        super().__init__(fed_name, message_interval, fedinitstring)
        self.talk_to_controllers_topic = "energy_orders"
        self.talk_to_market_topic = "eo_to_market"
        self.listen_topics = "controller_to_eo_2704;controller_to_eo_7954"
        self.listen_to_market_topic = "market_to_eo"
        self.register_publication(
            self.talk_to_controllers_topic, self.talk_to_controllers_topic, "String"
        )
        self.register_publication(
            self.talk_to_market_topic, self.talk_to_market_topic, "String"
        )
        for listen_topic in self.listen_topics.split(";"):
            self.register_subcription(listen_topic, listen_topic)
        self.register_subcription(
            self.listen_to_market_topic, self.listen_to_market_topic
        )
        self.start_execution()
        self.offers = {}
        self.completed_orders = {}

    def addressIsValid(self, address):
        return True

    def get_most_recent_bids(self):

        new_messages = self.fetch_subscriptions(skip=[self.listen_to_market_topic])
        for pair in new_messages.items():
            k, v = pair
            if v is not None:
                self.parse_bid(v)

    def parse_bid(self, v):
        for bid in v.items():
            key, schedule = bid
            if self.addressIsValid(key):
                for hour, energy_and_price in schedule.items():
                    if hour not in self.offers.keys():
                        self.offers[hour] = {}
                    self.offers[hour][key] = energy_and_price

    def publish_approved_to_controllers(self):
        self.publish(
            self.talk_to_controllers_topic,
            "{}".format(json.dumps(self.completed_orders)),
        )

    def publish_offers_to_market(self):
        self.publish(self.talk_to_market_topic, "{}".format(json.dumps(self.offers)))

    def update_from_market(self):
        v = self.fetch_subscription(self.listen_to_market_topic)
        if v is not None:
            for hour_data in v.items():
                hour, schedule = hour_data
                if hour not in self.completed_orders.keys():
                    self.completed_orders[hour] = {}
                self.completed_orders[hour].update(schedule)


def main():

    fed_name = "eo"

    eo = EnergyOrders(fed_name)

    for i in np.arange(START_TIME, END_TIME, TIMESTEP):
        stepped = False
        i = round(i, DEC_TOLERANCE)
        if (i - (TIMESTEP * 2)) % HOME_UPDATE_FREQ == 0:
            eo.stepTo(i)
            eo.get_most_recent_bids()

        if i % MARKET_SOLVE_FREQ == 0:
            if not stepped:
                eo.stepTo(i)
                stepped = True
            eo.publish_offers_to_market()

        if (i - (MARKET_SOLVE_TIME + 0.1)) % MARKET_SOLVE_FREQ == 0:
            if not stepped:
                eo.stepTo(i)
            eo.update_from_market()
            eo.publish_approved_to_controllers()

    eo.finalize()
    eo.close()


main()
