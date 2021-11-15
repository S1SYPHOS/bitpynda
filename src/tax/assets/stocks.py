from datetime import datetime

from .assets import Assets


class Stocks(Assets):
    def process_transaction(self, item: dict) -> tuple:
        # Set defaults
        transaction_type = 'unbekannt'

        # Classify each transaction
        # (1) Transfers
        if item['Transaction Type'] == 'transfer':
            transaction_type = 'erhalten'

            direction = 'in'

        # (2) Purchases & sales, deposits & withdrawals
        if item['Transaction Type'] in self.transaction_types:
            transaction_type = self.transaction_types[item['Transaction Type']]

            if item['Transaction Type'] in ['buy', 'deposit']:
                direction = 'in'

            if item['Transaction Type'] in ['sell', 'withdrawal']:
                direction = 'out'

        return (direction, transaction_type)


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
