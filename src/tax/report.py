import os
from datetime import datetime
from operator import itemgetter

import click
import pandas as pd

from .assets.fiat import Fiat
from .assets.metal import Metal
from .assets.crypto import Crypto
from .assets.stocks import Stocks

from .pdf import Document
from ..utils import slugify


# Define globally ..
# (1) .. current date
today = datetime.today()

# (2) .. sort order 'by date'
by_date = itemgetter('Datum')

# (3) .. asset classes
classes = {
    'Fiat': 'fiat',
    'Metal': 'metal',
    'Cryptocurrency': 'crypto',
    'Stock (derivative)': 'stocks',
}

# (4) .. asset instances
instances = {
    'fiat': Fiat(),
    'metal': Metal(),
    'crypto': Crypto(),
    'stocks': Stocks(),
}


class Report:
    # Define (level of) verbosity
    verbose = 0


    # Define user information
    user_info = {
        'name': 'Max Mustermann',
        'street': 'Musterstraße 11',
        'city': '12345 Musterstadt',
    }


    # Define categories
    categories = {
        'fiat': 'Währungen',
        'metal': 'Edelmetalle',
        'crypto': 'Kryptowährungen',
        'stocks': 'Aktien',
    }


    # Define tax guidelines
    tax_guidelines = {
        'metal': 'Für Edelmetalle in Deutschland (steuerfrei bei Haltefrist über einem Jahr)',
        'crypto': 'Für Kryptowährungen in Deutschland (steuerfrei bei Haltefrist über einem Jahr)',
        'stocks': 'Für Aktien in Deutschland (jede Veräußerung muss versteuert werden)',
    }


    # Define wallets for receiving donations
    donations = [
        {
            'title': 'Bitcoin',
            'address': 'bc1q09w7rac565vr7dtqvc2j6sv9f8fa4mscv9ct0s',
        },
        {
            'title': 'IOTA',
            'address': 'iota1qqffgg8cmwlh3dqss7s2u6fsl83007505j98zjpqjq9je3ca30cfccrs2uy',
        },
        {
            'title': 'BEST',
            'address': '0x34Fc219cDE52D31BE23D6fA83448B2d1903Df4FD',
        },
    ]


    def __init__(self, input_file: str) -> None:
        # Determine number of lines to be skipped
        # (1) Load data from file
        with open(input_file, 'r') as file:
            data = file.readlines()

        # (2) Set default
        skiprows = 6

        # (3) Loop over lines ..
        for index, line in enumerate(data):
            # .. if header line is found ..
            if 'Transaction ID' in line:
                # .. store lines to be skipped
                skiprows = index

                # .. abort loop
                break

        # Load CSV data
        self.csv_data = pd.read_csv(input_file, skiprows=skiprows).to_dict('records')

        if self.verbose > 1: click.echo('csv_data: {}'.format(csv_data))


    def extract_assets(self) -> tuple:
        # Create set for each asset class
        assets = {asset_class: set() for asset_class in instances.keys()}

        # Loop over CSV data
        for item in self.csv_data:
            # Take precautions ..
            if item['Asset class'] not in classes:
                # .. skipping unknown asset classes
                continue

            # Add asset to corresponding listing
            assets[classes[item['Asset class']]].add(item['Asset'])

        # Sort assets (by name)
        for asset, asset_set in assets.items():
            assets[asset] = sorted(list(asset_set))

        if self.verbose > 1:
            click.echo('assets: {}'.format(assets))

        # Create data array for net worth
        wealth = {}

        # Determine total of `fiat` paid for assets
        fiat_paid = 0

        for mode, asset_list in assets.items():
            # Initialize object
            obj = instances[mode]

            # Extract asset quantities & paid amount of `fiat`
            quantities, paid = obj.extract_assets(self.csv_data, asset_list)

            # Store asset quantities
            wealth[mode] = quantities

            # Add paid amount of `fiat`
            fiat_paid += paid

        if self.verbose > 1: click.echo('fiat_paid: {}'.format(fiat_paid))

        # Example:
        #
        # wealth['fiat'] = [
        #    {'asset': 'CHZ', 'amount': '-0.00'},
        #    {'asset': 'USD', 'amount': '985.00'},
        #    {'asset': 'EUR', 'amount': '-1465.00'},
        # ]

        # Normalize `fiat` amount
        for item in wealth['fiat']:
            # Skip fiat currencies other than €uro
            if item['asset'] != 'EUR':
                continue

            # Set default
            fiat_amount = fiat_paid + float(item['amount'])

            # If negative (even '-0.00') ..
            if not fiat_amount > 0:
                # .. fallback to zero
                fiat_amount = 0

            # Store formattet `fiat` amount
            item['amount'] = '{:.2f}'.format(fiat_amount)

        if self.verbose > 1:
            click.echo('wealth: {}'.format(wealth))

        return (assets, wealth)


    def process_transactions(self) -> dict:
        # Create data array
        transactions = {
            'fiat': {
                'in': [],
                'out': [],
            },
            'metal': {
                'in': [],
                'out': [],
            },
            'crypto': {
                'in': [],
                'out': [],
            },
            'stocks': {
                'in': [],
                'out': [],
            },
        }

        for item in self.csv_data:
            # Determine date & time of transaction
            date = datetime.strptime(item['Timestamp'][:10], '%Y-%m-%d')
            time = datetime.strptime(item['Timestamp'][11:19], '%H:%M:%S')

            # Format date & time
            date_string = '{} {}'.format(date.date(), time.time())

            if item['Asset class'] == 'Fiat':
                # Determine direction & transaction type
                direction, transaction_type = instances['fiat'].process_transaction(item)

                # Append transaction data accordingly
                transactions['fiat'][direction].append({
                    'Datum': date_string,
                    'Transaktion': transaction_type,
                    'Betrag': item['Amount Fiat'],
                    'Asset': item['Fiat'],
                    'Gebühren': item['Fee'],
                })

            else:
                # Determine current mode
                mode = classes[item['Asset class']]

                # Determine direction & transaction type
                direction, transaction_type = instances[mode].process_transaction(item)

                # Append transaction data accordingly
                transactions[mode][direction].append({
                    'Datum': date_string,
                    'Transaktion': transaction_type,
                    'Betrag': item['Amount Fiat'],
                    'Asset Menge': item['Amount Asset'],
                    'Asset Preis': item['Asset market price'],
                    'Asset': item['Asset'],
                    'Gebühren': item['Fee'],
                })

        # Process transactions
        for mode, transaction_data in transactions.items():
            # (1) Sort them (by date)
            # TODO: Investigate, as exported data should be sorted already
            for direction, data in transaction_data.items():
                transactions[mode][direction] = sorted(data, key=by_date)

            # (2) Build extra column, combining incoming/outgoing transactions per asset
            transactions[mode]['all'] = sorted(transactions[mode]['in'] + transactions[mode]['out'], key=by_date)

        if self.verbose > 1:
            click.echo('transactions: {}'.format(transactions))

        return transactions


    def calculate_margins(self, assets: dict, transactions: dict) -> tuple:
        # Create data arrays
        # (1) Balance
        balance = {
            'metal': [],
            'crypto': [],
            'stocks': [],
        }

        # (2) Taxes
        taxes = {
            'metal': [],
            'crypto': [],
            'stocks': [],
        }

        # (3) Portfolio
        portfolio = {
            'metal': [],
            'crypto': [],
            'stocks': [],
        }

        for mode in balance.keys():
            # Create data array
            balance_taxes = []

            for asset in assets[mode]:
                hint = False

                buffer = {
                    'in': [],
                    'out': [],
                }

                # Processing incoming transactions
                for item in transactions[mode]['in']:
                    if item['Asset'] != asset:
                        continue

                    if item['Betrag'] == '-':
                        item['Betrag'] = 0

                    if item['Gebühren'] == '-':
                        item['Gebühren'] = 0

                    if item['Transaktion'] == 'empfangen':
                        hint = True

                    buffer['in'].append({
                        'Datum': item['Datum'],
                        'Transaktion': item['Transaktion'],
                        'Betrag': '{:.2f}'.format(float(item['Betrag'])),
                        'Asset Menge': '{:.6f}'.format(float(item['Asset Menge'])),
                        'Asset Preis': '{:.2f}'.format(float(item['Asset Preis'])),
                        'Asset': item['Asset'],
                        'Gebühren': '{:.6f}'.format(float(item['Gebühren'])),
                    })

                # Processing outgoing transactions
                for item in transactions[mode]['out']:
                    if item['Asset'] != asset:
                        continue

                    if item['Betrag'] == '-':
                        item['Betrag'] = 0

                    if item['Gebühren'] == '-':
                        item['Gebühren'] = 0

                    buffer['out'].append({
                        'Datum': item['Datum'],
                        'Transaktion': item['Transaktion'],
                        'Betrag': '{:.2f}'.format(float(item['Betrag'])),
                        'Asset Menge': '{:.6f}'.format(float(item['Asset Menge'])),
                        'Asset Preis': '{:.2f}'.format(float(item['Asset Preis'])),
                        'Asset': item['Asset'],
                        'Gebühren': '{:.6f}'.format(float(item['Gebühren']))
                    })

                # Sort buffered transactions
                for direction, data in buffer.items():
                    buffer[direction] = sorted(data, key=by_date)

                if self.verbose > 1: click.echo('buffer: {}'.format(buffer))

                assets_balance = 0
                buffer_balance = 0

                for item in buffer['out']:
                    asset_balance = 0

                    if item['Asset'] == asset:
                        days = datetime.strptime(item['Datum'], '%Y-%m-%d %H:%M:%S') - datetime.strptime(buffer['in'][0]['Datum'], '%Y-%m-%d %H:%M:%S')
                        year = datetime.strptime(item['Datum'], '%Y-%m-%d %H:%M:%S')

                        if float(item['Asset Menge']) == 0:
                            item['Asset Menge'] = item['Gebühren']

                        if buffer['in']:
                            if float(item['Asset Menge']) > float(buffer['in'][0]['Asset Menge']):
                                while float(item['Asset Menge']) > float(buffer['in'][0]['Asset Menge']):
                                    if self.verbose > 1: click.echo('1: len(buffer["in"]): {}'.format(len(buffer['in'])))

                                    if item['Transaktion'] == 'Verkauf':
                                        buffer_balance += (float(buffer['in'][0]['Asset Menge']) * float(item['Asset Preis'])) - float(buffer['in'][0]['Betrag'])

                                    item['Betrag'] = '{:.2f}'.format((float(item['Asset Menge']) - float(buffer['in'][0]['Asset Menge'])) * float(item['Asset Preis']))
                                    item['Asset Menge'] = '{:.6f}'.format(float(item['Asset Menge']) - float(buffer['in'][0]['Asset Menge']))

                                    if buffer['in']:
                                        del buffer['in'][0]

                                    else:
                                        buffer['in'][0]['Betrag'] = 0
                                        buffer['in'][0]['Asset Menge'] = 0

                                    if float(item['Asset Menge']) < 0:
                                        if self.verbose > 1: click.echo('break because of Amount')
                                        break

                                    if self.verbose > 1: click.echo('2: len(buffer["in"]): {}'.format(len(buffer['in'])))

                                    if not buffer['in']:
                                        if self.verbose > 1: click.echo('break because of length')
                                        break

                                asset_balance += buffer_balance

                            if buffer['in']:
                                if float(item['Asset Menge']) == float(buffer['in'][0]['Asset Menge']):
                                    if item['Transaktion'] == 'Verkauf':
                                        asset_balance += float(item['Betrag']) - float(buffer['in'][0]['Betrag'])

                                    if buffer['in']:
                                        del buffer['in'][0]

                                    else:
                                        buffer['in'][0]['Betrag'] = 0
                                        buffer['in'][0]['Asset Menge'] = 0

                                elif float(item['Asset Menge']) < float(buffer['in'][0]['Asset Menge']):
                                    buffer['in'][0]['Betrag'] = '{:.2f}'.format((float(buffer['in'][0]['Asset Menge']) - float(item['Asset Menge'])) * float(buffer['in'][0]['Asset Preis']))
                                    buffer['in'][0]['Asset Menge'] = '{:.6f}'.format((float(buffer['in'][0]['Asset Menge']) - float(item['Asset Menge'])))

                                    if item['Transaktion'] == 'Verkauf':
                                        asset_balance += float(item['Betrag']) - (float(buffer['in'][0]['Asset Preis']) * float(item['Asset Menge']))

                    assets_balance += asset_balance

                    balance_taxes.append({
                        'Asset': '{}*'.format(asset) if hint else asset,
                        'HODL': days.days,
                        'Jahr': year.year,
                        'winLoss': '{:.2f}'.format(asset_balance),
                    })

                if buffer['in']:
                    for item in buffer['in']:
                        if float(item['Asset Menge']) > 0:
                            portfolio[mode].append(item)

                balance[mode].append({
                    'Asset': asset,
                    'winLoss': '{:.2f}'.format(assets_balance),
                })

                if assets_balance != 0:
                    taxes[mode] = (instances[mode].calculate_taxes(asset, balance_taxes))

                else:
                    taxes[mode].append({
                        'Asset': asset,
                        'Verkaufsjahr': 1990,
                        'Betrag': 0.00,
                    })

            # Sort taxes (by date of purchase & asset name)
            taxes[mode].sort(key=itemgetter('Verkaufsjahr', 'Asset'))

        if self.verbose > 1:
            click.echo('balance: {}'.format(balance))
            click.echo('taxes: {}'.format(taxes))
            click.echo('portfolio: {}'.format(portfolio))

        return (balance, taxes, portfolio)


    def get_tax_years(self, taxes: dict) -> set:
        tax_years = set()

        for mode in taxes.keys():
            for item in taxes[mode]:
                # Skip test entries
                if item['Verkaufsjahr'] == 1990:
                    continue

                tax_years.add(item['Verkaufsjahr'])

        if self.verbose > 1:
            click.echo('tax_years: {}'.format(tax_years))

        return tax_years


    def render(self, output_file: str, title: str = 'Bitpanda Report'):
        # Determine available assets
        if self.verbose > 0: click.echo('Extracting assets ..')
        assets, wealth = self.extract_assets()

        # Process transactions
        if self.verbose > 0: click.echo('Processing transactions ..')
        transactions = self.process_transactions()

        # Calculate invested capital
        if self.verbose > 0: click.echo('Calculating wins & losses ..')
        balance, taxes, portfolio = self.calculate_margins(assets, transactions)

        # Set up PDF generation
        if self.verbose > 0: click.echo('Generating PDF report ..')
        pdf = Document()

        # Create cover page (portfolio overview, pie charts included)
        if self.verbose > 0: click.echo('Creating cover page ..')
        pdf.add_cover_page(assets, wealth, self.categories, self.user_info)

        # Create `fiat` transactions pages
        if self.verbose > 0: click.echo('Creating fiat transaction pages ..')
        pdf.add_fiat_pages(assets['fiat'], transactions['fiat']['all'])

        # Create other transactions page
        if self.verbose > 0: click.echo('Creating other transaction pages ..')
        pdf.add_transaction_pages(assets, transactions, balance, self.categories)

        # Create taxes overview page
        if self.verbose > 0: click.echo('Creating taxes page ..')
        pdf.add_taxes_page(self.tax_guidelines, taxes)

        # Create tax pages for each year
        if self.verbose > 0: click.echo('Creating tax pages per year ..')
        pdf.add_tax_pages(self.get_tax_years(taxes), taxes, wealth['fiat'][0], self.categories)

        # Create portfolio page
        if self.verbose > 0: click.echo('Creating portfolio pages ..')
        pdf.add_portfolio_pages(portfolio, wealth, self.categories)

        # If enabled ..
        if self.donations:
            # .. create donations page (including QR code images)
            if self.verbose > 0: click.echo('Creating donations page ..')
            pdf.add_donations_page(self.donations)

        # Save PDF report
        if self.verbose > 0: click.echo('Exporting PDF report ..')
        pdf.export('{}.pdf'.format(output_file))
