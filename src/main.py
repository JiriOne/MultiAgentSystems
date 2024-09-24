import numpy as np
import matplotlib.pyplot as plt

from agent import agent
from order import order

def daily_energy_level(day):
    return np.sin(day / 8)*4 + 6 + np.random.uniform(-0.1, 0.1)

def main():
    
    #np.random.seed(0)

    agent_list = []
    buy_order_list = []
    sell_order_list = []

    n_agents = 5

    #add default_order to sell_order_list
    central_agent = agent(0, 999999, 0, sell_price=1, sensitivity=0.1)
    central_agent.create_energy(10)
    agent_list.append(central_agent)
    default_order = central_agent.create_order()
    sell_order_list.append(default_order)

    # Create agents
    for i in range(1,n_agents+1):
        agent_list.append(agent(i, 
                                np.random.randint(0, 10), 
                                own_demand_base=np.random.randint(200, 800), 
                                sell_price=np.random.uniform(0.8, 1.2), 
                                sensitivity=np.random.uniform(0.1, 0.5)))

    avg_price_list = []
    energy_list = []
    funds_list = []

    verbose = True

    days = 1000
    for day in range(days):

        if day % 100 == 0:
            print('Day: ', day)

        #reset lists
        buy_order_list = []
        sell_order_list = []

        energy_today = daily_energy_level(day)

        # create energy
        for curr_agent in agent_list:
            curr_agent.update(energy_today, avg_price_list[-1] if len(avg_price_list) > 0 else 1)

        # create orders
        for curr_agent in agent_list:
            order = curr_agent.create_order()
            if order is not None:
                if order.type == 'buy':
                    buy_order_list.append(order)
                else:
                    sell_order_list.append(order)
                    
        #add defaultorder to sell_order_list
        #reset central agent
        central_agent.current_energy = 999999
        default_order = central_agent.create_order()
        sell_order_list.append(default_order)

        #get stats for today    
        energy_list.append(energy_today)

        #print info
        if verbose:
            print('Day: ', day)
            print('Energy today: ', energy_today)
            print('')
            for i in range(n_agents):
                print('Agent id: ', agent_list[i].id, ' Energy: ', agent_list[i].current_energy, ' Demand: ', agent_list[i].own_demand)
            print('')
            print('Buy orders: ')
            for order in buy_order_list:
                print('Seller id: ', order.seller_id, ' Amount: ', order.amount, ' Price: ', order.price)
            print('Sell orders: ')
            for order in sell_order_list:
                print('Seller id: ', order.seller_id, ' Amount: ', order.amount, ' Price: ', order.price)
            print('')
            print('total energy: ', sum([agent.current_energy for agent in agent_list]))
            print('total demand: ', sum([agent.own_demand for agent in agent_list]))

        #sort orders by price
        sell_order_list = sorted(sell_order_list, key=lambda x: x.price)

        #total sales 
        sold_amount_list = []
        sold_price_list = []
        

        # match orders
        for buy_order in buy_order_list:

            while buy_order.type != 'done':
                for sell_order in sell_order_list:
                    #buy cheapest energy first
                    if sell_order.amount >= buy_order.amount and sell_order.type != 'done':
                        if verbose:
                            print('Matched order: ', 'Buyer: ', buy_order.seller_id, ' Seller: ', sell_order.seller_id, ' Amount: ', buy_order.amount, ' Price: ', buy_order.price)
                            print('Buyer: ', buy_order.seller_id, ' now has: ', agent_list[buy_order.seller_id].current_energy)

                        buyer = agent_list[buy_order.seller_id]
                        seller = agent_list[sell_order.seller_id]

                        buyer.set_own_enery(buyer.current_energy + buy_order.amount)
                        seller.set_own_enery(seller.current_energy - buy_order.amount)

                        buyer.funds -= buy_order.amount * buy_order.price
                        seller.funds += buy_order.amount * buy_order.price
                        

                        sold_amount_list.append(sell_order.amount)
                        sold_price_list.append(sell_order.price)

                        if verbose:
                            print('Buyer: ', buy_order.seller_id, ' now has: ', buyer.current_energy)

                        sell_order.amount -= buy_order.amount
                        buy_order.amount = 0
                        buy_order.type = 'done'
                        break
                    elif sell_order.amount < buy_order.amount and sell_order.type != 'done':
                        if verbose:
                            print('Matched order: ', 'Buyer: ', buy_order.seller_id, ' Seller: ', sell_order.seller_id, ' Amount: ', sell_order.amount, ' Price: ', sell_order.price)
                            print('Buyer: ', buy_order.seller_id, ' now has: ', agent_list[buy_order.seller_id].current_energy)

                        buyer = agent_list[buy_order.seller_id]
                        seller = agent_list[sell_order.seller_id]

                        buyer.set_own_enery(buyer.current_energy + buy_order.amount)
                        seller.set_own_enery(seller.current_energy - buy_order.amount)

                        buyer.funds -= buy_order.amount * buy_order.price    
                        seller.funds += buy_order.amount * buy_order.price

                        sold_amount_list.append(sell_order.amount)
                        sold_price_list.append(sell_order.price)

                        if verbose:
                            print('Buyer: ', buy_order.seller_id, ' now has: ', buyer.current_energy)

                        buy_order.amount -= sell_order.amount
                        sell_order.amount = 0
                        sell_order.type = 'done'  

        #adjust agent prices

        for sell_order in sell_order_list:
            if sell_order.type != 'done' and sell_order.seller_id != 0:
                if verbose:
                    print('Unfullfilled sell order: ', 'Seller: ', sell_order.seller_id, ' Amount: ', sell_order.amount, ' Price: ', sell_order.price)
                #sell to central agent
                central_agent.current_energy += sell_order.amount

                #update funds
                central_agent.funds -= sell_order.amount * 0.3

                seller = agent_list[sell_order.seller_id]
                seller.set_own_enery(seller.current_energy - sell_order.amount)
                seller.funds += sell_order.amount * 0.3

                sold_price_list.append(0.3)
                sold_amount_list.append(sell_order.amount)
                
                sell_order.amount = 0
                sell_order.type = 'done'

        #calculate average price
        avg_price = 0
        for i in range(len(sold_price_list)):
            avg_price += sold_price_list[i]*sold_amount_list[i]

        avg_price = avg_price / sum(sold_amount_list) if sum(sold_amount_list) > 0 else 0
        avg_price_list.append(avg_price)

        #funds 
        funds_list.append(sum([agent.funds for agent in agent_list])/ n_agents)

        

        #check if everyone is satisfied
        if verbose:
            for i in range(n_agents):
                if agent_list[i].current_energy < agent_list[i].own_demand:
                    print('Agent id: ', agent_list[i].id, ' not satisfied')
                else:
                    print('Agent id: ', agent_list[i].id, ' satisfied')
        
        

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

    plt.title(f' n_agents = {n_agents}, avg_re = {np.mean([agent.re_sources for agent in agent_list])}, avg_de = {np.mean([agent.own_demand for agent in agent_list])}')

    plt.savefig('output.png')

    fig2 = plt.figure()
    plt.plot(funds_list)
    plt.title('Funds over time')
    plt.xlabel('Days')
    plt.ylabel('Funds')
    plt.savefig('output_funds.png')










if __name__ == '__main__':
    main()

'''
TODO:
- move selling price function to agent
- determine initial conditions
- add separate central agent class (or just label?)
- fix print statements
- individualise energy production or not?
- fix multi-buy bug
- fix negative energy bug
'''