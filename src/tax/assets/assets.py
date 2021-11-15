from datetime import datetime


class Assets():
    # Define transaction labels
    transaction_types = {
        # (1) Transaction types
        'buy': 'Kauf',
        'sell': 'Verkauf',
        'deposit': 'Einzahlung',
        'withdrawal': 'Auszahlung',

        # (2) Transfer types
        'incoming': 'Empfangen',
        'outgoing': 'Versendet',
    }


    def extract_assets(self, csv_data: list, asset_list: list) -> tuple:
        # Create data array
        result = []

        # Determine amount of `fiat` paid for assets
        fiat_paid = 0.00

        for asset in asset_list:
            amount = 0.00

            for item in csv_data:
                # Skip non-compliant assets
                if item['Asset'] != asset:
                    continue

                # Normalize values
                # (1) Asset amount
                if item['Amount Asset'] == '-':
                    item['Amount Asset'] = '0.00'

                # (2) Fee
                if item['Fee'] == '-':
                    item['Fee'] = '0.00'

                # Gather transactions
                transaction = item['Transaction Type']

                # (1) Buying
                if transaction == 'buy':
                    amount += float(item['Amount Fiat'])
                    fiat_paid -= float(item['Amount Fiat'])

                # (2) Selling
                if transaction == 'sell':
                    amount -= float(item['Amount Fiat'])
                    fiat_paid += float(item['Amount Fiat'])

                # (3) Depositing
                if transaction == 'deposit':
                    amount += float(item['Amount Fiat'])

                # (4) Withdrawing
                if transaction == 'withdrawal':
                    amount -= float(item['Amount Fiat'])

                # (5) Transfering
                if transaction == 'transfer':
                    pass

                # Take fees into account
                if float(item['Fee']) >= 0.00:
                    amount -= float(item['Fee'])

            # Format asset amount
            amount = '{:.6f}'.format(amount)

            # If everything checks out ..
            if float(amount) > 0:
                # .. add asset
                result.append({
                    'asset': asset,
                    'amount': amount,
                })

        return (result, fiat_paid)


    def calculate_taxes(self, asset: str, balance_taxes: list) -> list:
        # Set initial values
        year_sold = ''
        to_pay = 0

        # Create buffer
        buffer = ''

        # Create data array
        taxes = []

        for item in balance_taxes:
            buffer = item['Asset']

            if item['Asset'][-1] == '*':
                buffer = item['Asset'][:-1]

            if asset != buffer:
                continue

            if int(item['HODL']) <= 365:
                if item['Jahr'] == year_sold:
                    to_pay += float(item['winLoss'])
                    continue

                if to_pay != 0:
                    taxes.append({
                        'Asset': item['Asset'],
                        'Verkaufsjahr': year_sold,
                        'Betrag': to_pay,
                    })

                year_sold = item['Jahr']
                to_pay = float(item['winLoss'])

        if to_pay != 0:
            taxes.append({
                'Asset': item['Asset'],
                'Verkaufsjahr': year_sold,
                'Betrag': to_pay,
            })

        return taxes
