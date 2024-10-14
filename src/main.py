import matplotlib.pyplot as plt
import numpy as np
import csv

from random import choices, shuffle

from agent import CentralAgent, ProsumerAgent
from data import get_average_difference_in_seasons
from enums import HouseType, OrderType
from progressbar import progressbar, clear_progressbar

# Maybe add production_range?
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

    seasonal_effect = (percentage_diff / 100) * seasonality

    # Add daily fluctuation for randomness (cloudy days, varying weather)
    daily_variability = np.random.uniform(-0.1, 0.1)

    # Base energy production level: 2 kWh per solar panel
    base_production = 2

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

    for i in range(1, n + 1):
        selected_house_type = choices(house_types, weights=house_proportions, k=1)[0]
        base_energy_demand_yearly = calculate_base_demand(selected_house_type)
        
        agent_list.append(
            ProsumerAgent(
                id=i,
                re_sources=calculate_solar_panels(base_energy_demand_yearly),
                base_energy_demand=base_energy_demand_yearly / 365,
                sell_price=np.random.uniform(0.8, 1.2),
                sensitivity=np.random.uniform(0.1, 0.5),
                house_type=selected_house_type
            )
        )

    if verbose:
        for agent in agent_list:
            print(f"Agent {agent.id} has house type {agent.house_type} and own demand base {agent.own_demand_base}")    

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


def calculate_solar_panels(annual_energy_demand, noise_level=0.1, zero_panel_prob=0.05):
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


def simulation(mode = 'distributed', n_agents = 200, n_runs = 10, t_max = 1000, verbose = False):
    #np.random.seed(0)

    print("Now running the simulation in " + mode + " mode")

    # open data file for storing results and write header
    f = open("../data/results_"+ mode + ".csv", 'w+', newline='')
    writer = csv.writer(f)
    writer.writerow(['run', 'timestep',  'average balance', 'total energy demand', 'total central energy bought', 
                     'total energy produced', 'average price'])

    for run in range(n_runs):

        progressbar(run, n_runs)

        _, _, percentage_diff = get_average_difference_in_seasons(2022)

        agent_list = []
        buy_order_list = []
        sell_order_list = []

        #add default_order to sell_order_list
        central_agent = CentralAgent(0, 999999, 1)
        central_agent.create_energy(10)
        agent_list.append(central_agent)
        default_order = central_agent.create_order()
        sell_order_list.append(default_order)

        # Create agents
        agent_list.extend(generate_agents(n_agents, verbose))

        avg_price = 1

        for day in range(t_max):

            if day % 100 == 0 and verbose:
                print('Day: ', day)

            #reset lists
            buy_order_list = []
            sell_order_list = []

            energy_today = daily_energy_level(day, percentage_diff)

            # create energy
            for curr_agent in agent_list:
                if isinstance(curr_agent, CentralAgent):
                    continue

                curr_agent.update(energy_today, avg_price, day)

            total_demand = sum([agent.energy_demand for agent in agent_list if not isinstance(agent, CentralAgent)])
            total_produced = sum([agent.energy_level for agent in agent_list if not isinstance(agent, CentralAgent)])

            # create orders
            for curr_agent in agent_list:
                order = curr_agent.create_order()
                if order is not None:
                    if order.type == OrderType.BUY:
                        buy_order_list.append(order)
                    elif mode == 'distributed': # prosumer agents only make sell order in distributed setup
                        sell_order_list.append(order)
                        
            #add defaultorder to sell_order_list
            #reset central agent
            central_agent.energy_level = 999999
            default_order = central_agent.create_order()
            sell_order_list.append(default_order)

            #print info
            if verbose:
                print('Day: ', day)
                print('Energy today: ', energy_today)
                print('')
                for i in range(n_agents):
                    if isinstance(agent_list[i], CentralAgent):
                        continue
                    print('Agent id: ', agent_list[i].id, ' Energy: ', agent_list[i].energy_level, ' Demand: ', agent_list[i].energy_demand)
                print('')
                print('Buy orders: ')
                for order in buy_order_list:
                    print('Seller id: ', order.seller_id, ' Amount: ', order.amount, ' Price: ', order.price)
                print('Sell orders: ')
                for order in sell_order_list:
                    print('Seller id: ', order.seller_id, ' Amount: ', order.amount, ' Price: ', order.price)
                print('')
                print('total energy: ', sum([agent.energy_level for agent in agent_list if not isinstance(agent, CentralAgent)]))
                print('total demand: ', sum([agent.energy_demand for agent in agent_list if not isinstance(agent, CentralAgent)]))

            #sort orders by price
            sell_order_list = sorted(sell_order_list, key=lambda x: x.price)

            #total sales 
            sold_amount_list = []
            sold_price_list = []
            

            # match orders and track energy bought from central distributor
            central_energy_sold = 0
            shuffle(buy_order_list)
            for buy_order in buy_order_list:

                while buy_order.type != OrderType.DONE:
                    for sell_order in sell_order_list:
                        #buy cheapest energy first
                        if sell_order.amount >= buy_order.amount and sell_order.type != OrderType.DONE:
                            if verbose:
                                print('Matched order: ', 'Buyer: ', buy_order.seller_id, ' Seller: ', sell_order.seller_id, ' Amount: ', buy_order.amount, ' Price: ', buy_order.price)
                                print('Buyer: ', buy_order.seller_id, ' now has: ', agent_list[buy_order.seller_id].energy_level)

                            buyer = agent_list[buy_order.seller_id]
                            seller = agent_list[sell_order.seller_id]

                            buyer.set_own_energy(buyer.energy_level + buy_order.amount)
                            seller.set_own_energy(seller.energy_level - buy_order.amount)

                            buyer.balance -= buy_order.amount * buy_order.price
                            seller.balance += buy_order.amount * buy_order.price
                            
                            # changed this to buy_order.amount since the sell order isn't fully drained
                            sold_amount_list.append(buy_order.amount)
                            sold_price_list.append(sell_order.price)

                            # only needed here because sell_order amount of central agent will never be lower than buy_order amount
                            if sell_order.seller_id == 0:
                                central_energy_sold += buy_order.amount


                            if verbose:
                                print('Buyer: ', buy_order.seller_id, ' now has: ', buyer.energy_level)

                            sell_order.amount -= buy_order.amount
                            buy_order.amount = 0
                            buy_order.type = OrderType.DONE
                            break
                        elif sell_order.amount < buy_order.amount and sell_order.type != OrderType.DONE:
                            if verbose:
                                print('Matched order: ', 'Buyer: ', buy_order.seller_id, ' Seller: ', sell_order.seller_id, ' Amount: ', sell_order.amount, ' Price: ', sell_order.price)
                                print('Buyer: ', buy_order.seller_id, ' now has: ', agent_list[buy_order.seller_id].energy_level)

                            buyer = agent_list[buy_order.seller_id]
                            seller = agent_list[sell_order.seller_id]

                            buyer.set_own_energy(buyer.energy_level + buy_order.amount)
                            seller.set_own_energy(seller.energy_level - buy_order.amount)

                            buyer.balance -= buy_order.amount * buy_order.price    
                            seller.balance += buy_order.amount * buy_order.price

                            sold_amount_list.append(sell_order.amount)
                            sold_price_list.append(sell_order.price)

                            if verbose:
                                print('Buyer: ', buy_order.seller_id, ' now has: ', buyer.energy_level)

                            buy_order.amount -= sell_order.amount
                            sell_order.amount = 0
                            sell_order.type = OrderType.DONE 

            #adjust agent prices

            for sell_order in sell_order_list:
                if sell_order.type != OrderType.DONE and sell_order.seller_id != 0:
                    if verbose:
                        print('Unfullfilled sell order: ', 'Seller: ', sell_order.seller_id, ' Amount: ', sell_order.amount, ' Price: ', sell_order.price)
                    #sell to central agent
                    central_agent.energy_level += sell_order.amount

                    #update balance
                    central_agent.balance -= sell_order.amount * 0.3

                    seller = agent_list[sell_order.seller_id]
                    seller.set_own_energy(seller.energy_level - sell_order.amount)
                    seller.balance += sell_order.amount * 0.3

                    sold_price_list.append(0.3)
                    sold_amount_list.append(sell_order.amount)
                    
                    sell_order.amount = 0
                    sell_order.type = OrderType.DONE

            #calculate average price
            avg_price = 0
            for i in range(len(sold_price_list)):
                avg_price += sold_price_list[i]*sold_amount_list[i]

            avg_price = avg_price / sum(sold_amount_list) if sum(sold_amount_list) > 0 else 0

            #balance 
            avg_balance = sum([agent.balance for agent in agent_list])/ n_agents 

            #check if everyone is satisfied
            if verbose:
                for i in range(n_agents):
                    if isinstance(agent_list[i], CentralAgent):
                        continue
                    if agent_list[i].energy_level < agent_list[i].energy_demand:
                        print('Agent id: ', agent_list[i].id, ' not satisfied')
                    else:
                        print('Agent id: ', agent_list[i].id, ' satisfied')


            # write timestep info to csv
            writer.writerow([run, day, avg_balance, total_demand, central_energy_sold, total_produced , avg_price])

    clear_progressbar()


if __name__ == '__main__':
    # run both simulations using 
    simulation('distributed')
    simulation('centralised')



# '''
# TODO:
# - determine initial conditions
# - maybe make separate simulation file in case time left over
# '''