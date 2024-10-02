from enum import Enum


class OrderType(Enum):
    BUY = "buy"
    SELL = "sell"
    DONE = "done"
    

class HouseType(Enum):
    TERRACED_HOUSE = "terraced_house"
    DETACHED_HOUSE = "detached_house"
    SEMI_DETACHED_HOUSE = "semi_detached_house"
    MULTI_FAMILY_HOUSE = "multi_family_house"