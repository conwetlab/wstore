CURRENCIES = {
    'EUR': '1',
    'GBP': '2',
    'BRL': '3',
    'ARS': '4',
    'MXN': '5',
    'CLP': '6',
    'PEN': '7',
    'VEF': '8',
    'COP': '9',
    'USD': '10',
    'NIO': '11',
    'GTQ': '12',
    'SVC': '13',
    'PAB': '14',
    'UYU': '15',
    'MYR': '16',
    'NOK': '17',
    'HUF': '18'
}

COUNTRIES = {
    'ES': '1',
    'GB': '2',
    'DE': '3',
    'MX': '4',
    'CL': '5',
    'AR': '6',
    'PE': '7',
    'VE': '8',
    'CO': '9',
    'EC': '10',
    'NI': '11',
    'GT': '12',
    'SV': '13',
    'PA': '14',
    'UY': '15',
    'BR': '16',
    'MY': '17',
    'NO': '18',
    'HU': '19'
}


def get_curency_code(curr):

    try:
        code = CURRENCIES[curr]
    except:
        raise Exception('Invalid currency code')

    return code


def get_country_code(country):

    try:
        code = COUNTRIES[country]
    except:
        raise Exception('Invalid country code')

    return code
