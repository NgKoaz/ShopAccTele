class NotEnoughBalanceError(Exception):
    pass

class NegativeBalanceError(Exception):
    """ Raise when user's balance is negative """
    pass