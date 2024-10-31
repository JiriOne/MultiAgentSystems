# Agent classes for the simulation
""" 
Descriprion:
This file contains the agent classes for the simulation. The agents are divided into two categories: CentralAgent and ProsumerAgent.
The CentralAgent is the agent that buys and sells energy to the ProsumerAgents. The ProsumerAgent is the agent that produces energy
and sells it to the CentralAgent or other prosumers.
"""



from abc import ABC, abstractmethod
import numpy as np

from enums import OrderType
from order import Order

# Base agent class
class BaseAgent(ABC):

    # Intialize the agent
    def __init__(self, id, sell_price):
        self.id = id
        self.sell_price = sell_price
        self.balance = 0
        self.total_sold_energy_list = []
        self.total_sold_energy_price_list = []


    # Order creation method
    @abstractmethod
    def create_order(self):
        pass

# Central agent class
class CentralAgent(BaseAgent):

    # Initialize the central agent
    def __init__(self, id, sell_price, buy_price):
        super().__init__(id, sell_price)
        self.energy_bought = 0
        self.energy_sold = 0
        self.buy_price = buy_price

    # Method to create an order
    def create_order(self):
        pass

# Prosumer agent class
class ProsumerAgent(BaseAgent):

    # Initialize the prosumer agent
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

    # Method to calculate the energy balance
    def calculate_energy_balance(self):
        self.energy_balance = self.energy_production - self.energy_demand + self.energy_bought  


    # Method to create energy
    def create_energy(self, daily_energy_level):
        return self.n_panels * daily_energy_level


    # Method to create an order
    def create_order(self):

        # Energy Surplus
        if self.energy_production > self.energy_demand:
            energy_surplus = self.energy_production - self.energy_demand
            return Order(self.id, energy_surplus, self.sell_price, OrderType.SELL)
        
        # Energy Deficit
        elif self.energy_production < self.energy_demand: # Deficit
            energy_deficit = self.energy_demand - self.energy_production
            return Order(self.id, energy_deficit, 0, OrderType.BUY)
        
        return None
    
    # Method to update the agent
    def update(self, daily_energy_level, average_price, iteration):

        # Reset agent & calculate energy production, demand and balance
        self.reset()
        self.energy_production = self.create_energy(daily_energy_level)
        self.energy_demand = calculate_seasonal_demand(iteration, self.base_energy_demand)
        self.energy_balance = self.energy_production - self.energy_demand

        # Calculate sold energy and price to update sell price
        if len(self.total_sold_energy_list) > 0:
            actual_sold_price = 0
            for idx, price in enumerate(self.total_sold_energy_price_list):
                actual_sold_price += price*self.total_sold_energy_list[idx]
            actual_sold_price /= sum(self.total_sold_energy_list)

            if actual_sold_price > average_price:
                self.sell_price = self.sell_price + self.sensitivity
            else:
                self.sell_price = max(0,self.sell_price - self.sensitivity)

        #reset lists
        self.total_sold_energy_list = []
        self.total_sold_energy_price_list = []

    # Method to reset the agent
    def reset(self):
        self.energy_production = 0
        self.energy_demand = 0
        self.energy_bought = 0
        self.energy_balance = 0

    # Method to set the energy production
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