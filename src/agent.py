from order import order
import numpy as np

class agent():
    def __init__(self, id, re_sources, own_demand, sell_price):
        self.id = id
        self.re_sources = re_sources
        self.own_demand = own_demand
        self.sell_price = sell_price
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

    def set_own_enery(self, energy):
        self.current_energy = energy

'''
TODO:
- implement getters and setters
- implement house types and incorporate them in energy demand
- add varied energy demand
- make update method to perform all updates agent needs (energy level, energy demand, etc.)
'''