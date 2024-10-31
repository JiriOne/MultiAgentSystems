""" 
Order class 
"""
class Order():
    def __init__(self, agent_id, amount, price, order_type):
        self.agent_id = agent_id
        self.amount = amount
        self.price = price
        self.type = order_type