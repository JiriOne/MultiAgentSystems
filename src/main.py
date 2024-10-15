import csv
import matplotlib.pyplot as plt
import numpy as np

from random import choices, shuffle, uniform

from agent import CentralAgent, ProsumerAgent
from data import get_average_difference_in_seasons
from enums import HouseType, OrderType
from progressbar import progressbar, clear_progressbar


CENTRAL_BUY_PRICE = 0.07
CENTRAL_SELL_PRICE = 0.24
HOUSE_TYPE_DATA = {
    HouseType.TERRACED_HOUSE: {"proportion": 28.8, "demand_range": (1590, 2610)},
    HouseType.DETACHED_HOUSE: {"proportion": 5.3, "demand_range": (4390, 4390)},
    HouseType.SEMI_DETACHED_HOUSE: {"proportion": 5.3, "demand_range": (2990, 3700)},
    HouseType.MULTI_FAMILY_HOUSE: {"proportion": 60.6, "demand_range": (1510, 2210)}
}


def daily_energy_level(day, percentage_diff):
    days_in_year = 365
    phase_shift = 0

    seasonality = np.sin((2 * np.pi * (day % days_in_year) / days_in_year) + phase_shift)
    print("Seasonality: ", seasonality)

    seasonal_effect = (percentage_diff / 100) * seasonality
    print("Seasonal Effect: ", seasonal_effect)

    # Add daily fluctuation for randomness (cloudy days, varying weather)
    daily_variability = np.random.uniform(-0.1, 0.1)

    # Base energy production level: 2 kWh per solar panel
    base_production = 2

    print("Seasonal Effect: ", seasonal_effect)

    # Final daily energy production level with seasonal and random variations
    return base_production * (1 + seasonal_effect + daily_variability)


def calculate_base_demand(house_type):
    demand_range = HOUSE_TYPE_DATA[house_type]["demand_range"]
    yearly_demand = np.random.randint(demand_range[0], demand_range[1] + 1)
    return yearly_demand


def generate_agents(n, verbose):
    house_types = list(HOUSE_TYPE_DATA.keys())
    house_proportions = [HOUSE_TYPE_DATA[ht]["proportion"] for ht in house_types]

    agent_list = []

    for i in range(n):
        selected_house_type = choices(house_types, weights=house_proportions, k=1)[0]
        base_energy_demand_yearly = calculate_base_demand(selected_house_type)
        
        agent_list.append(
            ProsumerAgent(
                id=i,
                n_panels=calculate_solar_panels(base_energy_demand_yearly),
                base_energy_demand=base_energy_demand_yearly / 365,
                sell_price=np.random.uniform(CENTRAL_BUY_PRICE + 0.01, CENTRAL_SELL_PRICE - 0.01),
                sensitivity=np.random.uniform(0.1, 0.5),
                house_type=selected_house_type
            )
        )

    if verbose:
        for agent in agent_list:
            print(f"Agent {agent.id} has house type {agent.house_type} and own demand base {agent.base_energy_demand}")    

    return agent_list


def plot_graphs(avg_price_list, energy_list, n_agents, agent_list, balance_sheet):
    #plot averge price and energy over time with two y axis scales
    fig, ax1 = plt.subplots()

    fig.set_figwidth(15)

    ax2 = ax1.twinx()
    ax1.plot(avg_price_list, 'g-')
    ax2.plot(energy_list, 'b-')

    ax1.set_xlabel('Days')
    ax1.set_ylabel('Average Price', color='g')
    #ax1.set_ylim(0, 2)
    ax2.set_ylabel('Energy', color='b')

    plt.title(f'n_agents = {n_agents}, avg_re = {np.mean([agent.re_sources for agent in agent_list if not isinstance(agent, CentralAgent)])}, avg_de = {np.mean([agent.own_demand for agent in agent_list if not isinstance(agent, CentralAgent)])}')

    plt.savefig('output.png')

    fig2 = plt.figure()
    plt.plot(balance_sheet)
    plt.title('Balance Sheet')
    plt.xlabel('Days')
    plt.ylabel('Balance')
    plt.savefig('output_balance.png')


def calculate_solar_panels(annual_energy_demand, noise_level=0.2, zero_panel_prob=0.05):
    # Check if the house gets 0 solar panels
    if np.random.rand() < zero_panel_prob:
        return 0

    # Solar panel production: 2 kWh per day, 365 days per year = 730 kWh/year per panel
    panel_production = 730

    # Calculate the optimal number of solar panels
    optimal_panels = annual_energy_demand / panel_production

    # Introduce variability (better or worse setups)
    noise_factor = np.random.uniform(1 - noise_level, 1 + noise_level)
    actual_panels = optimal_panels * noise_factor

    # Return the final number of panels
    return round(actual_panels)


def simulation(mode = 'distributed', n_agents = 10, n_runs = 1, t_max = 1000, verbose = False):
    #np.random.seed(0)

    print("Now running the simulation in " + mode + " mode")

    # open data file for storing results and write header
    with open(f"../data/results_{mode}.csv", 'w+', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['run', 'timestep', 'average balance', 'total energy demand', 'total central energy bought', 
                         'total energy produced', 'average price'])

        for run in range(n_runs):

            progressbar(run, n_runs)

            _, _, percentage_diff = get_average_difference_in_seasons(2022)

            agent_list = []
            buy_order_list = []
            sell_order_list = []

            #add default_order to sell_order_list
            central_agent = CentralAgent(0, CENTRAL_SELL_PRICE, CENTRAL_BUY_PRICE)

            # Create agents
            agent_list.extend(generate_agents(n_agents, verbose))

            avg_price = round(uniform(CENTRAL_BUY_PRICE + 0.01, CENTRAL_SELL_PRICE - 0.01), 2)

            for day in range(t_max):

                if day % 100 == 0 and verbose:
                    print('Day: ', day)

                #reset lists
                buy_order_list = []
                sell_order_list = []

                energy_today = daily_energy_level(day, percentage_diff)


                print("Energy Today: ", energy_today)

                # create energy
                for curr_agent in agent_list:
                    curr_agent.update(energy_today, avg_price, day)

                total_demand = sum([agent.energy_demand for agent in agent_list])
                total_produced = sum([agent.energy_production for agent in agent_list])

                # create orders
                for curr_agent in agent_list:
                    order = curr_agent.create_order()
                    if order is not None:
                        if order.type == OrderType.BUY:
                            buy_order_list.append(order)
                        else:
                            if mode == 'distributed': # prosumer agents only make sell order in distributed setup
                                sell_order_list.append(order)

                #print info
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

                #sort orders by price
                sell_order_list = sorted(sell_order_list, key=lambda x: x.price)

                #total sales 
                sold_amount_list = []
                sold_price_list = []
                central_energy_sold = 0
                
                shuffle(buy_order_list)

                # First, process agent-to-agent orders
                for buy_order in buy_order_list:
                    while buy_order.type != OrderType.DONE:
                        for sell_order in sell_order_list:
                                
                            # Fulfill the entire buy order if possible
                            if sell_order.amount >= buy_order.amount:
                                buyer = agent_list[buy_order.agent_id]
                                seller = agent_list[sell_order.agent_id]

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
                                buy_order.amount = 0
                                buy_order.type = OrderType.DONE

                                if verbose:
                                    print(f"Matched order: Buyer {buy_order.agent_id}, Seller {sell_order.agent_id}, Amount {buy_order.amount}, Price {buy_order.price}")

                                break  # Fully fulfilled, move to next buy_order

                            # If sell order can't fully fulfill the buy order, partially fulfill it
                            elif sell_order.amount < buy_order.amount:
                                buyer = agent_list[buy_order.agent_id]
                                seller = agent_list[sell_order.agent_id]

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

                            if verbose:
                                print(f"Central agent fulfilled {buy_order.amount} kWh for Buyer {buy_order.agent_id} at {central_agent.sell_price} €/kWh")
                            
                            # Mark buy order as done
                            buy_order.amount -= buy_order.amount
                            if buy_order.amount == 0:
                                buy_order.type = OrderType.DONE
                
                # The central agent buys energy at fixed prices (0.07)
                for sell_order in sell_order_list:
                    if sell_order.amount > 0:
                        seller = agent_list[sell_order.agent_id]

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
                        if agent.energy_production < agent.energy_demand:
                            print('Agent id: ', agent.id, ' not satisfied')
                            print('Energy production: ', agent.energy_production, ' Energy demand: ', agent.energy_demand)

                        else:
                            print('Agent id: ', agent.id, ' satisfied')


                # write timestep info to csv
                writer.writerow([run, day, avg_balance, total_demand, central_energy_sold, total_produced , avg_price])

        clear_progressbar()


if __name__ == '__main__':
    # run both simulations using 
    simulation('distributed')
    simulation('centralised')