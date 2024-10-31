""" 
Main file for running the simulation
The simulation can be run in two modes: 'centralised' and 'distributed'
"""

import csv
from random import choices, shuffle, uniform

import numpy as np

from agent import CentralAgent, ProsumerAgent
from data import get_average_difference_in_seasons
from enums import HouseType, OrderType
from progressbar import clear_progressbar, progressbar

#initalize buy and sell price of central agent
CENTRAL_BUY_PRICE = 0.07
CENTRAL_SELL_PRICE = 0.24

# Define the house type data & demand range
HOUSE_TYPE_DATA = {
    HouseType.TERRACED_HOUSE: {"proportion": 28.8, "demand_range": (1590, 2610)},
    HouseType.DETACHED_HOUSE: {"proportion": 5.3, "demand_range": (4390, 4390)},
    HouseType.SEMI_DETACHED_HOUSE: {"proportion": 5.3, "demand_range": (2990, 3700)},
    HouseType.MULTI_FAMILY_HOUSE: {"proportion": 60.6, "demand_range": (1510, 2210)}
}

# Calculate the daily energy level
def daily_energy_level(day, percentage_diff, verbose=False):
    """
    Caclulate the daily energy level based on the seasonality and random fluctuations
    :param day: current day
    :param percentage_diff: percentage difference between summer and winter energy production
    :param verbose: print additional information
    """
    days_in_year = 365
    phase_shift = 0
 
    seasonality = np.sin((2 * np.pi * (day % days_in_year) / days_in_year) + phase_shift) + 0.3        

    seasonal_effect = (percentage_diff / 100) * seasonality

    if verbose:
        print("Seasonality: ", seasonality)
        print("Seasonal Effect: ", seasonal_effect)

    # Add daily fluctuation for randomness (cloudy days, varying weather)
    daily_variability = np.random.uniform(-0.1, 0.1)

    # Base energy production level: 2 kWh per solar panel
    base_production = 2

    if verbose:
        print("Seasonal Effect: ", seasonal_effect)

    # Final daily energy production level with seasonal and random variations
    return base_production * (1 + seasonal_effect + daily_variability)

# Calculate the base demand for each house type
def calculate_base_demand(house_type):
    """
    Caclulate the base demand for each house type
    :param house_type: the type of the house
    """
    demand_range = HOUSE_TYPE_DATA[house_type]["demand_range"]
    yearly_demand = np.random.randint(demand_range[0], demand_range[1] + 1)
    return yearly_demand

# Generate agents with random house types and energy demands
def generate_agents(n, verbose, sens_range=[0.005, 0.02], panel_production=1):
    """
    Generate agents with random house types and energy demands, and solar panels
    :param n: number of agents
    :param verbose: print additional information
    :param sens_range: sensitivity range for the agents
    :param panel_production: production of the solar panels
    """
    house_types = list(HOUSE_TYPE_DATA.keys())
    house_proportions = [HOUSE_TYPE_DATA[ht]["proportion"] for ht in house_types]

    agent_list = []

    # Generate agents
    for i in range(n):
        selected_house_type = choices(house_types, weights=house_proportions, k=1)[0]
        base_energy_demand_yearly = calculate_base_demand(selected_house_type)
        
        agent_list.append(
            ProsumerAgent(
                id=i,
                n_panels=calculate_solar_panels(base_energy_demand_yearly, panel_production),
                base_energy_demand=base_energy_demand_yearly / 365,
                sell_price=np.random.uniform(CENTRAL_BUY_PRICE + 0.01, CENTRAL_SELL_PRICE - 0.01),
                sensitivity=np.random.uniform(sens_range[0], sens_range[1]),
                house_type=selected_house_type
            )
        )

    # Print agent info
    if verbose:
        for agent in agent_list:
            print(f"Agent {agent.id} has house type {agent.house_type} and own demand base {agent.base_energy_demand}")    

    return agent_list

# Calculate the number of solar panels for each house
def calculate_solar_panels(annual_energy_demand, noise_level=0.2, zero_panel_prob=0.25, panel_production=1):
    """
    Caclulate the number of solar panels for each house
    :param annual_energy_demand: the annual energy demand of the house
    :param noise_level: the noise level for the solar panels
    :param zero_panel_prob: the probability of having 0 solar panels
    :param panel_production: the production of the solar panels
    """
    # Check if the house gets 0 solar panels
    if np.random.rand() < zero_panel_prob:
        return 0

    # Solar panel production: 2 kWh per day, 365 days per year = 730 kWh/year per panel
    panel_production = round(365 * panel_production)

    # Calculate the optimal number of solar panels
    optimal_panels = annual_energy_demand / panel_production

    # Introduce variability (better or worse setups)
    noise_factor = np.random.uniform(1 - noise_level, 1 + noise_level) 
    actual_panels = optimal_panels * noise_factor

    # Return the final number of panels
    return round(actual_panels)

# Run the simulation
def simulation(mode = 'distributed', n_agents = 200, n_runs = 10, t_max = 1000, verbose = False, sens_range = [0.005,0.02], panel_prod = 1):
    """
    Run the simulation
    :param mode: the mode of the simulation ('centralised' or 'distributed')
    :param n_agents: the number of agents
    :param n_runs: the number of runs
    :param t_max: the maximum number of timesteps
    :param verbose: print additional information
    :param sens_range: sensitivity range for the agents
    :param panel_prod: production of the solar panels
    """
    # Set random seed for reproducibility
    #np.random.seed(0)

    print("Now running the simulation in " + mode + " mode")

    # open data file for storing results and write header
    with open(f"../data/results_{mode}_sens{sens_range}_panel{panel_prod}.csv", 'w+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'run', 
            'timestep', 
            'average balance', 
            'total energy demand', 
            'total central energy bought', 
            'total energy produced', 
            'average price'
        ])

        for run in range(n_runs):

            progressbar(run, n_runs)

            _, _, percentage_diff = get_average_difference_in_seasons(2022)

            agent_list = []
            buy_order_list = []
            sell_order_list = []

            # Create central agent
            central_agent = CentralAgent(0, CENTRAL_SELL_PRICE, CENTRAL_BUY_PRICE)

            # Create agents
            agent_list.extend(generate_agents(n_agents, verbose, sens_range, panel_prod))

            # Set starting random avg price between 0.08 - 0.23 for for run
            avg_price = round(uniform(CENTRAL_BUY_PRICE + 0.01, CENTRAL_SELL_PRICE - 0.01), 2)

            for day in range(t_max):

                if day % 100 == 0 and verbose:
                    print('Day: ', day)

                # Reset order lists
                buy_order_list = []
                sell_order_list = []

                # Determine energy level for day
                energy_today = daily_energy_level(day, percentage_diff, verbose)

                if verbose:
                    print("Energy Today: ", energy_today)

                # Update agent energy based on energy level of the day (energy_today)
                for curr_agent in agent_list:
                    curr_agent.update(energy_today, avg_price, day)


                # Determine total demand and produced energy
                total_demand = sum([agent.energy_demand for agent in agent_list])
                total_produced = sum([agent.energy_production for agent in agent_list])

                # Create orders
                for curr_agent in agent_list:
                    order = curr_agent.create_order()
                    if order is not None:
                        if order.type == OrderType.BUY:
                            buy_order_list.append(order)
                        else:
                            sell_order_list.append(order)

                # Print info
                if verbose:
                    print('Day: ', day)
                    print('Energy today: ', energy_today)
                    print('')
                    for agent in agent_list:
                        print('Agent id: ', agent.id, ' Energy Production: ', agent.energy_production, ' Energy Demand: ', agent.energy_demand)
                    print('')
                    print('Buy orders: ')
                    for order in buy_order_list:
                        print('Agent id: ', order.agent_id, ' Amount: ', order.amount)
                    print('Sell orders: ')
                    for order in sell_order_list:
                        print('Agent id: ', order.agent_id, ' Amount: ', order.amount, ' Price: ', order.price)
                    print('')
                    print('total energy produced: ', sum([agent.energy_production for agent in agent_list]))
                    print('total energy demand: ', sum([agent.energy_demand for agent in agent_list]))

                # Sort orders by price (low to high))
                sell_order_list = sorted(sell_order_list, key=lambda x: x.price)

                # Create sales tracking variables
                sold_amount_list = []
                sold_price_list = []
                central_energy_sold = 0
                
                # Shuffle buy order list so order of agents purchasing energy is random.
                shuffle(buy_order_list)

                # First, process agent-to-agent orders
                for buy_order in buy_order_list:

                    # Loop till order is fulfilled
                    while buy_order.type != OrderType.DONE:

                        # Only process agent-to-agent order if mode is 'distributed'
                        if mode == 'distributed':
                            for sell_order in sell_order_list:

                                # If agent sell price is higher than the central agent sell price (0.24), cancel agent-to-agent orders.
                                # if sell_order_list[0].price > central_agent.sell_price:
                                #     break

                                # Fulfill the entire buy order if possible
                                if sell_order.amount >= buy_order.amount and sell_order.price <= central_agent.sell_price:
                                    buyer = agent_list[buy_order.agent_id]
                                    seller = agent_list[sell_order.agent_id]

                                    seller.total_sold_energy_list.append(buy_order.amount)
                                    seller.total_sold_energy_price_list.append(sell_order.price)

                                    # Transfer energy from seller to buyer
                                    buyer.set_own_energy(buy_order.amount)
                                    seller.set_own_energy(-buy_order.amount)

                                    # Update balances
                                    buyer.balance -= buy_order.amount * sell_order.price
                                    seller.balance += buy_order.amount * sell_order.price

                                    sold_amount_list.append(buy_order.amount)
                                    sold_price_list.append(sell_order.price)

                                    # Mark orders as done
                                    sell_order.amount -= buy_order.amount
                                    buyer.energy_bought += buy_order.amount
                                    buy_order.amount = 0
                                    buy_order.type = OrderType.DONE

                                    if sell_order.price > central_agent.sell_price:
                                        print(f"Agent {sell_order.agent_id} sold energy at higher price than central agent: {sell_order.price} €/kWh")

                                    if verbose:
                                        print(f"Matched order: Buyer {buy_order.agent_id}, Seller {sell_order.agent_id}, Amount {buy_order.amount}, Price {buy_order.price}")

                                    break  # Fully fulfilled, move to next buy_order

                                # If sell order can't fully fulfill the buy order, partially fulfill it
                                elif sell_order.amount < buy_order.amount and sell_order.price <= central_agent.sell_price:
                                    buyer = agent_list[buy_order.agent_id]
                                    seller = agent_list[sell_order.agent_id]

                                    seller.total_sold_energy_list.append(sell_order.amount)
                                    seller.total_sold_energy_price_list.append(sell_order.price)

                                    # Transfer partial energy from seller to buyer
                                    buyer.set_own_energy(sell_order.amount)
                                    seller.set_own_energy(-sell_order.amount)

                                    # Update balances
                                    buyer.balance -= sell_order.amount * sell_order.price
                                    seller.balance += sell_order.amount * sell_order.price

                                    sold_amount_list.append(sell_order.amount)
                                    sold_price_list.append(sell_order.price)

                                    # Adjust the amounts left in both orders
                                    buy_order.amount -= sell_order.amount
                                    buyer.energy_bought += sell_order.amount
                                    sell_order.amount = 0
                                    sell_order.type = OrderType.DONE

                                    if verbose:
                                        print(f"Partial match: Buyer {buy_order.agent_id}, Seller {sell_order.agent_id}, Amount {sell_order.amount}, Price {sell_order.price}")

                                    # Continue looping through other sell orders to fulfill the rest of the buy order


                        buyer = agent_list[buy_order.agent_id]

                        # The central agent sells energy at fixed prices (0.24)
                        if buy_order.amount > 0:  # Agent needs to buy energy from central
    
                            buyer.set_own_energy(buy_order.amount)
                            central_agent.energy_sold += buy_order.amount

                            # Adjust balances
                            buyer.balance -= buy_order.amount * central_agent.sell_price
                            central_agent.balance += buy_order.amount * central_agent.sell_price

                            sold_amount_list.append(buy_order.amount)
                            sold_price_list.append(central_agent.sell_price)

                            central_energy_sold += buy_order.amount

                            if verbose:
                                print(f"Central agent fulfilled {buy_order.amount} kWh for Buyer {buy_order.agent_id} at {central_agent.sell_price} €/kWh")
                            
                            # Mark buy order as done
                            buy_order.amount -= buy_order.amount
                            buyer.energy_bought += buy_order.amount
                            if buy_order.amount == 0:
                                buy_order.type = OrderType.DONE
                
                # The central agent buys energy at fixed prices (0.07)
                for sell_order in sell_order_list:
                    if sell_order.amount > 0:
                        
                        seller = agent_list[sell_order.agent_id]

                        seller.total_sold_energy_list.append(sell_order.amount)
                        seller.total_sold_energy_price_list.append(sell_order.price)

                        seller.set_own_energy(-sell_order.amount)
                        central_agent.energy_bought += sell_order.amount

                        # Adjust balances
                        seller.balance += sell_order.amount * central_agent.buy_price
                        central_agent.balance -= sell_order.amount * central_agent.buy_price

                        sold_amount_list.append(sell_order.amount)
                        sold_price_list.append(central_agent.buy_price)

                        if verbose:
                            print(f"Central agent fulfilled {sell_order.amount} kWh for Seller {sell_order.agent_id} at {central_agent.buy_price} €/kWh")


                # Calculate the weighted average price
                total_amount_sold = sum(sold_amount_list)
                avg_price = (
                    sum(price * amount for price, amount in zip(sold_price_list, sold_amount_list)) / total_amount_sold
                    if total_amount_sold > 0 else 0
                )

                # Calculate the average balance of all agents
                avg_balance = sum(agent.balance for agent in agent_list) / n_agents

                # Check if each agent is satisfied
                if verbose:
                    for agent in agent_list:
                        if round(agent.energy_production, 5) < round(agent.energy_demand, 5):
                            print('Agent id: ', agent.id, ' not satisfied')
                            print('Energy production: ', agent.energy_production, ' Energy demand: ', agent.energy_demand)

                        else:
                            print('Agent id: ', agent.id, ' satisfied')


                # write timestep info to csv
                writer.writerow([run, day, avg_balance, total_demand, central_energy_sold, total_produced , avg_price])
                

        clear_progressbar()


if __name__ == '__main__':
    #grid search for sensitivity and panel production
    for sens in [[0.005, 0.02], [0.01, 0.02], [0.05, 0.1]]:
        for panel_prod in [0.1, 0.25, 0.5, 1]:
            simulation('distributed', n_agents=200, n_runs=100, t_max=365*5, sens_range=sens, panel_prod=panel_prod)
            quit()
            simulation('centralised', n_agents=200, n_runs=100, t_max=365*5, sens_range=sens, panel_prod=panel_prod)