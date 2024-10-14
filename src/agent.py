import numpy as np
from abc import ABC, abstractmethod

from order import Order
from enums import OrderType, HouseType 


class BaseAgent(ABC):
    def __init__(self, id, n_panels, sell_price):
        self.id = id
        self.n_panels = n_panels
        self.sell_price = sell_price
        self.balance = 0
        self.energy_level = 0


    @abstractmethod
    def create_order(self):
        pass


class CentralAgent(BaseAgent):
    def create_energy(self, daily_energy_level):
        self.energy_level = self.n_panels * daily_energy_level * 10

    def set_own_energy(self, energy):
        self.energy_level = energy

    def create_order(self):
        return Order(self.id, self.n_panels, self.sell_price, OrderType.SELL)


class ProsumerAgent(BaseAgent):
    def __init__(self, id, re_sources, base_energy_demand, sell_price, sensitivity, house_type):
        super().__init__(id, re_sources, sell_price)
        self.base_energy_demand = base_energy_demand
        self.energy_demand = base_energy_demand
        self.sensitivity = sensitivity
        self.house_type = house_type


    def create_energy(self, daily_energy_level):
        self.energy_level = self.n_panels * daily_energy_level * 1.5


    def create_order(self):
        if self.energy_level > self.energy_demand:
            tmp_amount = self.energy_level - self.energy_demand
            return Order(self.id, tmp_amount, self.sell_price, OrderType.SELL)
        elif self.energy_level < self.energy_demand:
            tmp_amount = self.energy_demand - self.energy_level
            return Order(self.id, tmp_amount, self.sell_price, OrderType.BUY)
        return None
    

    def update(self, daily_energy_level, average_price, iteration):
        self.energy_level = 0
        self.create_energy(daily_energy_level)
        self.energy_demand = calculate_seasonal_demand(iteration, self.base_energy_demand)
        self.sell_price = self.sensitivity * abs(self.energy_level - self.energy_demand) + average_price + np.random.uniform(-0.1, 0.1)
        

    def set_own_energy(self, energy):
        self.energy_level = energy


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