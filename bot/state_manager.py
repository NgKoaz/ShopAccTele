class StateManager:
    """ PURCHASE PRODUCT CONVERSATION """
    CHOOSE_PURCHASE_CATEGORY, CHOOSE_PURCHASE_QUANTITY, CONFIRM_PURCHASE = range(1000, 1003)

    """ ADMIN ADD CATEGORY """
    GET_CATEGORY_FILE = range(10000, 10001)

    """ ADMIN DELETE CATEGORY """
    CHOOSE_DELETE_CATEGORY, CONFIRM_DELETE_CATEGORY = range(10500, 10502)

    """ ADMIN ADD PRODUCT """
    SELECT_CATEGORY_FOR_PRODUCT, SEND_PRODUCT = range(11000, 11002)