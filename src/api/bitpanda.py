import asyncio
import functools

import httpx


class Bitpanda:
    """
    Wrapper for the Bitpanda API.
    """

    page_size = 200


    def __init__(self, api_key: str = ''):
        self.api_key = api_key


    # API METHODS

    async def make_request(self, path: str, method: str = 'get') -> dict:
        """
        Internal implementation to make a request to the Bitpanda API.
        """

        # Build request URL
        url = 'https://api.bitpanda.com/v1/' + path

        async with httpx.AsyncClient() as client:
            response = await client.request(method, url, headers={'X-API-KEY': self.api_key})

        if not response or response.status_code != 200:
            raise Exception('Invalid or empty response.')

        return response.json()


    async def get_trades(self) -> list:
        """
        Get all trades made by the user, sorted by date.
        """

        trades = []
        has_more = True

        path = 'trades?page=1&page_size={}'.format(self.page_size)

        try:
            while has_more:
                result = await self.make_request(path)
                trades += [trade['attributes'] for trade in result['data']]

                # Keep fetching trades while there are more pages on the result.
                if 'links' in result and 'next' in result['links']:
                    path = 'trades{}'.format(result['links']['next'])

                else:
                    has_more = False

            # Sort trades (by timestamp)
            trades.sort(key=lambda d: d['time']['unix'])

        except:
            raise

        return trades


    async def get_fiat_transactions(self) -> list:
        """
        Get user's fiat transactions, sorted by date.
        """

        transactions = []
        has_more = True

        path = 'fiatwallets/transactions?page=1&page_size={}'.format(self.page_size)

        try:
            while has_more:
                result = await self.make_request(path)
                transactions += [transaction['attributes'] for transaction in result['data']]

                # Keep fetching transactions while there are more pages on the result.
                if 'links' in result and 'next' in result['links']:
                    path = 'fiatwallets/transactions{}'.format(result['links']['next'])

                else:
                    has_more = False

            transactions.sort(key=lambda d: d['time']['unix'])

        except:
            raise

        return transactions


    async def get_wallets(self) -> list:
        """
        Get list of crypto wallets from the user.
        """

        try:
            wallets = await self.make_request('wallets')

            return [w['attributes'] for w in wallets['data']]

        except:
            raise


    async def get_fiat_wallets(self) -> list:
        """
        Get list of fiat wallets from the user.
        """

        try:
            fiat_wallets = await self.make_request('fiatwallets')

            return [fw['attributes'] for fw in fiat_wallets['data']]

        except:
            raise


    async def get_ticker(self) -> dict:
        """
        Get prices ticker for all available assets.
        """

        try:
            return await self.make_request('ticker')

        except:
            raise


    async def fetch_data(self) -> dict:
        return {
            'ticker': await self.get_ticker(),
            'wallets': await self.get_wallets(),
            'trades': await self.get_trades(),
            'fiat_wallets': await self.get_fiat_wallets(),
            'fiat_transactions': await self.get_fiat_transactions(),
        }


    def get_report(self) -> dict:
        """
        Get a full report by matching wallets, trades and transactions.
        """

        wallets = {}

        best_wallet = {
            'id': '',
            'symbol': '',
            'balance': 0,
            'current_value': 0,
            'total_buy': 0,
            'total_sell': 0,
            'total_fees': 0,
            'buy': [],
            'sell': [],
        }

        total_profit = 0
        total_deposit = 0
        total_withdrawal = 0
        deposit_count = 0
        withdrawal_count = 0
        fiat_balance = 0

        # Get all the necessary data from Bitpanda.
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(self.fetch_data())
        loop.close()

        # Create the resulting wallets array with the correct asset IDs.
        for w in data['wallets']:
            if w['cryptocoin_id'] not in wallets:
                wallet = {
                    'id': w['cryptocoin_id'],
                    'symbol': w['cryptocoin_symbol'],
                    'balance': float(w['balance']),
                    'current_value': 0,
                    'total_buy': 0,
                    'total_sell': 0,
                    'total_fees': 0,
                    'buy': [],
                    'sell': [],
                }

                if w['cryptocoin_id'] not in wallet:
                    wallets[w['cryptocoin_id']] = wallet

                if wallet['symbol'] == 'BEST':
                    best_wallet = wallet

        # Add default OTHER wallet (for uknown transactions).
        wallets['UNKNOWN'] = {
            'id': '-1',
            'symbol': 'UNKNOWN',
            'balance': 0,
            'current_value': 0,
            'total_buy': 0,
            'total_sell': 0,
            'total_fees': 0,
            'buy': [],
            'sell': []
        }

        # Calculate current fiat balance.
        for fw in data['fiat_wallets']:
            if fw['fiat_symbol'] == 'EUR':
                fiat_balance += float(fw['balance'])

            else:
                ref = data['ticker']['USDT'] if 'USDT' in data['ticker'] else data['ticker']['ETH']
                multi = float(ref['EUR']) / float(ref[fw['fiat_symbol']])
                eur_balance = multi * float(fw['balance'])
                fiat_balance += eur_balance

        # Parse fiat transactions and add them to the related wallets.
        for t in data['fiat_transactions']:
            if t['status'] != 'finished':
                continue

            # Calculate total deposit and withdrawals.
            eur_amount = float(t['amount']) * float(t['to_eur_rate'])

            if t['type'] == 'deposit':
                total_deposit += eur_amount
                deposit_count += 1

            if t['type'] == 'withdrawal':
                total_withdrawal += eur_amount
                withdrawal_count += 1

        # Parse trades and add them to the related wallets.
        for t in data['trades']:
            if t['status'] != 'finished':
                continue

            # Add to default wallet if not found.
            if t['cryptocoin_id'] not in wallets:
                t['cryptocoin_id'] = 'UNKNOWN'

            info = {
                'asset_amount': float(t['amount_cryptocoin']),
                'asset_price': float(t['price']),
                'cost': float(t['amount_fiat']),
                'timestamp': int(t['time']['unix'])
            }

            # Buying or selling?
            if t['type'] == 'buy':
                wallets[t['cryptocoin_id']]['buy'].append(info)

            if t['type'] == 'sell':
                wallets[t['cryptocoin_id']]['sell'].append(info)

            # Paid with BEST?
            if t['bfc_used'] and t['best_fee_collection']:
                att = t['best_fee_collection']['attributes']
                info['fee'] = float(att.bfc_market_value_eur) if 'bfc_market_value_eur' in att else 0
                info['best_amount'] = float(att['bfc_market_value_eur']) / float(att['best_current_price_eur'])

                best_wallet['sell'].append({
                    'asset_amount': info['best_amount'],
                    'asset_price': float(att['best_current_price_eur']),
                    'cost': 0,
                    'timestamp': int(t['time']['unix'])
                })

            else:
                info['fee'] = float(t['fee']) if 'fee' in t else 0

            wallets[t['cryptocoin_id']]['total_fees'] += info['fee']

        # Iterate wallets to calculate trading profits or losses.
        for wallet in wallets.values():
            # No transactions? Stop here.
            if not wallet['buy'] and not wallet['sell']:
                continue

            # Purchased assets? Calculate total in fiat.
            if wallet['buy']:
                wallet['total_buy'] = sum([t['cost'] for t in wallet['buy']])

            # Solds assets? Calculate total in fiat.
            if wallet['sell']:
                wallet['total_sell'] = sum([t['cost'] for t in wallet['sell']])

            # How many assets were bought and sold? Calculate balance.
            sell_count = sum([t['asset_amount'] for t in wallet['sell']])

            wallet['current_value'] = float(data['ticker'][wallet['symbol']]['EUR']) * wallet['balance'] if wallet['balance'] > 0 and wallet['symbol'] in data['ticker'] else 0

            # Sold assets?
            if sell_count > 0:
                arr_price_paid = []
                match_buy_count = 0
                i = 0

                # Calculate how much was paid for the assets that were sold.
                while match_buy_count < sell_count and i in wallet['buy']:
                    trade = wallet['buy'][i]

                    amount = trade['asset_amount']
                    match_buy_count += amount

                    # Reached the amount sold? Remove extra so we can properly calculate the average.
                    if match_buy_count > sell_count:
                        amount -= match_buy_count - sell_count

                    arr_price_paid.append([amount, trade['cost'] / trade['asset_amount']])
                    i += 1

                # Total price paid for the sold assets.
                price_paid = self.weighted_avg(sell_count, arr_price_paid) * sell_count
                wallet['sell_profit'] = wallet['total_sell'] - pric_paid - wallet['total_fees']
                total_profit += wallet['sell_profit']

        # Filter only wallets that had transactions.
        active_wallets = [w for w in wallets.values() if w['buy'] or w['sell']]

        # The BEST profit takes into account trade fees paid with BEST, so BEST usage was essentially counted twice.
        # Here we add these feed back to the total profit.
        best_wallet['sell'] = [t for t in best_wallet['sell'] if t['cost'] > 0]
        total_profit += sum([w['total_fees'] for w in active_wallets])

        return {
            'wallets': active_wallets,
            'profit': total_profit,
            'deposit': total_deposit,
            'deposit_count': deposit_count,
            'withdrawal': total_withdrawal,
            'withdrawal_count': withdrawal_count,
            'fiat_balance': fiat_balance
        }


    # HELPERS

    def weighted_avg(self, total: int, positions: list) -> int:
        """
        Calculate the weighted price average based on volume.
        """

        if total <= 0:
            return 0

        if len(positions) == 1:
            return positions[0][1]

        return functools.reduce(lambda acc, next: acc + next[0] * next[1], positions, 0) / totals
