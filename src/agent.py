from order import order
import numpy as np

class agent():
    def __init__(self, id, re_sources, own_demand_base, sell_price, sensitivity):
        self.id = id
        self.re_sources = re_sources
        self.own_demand_base = own_demand_base
        self.own_demand = own_demand_base
        self.sell_price = sell_price
        self.sensitivity = sensitivity
        self.funds = 0
        self.current_energy = 0
        
        
    def create_energy(self, daily_energy_level):
        self.current_energy = self.re_sources * daily_energy_level * 10


    def create_order(self):

        if self.current_energy > self.own_demand:
            tmp_amount = self.current_energy - self.own_demand
            return order(self.id, tmp_amount, self.sell_price, 'sell')
        elif self.current_energy < self.own_demand:
            tmp_amount = self.own_demand - self.current_energy
            return order(self.id, tmp_amount, self.sell_price, 'buy')
        
        return None
    
    def update(self, daily_energy_level, average_price):
        self.current_energy = 0
        self.create_energy(daily_energy_level)
        self.own_demand = self.own_demand_base + np.random.randint(-50, 50)

        if self.id != 0:

            self.sell_price = self.sensitivity * abs(self.current_energy - self.own_demand) + average_price + np.random.uniform(-0.1, 0.1)
        


    def set_own_enery(self, energy):
        self.current_energy = energy

'''
TODO:
- implement getters and setters
- implement house types and incorporate them in energy demand
    - set a range of possible base demands per house type
    - initiate agents based on housetype probabilities and then assign based demand
- improve sell price stuff
- determine parameter values (i.e. noise ranges, starting values, etc.)
'''