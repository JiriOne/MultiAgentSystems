"""
Initializes the enums for the order type and house type.
"""


from enum import Enum

# Enum for the order type
class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    DONE = "done"
    
# Enum for the house type
class HouseType(Enum):
    TERRACED_HOUSE = "terraced_house"
    DETACHED_HOUSE = "detached_house"
    SEMI_DETACHED_HOUSE = "semi_detached_house"
    MULTI_FAMILY_HOUSE = "multi_family_house"