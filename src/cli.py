from io import BufferedReader

import click

from .api.bitpanda import Bitpanda
from .tax.report import Report
from .utils import load_yaml, dump_json, pretty_print


@click.group()
@click.pass_context
@click.option('-v', '--verbose', count=True, help='Enable verbose mode')
@click.version_option('0.1.0')
def cli(ctx, verbose: int) -> None:
    """
    A simple CLI utility for reports on 'Bitpanda' portfolios
    """

    # Ensure context object exists & is dictionary
    ctx.ensure_object(dict)

    # Initialize context object
    ctx.obj['verbose'] = verbose


@cli.command()
@click.pass_context
@click.argument('input_file', type=click.Path())
@click.option('-o', '--output-file', default='report', type=click.Path(), help='Output filename')
@click.option('-u', '--user-file', type=click.File('rb'), help='YAML file holding user information')
@click.option('-t', '--title', default='Bitpanda Report', help='PDF document title')
@click.option('-n', '--name', help='First name and surname')
@click.option('-s', '--street', help='Street address')
@click.option('-c', '--city', help='Postcode and city')
def report(ctx: dict, input_file: str, output_file: str, user_file: BufferedReader, title: str, name: str, street: str, city: str) -> None:
    """
    Creates report using an exported CSV file
    """

    # Import dependency
    from datetime import datetime

    # If verbose mode is enabled ..
    if ctx.obj['verbose'] > 0:
        # .. report title & date of creation
        click.echo('"{}" vom {}:'.format(title, datetime.today().strftime('%d.%m.%Y')))

    # Determine user information (as displayed on report cover)
    # (1) Set default
    user_info = {}

    # (2) If information are stored ..
    if user_file:
        # .. load them
        user_info = load_yaml(user_file)

        if ctx.obj['verbose'] > 0: click.echo('Loading user information ..')

    # (3) If not ..
    if not user_info:
        # .. ask for them
        user_info = {
            'name': name if name else click.prompt('Dein Name', type=str),
            'street': street if street else click.prompt('Straße & Hausnummer', type=str),
            'city': city if city else click.prompt('PLZ und Ort', type=str),
        }

    if ctx.obj['verbose'] > 1: click.echo('user_info: {}'.format(user_info))

    # Initialize object
    obj = Report(input_file)

    # Configure it
    obj.verbose = ctx.obj['verbose']
    obj.user_info = user_info

    # Fire it up
    obj.render(output_file, title)


@cli.command()
@click.pass_context
@click.option('-k', '--api-key', prompt=True, hide_input=True, help='API key')
@click.option('-o', '--output-file', default='report', type=click.Path(), help='Output filename')
def connect(ctx: dict, api_key: str, output_file: str) -> None:
    """
    Creates report using the 'Bitpanda' API
    """

    # Import dependency
    import asyncio

    # If not specified ..
    if not api_key:
        # .. ask for API key
        api_key = click.prompt('Please enter your API key')

    # Fetch report
    if ctx.obj['verbose'] > 0: click.echo('Fetching portfolio ..')

    try:
        report = Bitpanda(api_key).get_report()

        # Present findings
        if ctx.obj['verbose'] > 1:
            pretty_print(report)

        dump_json(report, '{}.json'.format(output_file))

    except Exception as e:
        click.Context.fail(ctx, e)
