from abc import ABC, abstractmethod
import numpy as np

from enums import OrderType
from order import Order


class BaseAgent(ABC):
    def __init__(self, id, sell_price):
        self.id = id
        self.sell_price = sell_price
        self.balance = 0


    @abstractmethod
    def create_order(self):
        pass


class CentralAgent(BaseAgent):
    def __init__(self, id, sell_price, buy_price):
        super().__init__(id, sell_price)
        self.energy_bought = 0
        self.energy_sold = 0
        self.buy_price = buy_price


    def create_order(self):
        pass


class ProsumerAgent(BaseAgent):
    def __init__(self, id, sell_price, n_panels, base_energy_demand, sensitivity, house_type):
        super().__init__(id, sell_price)
        self.n_panels = n_panels
        self.base_energy_demand = base_energy_demand
        self.energy_demand = base_energy_demand
        self.energy_production = 0
        self.energy_bought = 0
        self.energy_balance = 0
        self.sensitivity = sensitivity
        self.house_type = house_type


    def calculate_energy_balance(self):
        self.energy_balance = self.energy_production - self.energy_demand + self.energy_bought  


    def create_energy(self, daily_energy_level):
        return self.n_panels * daily_energy_level


    def create_order(self):
        if self.energy_production > self.energy_demand: # Surplus
            energy_surplus = self.energy_production - self.energy_demand
            return Order(self.id, energy_surplus, self.sell_price, OrderType.SELL)
        
        elif self.energy_production < self.energy_demand: # Deficit
            energy_deficit = self.energy_demand - self.energy_production
            return Order(self.id, energy_deficit, 0, OrderType.BUY)
        
        return None
    

    def update(self, daily_energy_level, average_price, iteration):
        self.reset()
        self.energy_production = self.create_energy(daily_energy_level)
        self.energy_demand = calculate_seasonal_demand(iteration, self.base_energy_demand)
        self.energy_balance = self.energy_production - self.energy_demand
        self.sell_price = self.sensitivity * abs(self.energy_production - self.energy_demand) + average_price + np.random.uniform(-0.1, 0.1)
    

    def reset(self):
        self.energy_production = 0
        self.energy_demand = 0
        self.energy_bought = 0
        self.energy_balance = 0


    def set_own_energy(self, energy):
        self.energy_production += energy


# Sinusoidal function over 365 days
def calculate_seasonal_demand(iteration, own_demand_base):
    days_in_year = 365
    phase_shift = np.pi  # Shift by π to make the peak in winter and the trough in summer
    seasonality = np.sin((2 * np.pi * (iteration % days_in_year) / days_in_year) + phase_shift)
    
    seasonal_effect = 0.3 * seasonality
    
    # Add some random noise to the seasonality for variability at 2%
    random_noise = np.random.normal(loc=0, scale=0.02)
    
    return own_demand_base * (1 + seasonal_effect + random_noise)