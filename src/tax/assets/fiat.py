from .assets import Assets


class Fiat(Assets):
    def extract_assets(self, csv_data: list, asset_list: list) -> tuple:
        # Create data array
        result = []

        fiat_paid = 0.00

        for asset in asset_list:
            amount = 0.00

            for item in csv_data:
                # Skip non-compliant assets
                if item['Asset'] != asset:
                    continue

                # Normalize values
                # (1) Fiat amount
                if item['Amount Fiat'] == '-':
                    item['Amount Fiat'] = '0.00'

                # (2) Fee
                if item['Fee'] == '-':
                    item['Fee'] = '0.00'

                # Gather transactions
                transaction = item['Transaction Type']

                # (1) Buying
                if transaction == 'buy':
                    amount += float(item['Amount Fiat'])

                # (2) Selling
                if transaction == 'sell':
                    amount -= float(item['Amount Fiat'])

                # (3) Depositing
                if transaction == 'deposit':
                    amount += float(item['Amount Fiat'])

                # (4) Withdrawing
                if transaction == 'withdrawal':
                    amount -= float(item['Amount Fiat'])

                # (5) Transfering
                if transaction == 'transfer':
                    if item['In/Out'] == 'outgoing':
                        amount -= float(item['Amount Fiat'])

                    if item['In/Out'] == 'incoming':
                        amount += float(item['Amount Fiat'])

                # Take fees into account
                if float(item['Fee']) >= 0.00:
                    amount -= float(item['Fee'])

            # Format asset amount
            amount = '{:.2f}'.format(amount)

            # If everything checks out ..
            if float(amount) > 0:
                # .. add asset
                result.append({
                    'asset': asset,
                    'amount': amount,
                })

        return (result, fiat_paid)


    def process_transaction(self, item: dict) -> tuple:
        # Set defaults
        transaction_type = 'unbekannt'

        # Classify each transaction
        # (1) Transfers
        if item['Transaction Type'] == 'transfer':
            transaction_type = self.transaction_types[item['In/Out']]

            if item['In/Out'] == 'incoming':
                direction = 'in'

            if item['In/Out'] == 'outgoing':
                direction = 'out'

        # (2) Purchases & sales, deposits & withdrawals
        if item['Transaction Type'] in self.transaction_types:
            transaction_type = self.transaction_types[item['Transaction Type']]

            if item['Transaction Type'] in ['buy', 'deposit']:
                direction = 'in'

            if item['Transaction Type'] in ['sell', 'withdrawal']:
                direction = 'out'

        return (direction, transaction_type)
