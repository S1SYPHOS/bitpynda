import os
import glob
from datetime import datetime

import click
from fpdf import FPDF

from ..utils import create_path, slugify


# Define globally ..
# (1) .. current date
today = datetime.today()

# (2) .. dimensions (A4)
pdf_width = 210
pdf_height = 297


class PDF(FPDF):
    # Date format
    date_format = '%d.%m.%Y'


    def header(self) -> None:
        # TODO: Insert logo
        # self.image('fox_face.png', 10, 8, 25)

        # Set font family
        self.set_font('times', 'B', 20)

        # Insert title
        self.cell(0, 0, 'Bitpanda Report', ln=True, align='C')

        # Add line break
        self.ln(10)


    def footer(self) -> None:
        # Set footer position
        self.set_y(-15)

        # Set font family
        self.set_font('times', 'I', 10)

        # Insert date
        self.cell(0, 10, datetime.today().strftime(self.date_format), align='L')

        # Insert page number
        self.cell(0, 10, '{}/nb'.format(self.page_no()), align='R')


class Document:
    # Define ..
    # (1) .. huge amounts of ..
    whitespace = '                                       '


    # (2) .. a ridiculously ..
    large_line = '_____________________________________________________________________________________________________________'


    def __init__(self, title: str = 'Bitpanda Report') -> None:
        # For reference:
        #
        # Layout: 'P'ortrait or 'L'andscape
        # Unit: 'mm', 'cm' or 'in'
        # Format: 'A3', 'A4', 'A5', 'Letter', 'Legal' or (100, 150)

        # Set up document
        # (1) Create '(F)PDF' object
        self.pdf = PDF('P', 'mm', 'A4')

        # (2) Enable page numbers
        self.pdf.alias_nb_pages(alias='nb')

        # (3) Set automatic page break
        self.pdf.set_auto_page_break(auto=True, margin=15)

        # (4) Set document title
        self.pdf.set_title(title)

        # Define temporary directory
        # (1) Determine application home
        self.app_dir = click.get_app_dir('bitpanda')

        # (2) Attempt to create directory ..
        if not create_path(self.app_dir):
            # .. otherwise raise exception
            raise Exception('Unable to create app_dir "{}"'.format(self.app_dir))


    def add_cover_page(self, assets: dict, wealth: dict, categories: dict, user_info: dict) -> None:
        # Import dependency
        import matplotlib.pyplot as plt

        # Create data array for pie charts
        png_files = {}

        # Loop over categories
        for mode, category in categories.items():
            asset_list = []

            for asset in wealth[mode]:
                if abs(float(asset['amount'])) != 0:
                    asset_list.append(asset)

            # If assets unavailable ..
            if not asset_list:
                # .. proceed
                continue

            # Generate pie chart
            x_list = []
            labels = []

            for index, asset in enumerate(asset_list):
                x_list.append(asset['amount'])
                labels.append('{}\n({})'.format(asset['asset'], asset['amount']))

            # Make it round
            plt.axis('equal')

            # Set filename
            png_file = os.path.join(self.app_dir, '{}.png'.format(slugify(category)))

            # Create pie chart
            plt.pie(x_list, labels=labels, autopct='%1.1f%%', normalize=True)
            plt.title(category)
            plt.savefig(png_file, bbox_inches='tight')
            plt.close()

            # Store filename
            png_files[mode] = png_file

        # Add a page
        self.pdf.add_page()

        # Specify font family & size
        # fonts ('times', 'courier', 'helvetica', 'symbol', 'zpfdingbats')
        # 'B' (bold), 'U' (underline), 'I' (italic), '' (regular), combination (i.e. ('BU'))
        self.pdf.set_font('times', '', 14)
        self.pdf.ln(5)

        # Add text
        # w = width
        # h = height
        # txt = your text
        # ln (0 False; 1 True - move cursor down to next line)
        # border (0 False; 1 True - add border around cell)

        # Print user information
        self.pdf.cell(40, 8, user_info['name'], ln=True, border=False)
        self.pdf.cell(40, 8, user_info['street'], ln=True)
        self.pdf.cell(40, 8, user_info['city'], ln=True)
        self.pdf.ln(6)

        # Print traded assets
        # (1) Heading
        self.pdf.set_font('times', 'B', 10)
        self.pdf.cell(40, 8, 'Du hast gehandelt mit:\n', ln=True)
        self.pdf.ln(3)

        for mode, category in categories.items():
            # (2) Subheading & asset names
            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(40, 8, '{}\n'.format(category), ln=True)
            self.pdf.set_font('times', '', 10)

            # If assets available ..
            if assets[mode]:
                # .. print them
                self.pdf.cell(40, 8, '{}\n'.format(', '.join(assets[mode])), ln=True)

            # .. otherwise ..
            else:
                # .. print hyphen
                self.pdf.cell(40, 8, '-\n', ln=True)

        # Dimensions (by number of images & corresponding indices)
        dimensions = {
            1: {
                0: [pdf_width / 2 - 75, 140, 150],
            },
            2: {
                0: [15, 140, 100],
                1: [pdf_width - 115, 140, 100],
            },
            3: {
                0: [15, 140, 70],
                1: [pdf_width - 85, 140, 70],
                2: [pdf_width / 2 - 35, 200, 70],
            },
            4: {
                0: [15, 140, 70],
                1: [pdf_width - 85, 140, 70],
                2: [15, 200, 70],
                3: [pdf_width - 85, 200, 70],
            }
        }

        # Count existing pie charts
        count = len(png_files)

        index = 0

        # Loop over pie chart images
        for png_file in png_files.values():
            # (1) Determine position & width
            x, y, width = dimensions[count][index]

            # (2) Insert image
            self.pdf.image(png_file, x, y, width)

            # (3) Increase index
            index += 1

        self.pdf.ln(140)

        # Insert disclaimers
        disclaimers = [
            # (1) German
            '- Haftungsausschluss: Alle Angaben ohne Gewähr, Irrtümer und Änderungen vorbehalten. -',

            # (2) English
            '- Disclaimer: All data is without guarantee, errors and changes are reserved. -',
        ]

        for disclaimer in disclaimers:
            self.pdf.set_font('times', 'I', 12)
            self.pdf.cell(0, 0, disclaimer, ln=True, align="C")
            self.pdf.ln(5)

        self.pdf.set_font('times', '', 10)


    def add_fiat_pages(self, assets: dict, transactions: dict) -> None:
        # Loop over `fiat` assets
        for asset in assets:
            # Add a page
            self.pdf.add_page()

            # Print heading
            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(40, 8, 'Details der {} Fiat Transaktionen:\n'.format(asset), ln=True)
            self.pdf.set_font('times', '', 10)
            self.pdf.ln(5)

            th = self.pdf.font_size + 2
            col_width = (pdf_width - 30) / 4

            # Generate table
            # (1) Print header row
            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(col_width, th, 'Datum', align='C', border=1)
            self.pdf.cell(col_width, th, 'Transaktion', align='C', border=1)
            self.pdf.cell(col_width, th, 'Betrag', align='C', border=1)
            self.pdf.cell(col_width, th, 'Gebühren', align='C', border=1)
            self.pdf.ln(th)
            self.pdf.set_font('times', '', 9)

            th = self.pdf.font_size + 2

            # Loop over transactions
            for transaction in transactions:
                # Skip fiat currencies not currently selected
                if transaction['Asset'] != asset:
                    continue

                # (2) Print table row
                self.pdf.cell(col_width, th, str(transaction['Datum']), border=1)
                self.pdf.cell(col_width, th, str(transaction['Transaktion']), border=1)
                self.pdf.cell(col_width, th, str(transaction['Betrag']), border=1)
                self.pdf.cell(col_width, th, str(transaction['Gebühren']), border=1)

                self.pdf.ln(th)


    def add_transaction_pages(self, assets: dict, transactions: list, balance: list, categories: dict) -> None:
        # Loop over assets
        for mode, asset_list in assets.items():
            # Skip `fiat` (which is handled separately)
            if mode == 'fiat':
                continue

            for asset in asset_list:
                # Set default
                hint = False

                # Add a page
                self.pdf.add_page()

                # Print heading
                self.pdf.set_font('times', 'B', 10)
                self.pdf.cell(40, 8, 'Details der {} {} Transaktionen:\n'.format(asset, categories[mode]), ln=True)
                self.pdf.set_font('times', '', 10)
                self.pdf.ln(5)

                th = self.pdf.font_size + 2
                col_width = (pdf_width - 30) / 6

                # Generate table
                # (1) Print header row
                self.pdf.set_font('times', 'B', 10)
                self.pdf.cell(col_width, th, 'Datum', align='C', border=1)
                self.pdf.cell(col_width, th, 'Transaktion', align='C', border=1)
                self.pdf.cell(col_width, th, 'Betrag', align='C', border=1)
                self.pdf.cell(col_width, th, 'Asset Menge', align='C', border=1)
                self.pdf.cell(col_width, th, 'Asset Preis', align='C', border=1)
                self.pdf.cell(col_width, th, 'Gebühren', align='C', border=1)
                self.pdf.ln(th)

                self.pdf.set_font('times', '', 9)
                th = self.pdf.font_size + 2

                # Loop over transactions
                for item in transactions[mode]['all']:
                    # Skip assets not currently selected
                    if item['Asset'] != asset:
                        continue

                    # If assets were transfered over ..
                    if item['Transaktion'] == 'empfangen':
                        # .. remember it (to notify about possible inaccuracy later)
                        hint = True

                    # (2) Print table row
                    self.pdf.cell(col_width, th, str(item['Datum']), border=1)
                    self.pdf.cell(col_width, th, str(item['Transaktion']), border=1)
                    self.pdf.cell(col_width, th, str(item['Betrag']), border=1)
                    self.pdf.cell(col_width, th, str(item['Asset Menge']), border=1)
                    self.pdf.cell(col_width, th, str(item['Asset Preis']), border=1)
                    self.pdf.cell(col_width, th, str(item['Gebühren']), border=1)
                    self.pdf.ln(th)

                for item in balance[mode]:
                    if item['Asset'] == asset:
                        self.pdf.ln(th * 2)
                        self.pdf.set_font('times', 'B', 10)
                        self.pdf.cell(45, th, 'Gewinn/Verlust: ')

                        if float(item['winLoss']) < 0:
                            self.pdf.set_text_color(225, 0, 0)

                        elif float(item['winLoss']) > 0:
                            self.pdf.set_text_color(0, 225, 0)

                        else:
                            self.pdf.set_text_color(0, 0, 0)

                        self.pdf.cell(100, th, '{:.2f} EUR'.format(float(item['winLoss'])), ln=True)

                        self.pdf.set_font('times', '', 10)
                        self.pdf.set_text_color(0, 0, 0)

                # If hint is indicated ..
                if hint:
                    # (1) .. print hint
                    self.pdf.set_text_color(225, 0, 0)
                    self.pdf.ln(th)
                    self.pdf.cell(45, th, '* Durch das Einzahlen des Assets ist eine genaue Berechnung nicht möglich.')
                    self.pdf.set_text_color(0, 0, 0)

                    # (2) .. reset hint
                    hint = False


    def add_taxes_page(self, guidelines: dict, taxes: dict) -> None:
        # Loop over taxable assets & their corresponding guidelines
        for mode, guideline in guidelines.items():
            # Skip mode if ..
            # (1) .. mode not available
            if mode not in taxes:
                continue

            # (2) .. no corresponding taxes available
            if not taxes[mode]:
                continue

            # (3) .. first entry is test
            # TODO: Revisit this implementation, let it down gently
            if taxes[mode][0]['Verkaufsjahr'] == 1990:
                continue

            # Add a page
            self.pdf.add_page()

            # Insert heading
            self.pdf.ln(5)
            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(40, 8, 'Welchen Gewinn muss ich versteuern:', ln=True)
            self.pdf.set_font('times', '', 10)
            self.pdf.ln(3)

            # Insert tax guideline
            self.pdf.cell(0, 0, guideline, ln=True, align='C')
            self.pdf.ln(12)

            col_width = (pdf_width - 30) / 3
            th = self.pdf.font_size + 2

            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(col_width, th, 'Asset', align='C', border=1)
            self.pdf.cell(col_width, th, 'relevantes Jahr', align='C', border=1)
            self.pdf.cell(col_width, th, 'Betrag', align='C', border=1)
            self.pdf.ln(th)
            self.pdf.set_font('times', '', 9)

            for item in taxes[mode]:
                # Insert subheading
                self.pdf.cell(col_width, th, item['Asset'], border=1)
                self.pdf.cell(col_width, th, str(item['Verkaufsjahr']), align='C', border=1)

                # Set color ..
                # (1) .. red if negative
                if float(item['Betrag']) < 0:
                    self.pdf.set_text_color(225, 0, 0)

                # (2) .. green if positive
                if float(item['Betrag']) > 0:
                    self.pdf.set_text_color(0, 225, 0)

                # Insert taxable amount
                self.pdf.cell(col_width, th, '{:.2f}'.format(item['Betrag']), align='C', border=1)
                self.pdf.set_text_color(0, 0, 0)
                self.pdf.ln(th)

            self.pdf.cell(45, th, '* Durch das Einzahlen des Assets ist eine genaue Berechnung nicht möglich.')
            self.pdf.ln(16)

            year = taxes[mode][0]['Verkaufsjahr']
            tax_amount = 0

            for item in taxes[mode]:
                if year == item['Verkaufsjahr']:
                    tax_amount += float(item['Betrag'])

                else:
                    if year == today.year:
                        self.pdf.cell(45, th, 'In {} sind bis jetzt Gewinne/Verluste im Wert von {:.2f} angefallen.'.format(year, tax_amount))
                        self.pdf.ln(6)

                    else:
                        self.pdf.cell(45, th, 'In {} sind Gewinne/Verluste im Wert von {:.2f} angefallen.'.format(year, tax_amount))
                        self.pdf.ln(6)

                    tax_amount = float(item['Betrag'])
                    year = item['Verkaufsjahr']

            if tax_amount != 0:
                if year == today.year:
                    self.pdf.cell(45, th, 'In {} sind bis jetzt Gewinne/Verluste im Wert von {:.2f} angefallen.'.format(year, tax_amount))
                    self.pdf.ln(6)

                else:
                    self.pdf.cell(45, th, 'In {} sind Gewinne/Verluste im Wert von {:.2f} angefallen.'.format(year, tax_amount))
                    self.pdf.ln(6)


    def add_tax_pages(self, years: set, taxes: dict, currency: dict, categories: dict) -> None:
        # Loop over taxable years
        for year in years:
            # Add a page
            self.pdf.add_page()

            # Insert heading
            th = self.pdf.font_size + 2
            self.pdf.ln(5)
            self.pdf.set_font('times', 'B', 12)
            self.pdf.cell(40, 8, 'Zusammenfassung Steuern {}:'.format(year), ln=True)
            self.pdf.set_font('times', '', 10)
            self.pdf.ln(th * 3)

            # Set total
            amount = 0

            for mode, category in categories.items():
                # Skip `fiat` (no tax page)
                if mode == 'fiat':
                    continue

                temp_amount = 0

                if taxes[mode]:
                    self.pdf.set_font('times', 'B', 10)
                    self.pdf.cell(0, 0, category, ln=True)
                    self.pdf.set_font('times', '', 10)
                    self.pdf.ln(th)

                    for item in taxes[mode]:
                        if item['Verkaufsjahr'] == year:
                            self.pdf.ln(th)
                            self.pdf.cell(0, 0, '{}'.format(item['Asset']), ln=True)
                            self.pdf.cell(0, 0, '{}{:.2f} {}'.format(self.whitespace, item['Betrag'], currency), align='R', ln=True)

                            temp_amount += float(item['Betrag'])

                    self.pdf.ln(th)
                    self.pdf.cell(0, 0, self.large_line, ln=True)
                    self.pdf.ln(th)
                    self.pdf.cell(0, 0, '{}{:.2f} {}'.format(self.whitespace, temp_amount, currency), align='R', ln=True)
                    self.pdf.ln(th * 2)

                    amount += temp_amount

            self.pdf.ln(th * 4)
            self.pdf.set_font('times', 'B', 11)

            if year == today.year:
                self.pdf.cell(45, th, 'In {} sind bis jetzt Gewinne/Verluste im Wert von {:.2f} {} zu versteuern.'.format(year, amount, currency))
                self.pdf.ln(6)

            else:
                self.pdf.cell(45, th, 'In {} sind Gewinne/Verluste im Wert von {:.2f} {} zu versteuern.'.format(year, amount, currency))
                self.pdf.ln(6)

            self.pdf.ln(6)
            self.pdf.set_font('times', '', 9)
            self.pdf.cell(45, th, '*gezahlte Gebühren werden derzeit noch nicht mit verrechnet, da die *csv Datei keine Asset Preise für Gebühren zur verfügung stellt.', ln=True)


    def add_portfolio_pages(self, portfolio: dict, assets: dict, categories: dict) -> None:
        # Loop over asset classes
        for mode, category in categories.items():
            # Skip mode if ..
            # (1) .. mode not available
            if mode not in portfolio:
                continue

            # (2) .. no corresponding portfolio available
            if not portfolio[mode]:
                continue

            # Gather portfolio
            asset_portfolio = [item for item in portfolio[mode] if item['Asset'] in [item['asset'] for item in assets[mode]]]

            if not asset_portfolio:
                continue

            # Add a page
            self.pdf.add_page()

            # Insert heading
            self.pdf.ln(5)
            self.pdf.set_font('times', 'B', 10)
            self.pdf.cell(40, 8, 'Diese Vermögenswerte der Anlageklasse "{}" sollten in deinem Portfolio sein:'.format(category), ln=True)
            self.pdf.set_font('times', '', 10)
            self.pdf.ln(12)
            col_width = (pdf_width - 30) / 6
            self.pdf.set_font('times', 'B', 10)
            th = self.pdf.font_size + 2

            self.pdf.cell(col_width, th, 'Datum', align='C', border=1)
            self.pdf.cell(col_width, th, 'Transaktion', align='C', border=1)
            self.pdf.cell(col_width, th, 'Betrag', align='C', border=1)
            self.pdf.cell(col_width, th, 'Asset Menge', align='C', border=1)
            self.pdf.cell(col_width, th, 'Asset Preis', align='C', border=1)
            self.pdf.cell(col_width, th, 'HODL Zeit', align='C', border=1)
            self.pdf.ln(th)
            self.pdf.set_font('times', '', 9)

            temp_asset = ''
            temp_amount = 0
            temp_price = 0
            hodl_amount = 0

            for item in asset_portfolio:
                diftime = today - datetime.strptime(item['Datum'], '%Y-%m-%d %H:%M:%S')

                if item['Asset'] != temp_asset:
                    if temp_price > 0:
                        col_width = pdf_width - 30

                        if hodl_amount > 0:
                            self.pdf.cell(col_width, th, 'Haltefrist 1 Jahr+: {:.6f} {}'.format(hodl_amount, temp_asset), align='R',  border=1)
                            self.pdf.ln(th)

                        else:
                            self.pdf.cell(col_width, th, '',  border=1)
                            self.pdf.ln(th)

                        self.pdf.cell(col_width, th, 'Investiert: {:.2f}'.format(temp_price), align='R', border=1)
                        self.pdf.ln(th)
                        self.pdf.cell(col_width, th, 'Gesamt Menge: {:.6f} {}'.format(temp_amount, temp_asset), align='R',  border=1)
                        self.pdf.ln(th)
                        self.pdf.cell(col_width, th, 'Durchschnitt Preis: {:.3f}'.format(temp_price / temp_amount), align='R', border=1)
                        self.pdf.ln(th)

                    temp_asset = item['Asset']

                    col_width = pdf_width - 30

                    self.pdf.set_font('times', 'B', 10)
                    self.pdf.cell(col_width, th, item['Asset'], align='C', border=1)
                    self.pdf.set_font('times', '', 9)
                    self.pdf.ln(th)

                    col_width = (pdf_width - 30) / 6
                    temp_amount = 0
                    temp_price = 0

                col_width = (pdf_width - 30) / 6

                self.pdf.cell(col_width, th, str(item['Datum']), border=1)
                self.pdf.cell(col_width, th, str(item['Transaktion']), border=1)
                self.pdf.cell(col_width, th, str(item['Betrag']), border=1)
                self.pdf.cell(col_width, th, str(item['Asset Menge']), border=1)
                self.pdf.cell(col_width, th, str(item['Asset Preis']), border=1)

                if float(diftime.days) > 365:
                    self.pdf.set_text_color(0, 255, 0)

                    hodl_amount += float(item['Asset Menge'])

                self.pdf.cell(col_width, th, str(diftime.days), border=1)
                self.pdf.ln(th)
                self.pdf.set_text_color(0, 0, 0)

                temp_amount += float(item['Asset Menge'])

                if item['Betrag'] != '':
                    temp_price += float(item['Betrag'])

            col_width = (pdf_width - 30) / 4

            if temp_price > 0:
                col_width = pdf_width - 30

                if hodl_amount > 0:
                    self.pdf.cell(col_width, th, 'Haltefrist 1 Jahr+: {:.6f} {}'.format(hodl_amount, temp_asset), align='R',  border=1)
                    self.pdf.ln(th)

                else:
                    self.pdf.cell(col_width, th, '',  border=1)
                    self.pdf.ln(th)

                self.pdf.cell(col_width, th, 'Investiert: {:.2f}'.format(temp_price), align='R', border=1)
                self.pdf.ln(th)
                self.pdf.cell(col_width, th, 'Gesamt Menge: {:.6f} {}'.format(temp_amount, temp_asset), align='R',  border=1)
                self.pdf.ln(th)
                self.pdf.cell(col_width, th, 'Durchschnitt Preis: {:.3f}'.format(temp_price / temp_amount), align='R', border=1)
                self.pdf.ln(th)


    def add_donations_page(self, donations: list) -> None:
        # Import dependency
        import pyqrcode

        # If more than three donations submitted ..
        if len(donations) > 3:
            # .. limit them
            donations = donations[:3]

        # Loop over donations
        for donation in donations:
            # Generate QR code
            png_file = os.path.join(self.app_dir, '{}.png'.format(slugify(donation['title'])))
            code = pyqrcode.create(donation['address'])
            code.png(png_file, scale=1, module_color=[0, 0, 0, 128], background=[0xff, 0xff, 0xff])

            # Add to donation
            donation['qr'] = png_file

        # Add a page
        self.pdf.add_page()

        # Insert heading
        self.pdf.ln(5)
        self.pdf.cell(40, 8, 'Gefällt dir diese Anwendung, dann würde ich mich über eine Spende freuen.', ln=True)
        self.pdf.set_font('times', '', 10)
        self.pdf.ln(20)

        # Define positions for up to three images
        dimensions = [
            [100, 55, 20],
            [100, 100, 20],
            [100, 145, 20],
        ]

        # Insert donations
        for index, donation in enumerate(donations):
            # (1) Determine position & width of QR code
            x, y, width = dimensions[index]

            # Insert QR code & transfer details
            self.pdf.cell(40, 8, '{}:\n'.format(donation['title']), ln=True)
            self.pdf.image(donation['qr'], x, y, width)
            self.pdf.ln(20)
            self.pdf.cell(0, 0, '{}\n'.format(donation['address']), ln=True, align = 'C')
            self.pdf.ln(20)

        # Insert footer
        # (1) Thanks
        self.pdf.cell(40, 8, 'Vielen Dank.', ln=True)
        self.pdf.ln(20)

        # (2) Github
        git_link = 'https://github.com/MrRo-de/Bitpanda-Report'

        self.pdf.cell(40, 8, 'Das Script zur Erstellung dieses PDF findet Ihr unter:', ln=True)
        self.pdf.ln(5)
        self.pdf.cell(0, 0, git_link, link=git_link, ln=True, align = 'C')
        self.pdf.ln(20)
        self.pdf.cell(40, 8, 'Hier könnt Ihr auch gerne unter \"Issues\" einen \"New Issue\" anlegen, um mir Fehler und Verbesserungsvorschläge zukommen zu lassen.', ln=True)


    def export(self, output_file: str) -> None:
        # Export PDF report
        self.pdf.output(output_file)

        # Loop over generated images ..
        for png_file in glob.glob(os.path.join(self.app_dir, '*.png')):
            # .. deleting each one of them
            os.remove(png_file)
