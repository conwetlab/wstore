

def resolve_price(pricing_model, sdr=None):

    # Check if the price is pay per use
    if sdr != None:
        # Check the unit included in the SDR
        found = False
        i = 0
        # Limited to one part of each pay per use unit
        while not found and i < len(pricing_model['pay_per_use']):
            if pricing_model['pay_per_use'][i]['unit'] == sdr['unit'].lower():
                found = True
                part = pricing_model['pay_per_use'][i]
            i = i + 1

        if not found:
            raise Exception('The provided unit is not included in the offering pricing model')

        # Get the value per unit and the units consumed
        per_unit = float(part['value'])
        units = float(sdr['value'])

        # Calculate the price
        price = {
            'price': units*per_unit,
            'part': part
        }

    else:
        price = 0
        if 'single_payment' in pricing_model:
            for payment in pricing_model['single_payment']:
                # FIXME currency value can only be euros in a first version
                price = price + float(payment['value'])

        if 'subscription' in pricing_model:
            for payment in pricing_model['subscription']:
                price = price + float(payment['value'])

    return price
