

def resolve_price(pricing_model, sdr=None):
    # Check if the price is pay per use
    if sdr != None:
        pass
    # If pay per use extract the price part
    # Calculate the price
    # If not pay per use aggrgate payments and suscriptions

    price = 0
    if 'single_payment' in pricing_model:
        for payment in pricing_model['single_payment']:
            # FIXME currency value can only be euros in a first version
            price = price + float(payment['value'])

    if 'subscription' in pricing_model:
        price = price + float(payment['value'])

    return price
