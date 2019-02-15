import helics as h
import json
import time
import random

class HelicsAgent:
    def __init__(self, fed_name,message_interval,fedinitstring):
        time.sleep(random.random() * 0.25)
        self.fed = None
        self.fed_name = fed_name
        self.current_time = 0.0
        self.publications = {}
        self.subscriptions = {}
        self.step_increment = message_interval
        self.create_federate(fedinitstring,message_interval)

    def create_federate(self, fedinitstring, message_interval,type="value"):
        fedinfo = h.helicsCreateFederateInfo()
        status = h.helicsFederateInfoSetCoreName(fedinfo, self.fed_name)
        status = h.helicsFederateInfoSetCoreTypeFromString(fedinfo, "zmq")
        status = h.helicsFederateInfoSetCoreInitString(fedinfo, fedinitstring)
        status = h.helicsFederateInfoSetTimeProperty(fedinfo, h.helics_property_time_delta, message_interval)
        self.fed = h.helicsCreateValueFederate(self.fed_name, fedinfo)
        print("{} federate created".format(self.fed_name))

    def register_subcription(self, name, topic, optional=False):
        if optional:
            sub = h.helicsFederateRegisterOptionalSubscription(self.fed, topic, "")
        else:
            sub = h.helicsFederateRegisterSubscription(self.fed, topic, "")
        self.subscriptions[name] = { "obj":sub }

    def register_publication(self, name, topic, data_type, global_pub=True):
        if global_pub:
            pub = h.helicsFederateRegisterGlobalTypePublication(self.fed, topic, data_type, "")
        else:
            pub = h.helicsFederateRegisterPublication(self.fed, topic, data_type, "")
        self.publications[name] = {"type":data_type, "obj":pub }

    def start_execution(self):
        status = h.helicsFederateEnterExecutingMode(self.fed)

    def stepTo(self, timestep):
        while self.current_time < timestep:
            self.current_time = h.helicsFederateRequestTime(self.fed, timestep)
        print("TIMESTEP {}".format(self.current_time))
        return self.current_time

    def publish(self,name, value):
         h.helicsPublicationPublishString(self.publications[name]['obj'], value)
         print("{} Sent value = {} at time {} from subscription {}".format(self.fed_name, value, self.current_time, name))

    def fetch_subscription(self, name):
        value = h.helicsInputGetString(self.subscriptions[name]['obj'])
        print("{} Received value = {} at time {} from subscription {}".format(self.fed_name, value, self.current_time, name))
        try:
            value = json.loads(value)
            if value == 0.0:
                value = None
        except:
            value = None
        return value

    def fetch_subscriptions(self,skip=[]):
        result = {}
        for name, sub in self.subscriptions.items():
            if name not in skip:
                value = h.helicsInputGetString(self.subscriptions[name]['obj'])
                try:
                    value = json.loads(value)
                    if value == 0.0:
                        value = None
                except:
                    value = None
                print("{} Received value = {} at time {} from subscription {}".format(self.fed_name, value, self.current_time, name))
                result[name] = value
        return result
    def finalize(self):
        h.helicsFederateFinalize(self.fed)

    def close(self):
        h.helicsFederateFree(self.fed)
        h.helicsCloseLibrary()
        print("{} Federate finalized".format(self.fed_name))
