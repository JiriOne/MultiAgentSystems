import numpy as np
from abc import ABC, abstractmethod

from order import Order
from enums import OrderType, HouseType 


class BaseAgent(ABC):
    def __init__(self, id, re_sources, sell_price):
        self.id = id
        self.re_sources = re_sources
        self.sell_price = sell_price
        self.funds = 0
        self.current_energy = 0


    @abstractmethod
    def create_order(self):
        pass


class CentralAgent(BaseAgent):
    def create_energy(self, daily_energy_level):
        self.current_energy = self.re_sources * daily_energy_level * 10

    def set_own_energy(self, energy):
        self.current_energy = energy

    def create_order(self):
        return Order(self.id, self.re_sources, self.sell_price, OrderType.SELL)


class DistributedAgent(BaseAgent):
    def __init__(self, id, re_sources, own_demand_base, sell_price, sensitivity, house_type):
        super().__init__(id, re_sources, sell_price)
        self.own_demand_base = own_demand_base
        self.own_demand = own_demand_base
        self.sensitivity = sensitivity
        self.house_type = house_type


    def create_energy(self, daily_energy_level):
        self.current_energy = self.re_sources * daily_energy_level * 1.5


    def create_order(self):
        if self.current_energy > self.own_demand:
            tmp_amount = self.current_energy - self.own_demand
            return Order(self.id, tmp_amount, self.sell_price, OrderType.SELL)
        elif self.current_energy < self.own_demand:
            tmp_amount = self.own_demand - self.current_energy
            return Order(self.id, tmp_amount, self.sell_price, OrderType.BUY)
        return None
    

    def update(self, daily_energy_level, average_price, iteration):
        self.current_energy = 0
        self.create_energy(daily_energy_level)
        self.own_demand = calculate_seasonal_demand(iteration, self.own_demand_base)
        self.sell_price = self.sensitivity * abs(self.current_energy - self.own_demand) + average_price + np.random.uniform(-0.1, 0.1)
        

    def set_own_energy(self, energy):
        self.current_energy = energy


# Sinusoidal function over 365 days
def calculate_seasonal_demand(iteration, own_demand_base):
    days_in_year = 365
    phase_shift = np.pi  # Shift by π to make the peak in winter and the trough in summer
    seasonality = np.sin((2 * np.pi * (iteration % days_in_year) / days_in_year) + phase_shift)
    
    seasonal_effect = 0.3 * seasonality
    
    # Add some random noise to the seasonality for variability at 2%
    random_noise = np.random.normal(loc=0, scale=0.02)
    
    return own_demand_base * (1 + seasonal_effect + random_noise)



# '''
# TODO:
# - implement getters and setters
# - implement house types and incorporate them in energy demand
#     - set a range of possible base demands per house type
#     - initiate agents based on housetype probabilities and then assign based demand
# - improve sell price stuff
# - determine parameter values (i.e. noise ranges, starting values, etc.)
# '''