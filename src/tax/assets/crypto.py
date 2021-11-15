from .assets import Assets


class Crypto(Assets):
    def process_transaction(self, item: dict) -> tuple:
        # Set defaults
        transaction_type = 'unbekannt'

        # Classify each transaction
        # (1) Transfers
        if item['Transaction Type'] == 'transfer':
            transaction_type = 'erhalten'

            if item['Asset'] == 'BEST':
                transaction_type = 'Rewards'

            direction = 'in'

        # (2) Purchases & sales, deposits & withdrawals
        if item['Transaction Type'] in self.transaction_types:
            transaction_type = self.transaction_types[item['Transaction Type']]

            if item['Transaction Type'] in ['buy', 'deposit']:
                direction = 'in'

            if item['Transaction Type'] in ['sell', 'withdrawal']:
                direction = 'out'

        return (direction, transaction_type)
