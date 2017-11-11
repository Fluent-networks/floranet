import click
from floranet.util import euiString, devaddrString, intHexString, hexStringInt
from floranet.commands import version, restRequest
    
@click.group()
def property():
    pass

@property.command(context_settings=dict(
    ignore_unknown_options=True, allow_extra_args=True))
@click.argument('appeui')
@click.pass_context
def add(ctx, appeui):
    """add an application property.
    
    Args:
        ctx (Context): Click context
        appeui (str): Application EUI string
    """
    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    # Check for required args
    required = ['port', 'name', 'type']
    
    missing = [item for item in required if item not in args.keys()]
    if missing:
        if len(missing) == 1:
            click.echo("Missing argument " + missing[0])
        else:
            click.echo("Missing arguments: " + ' '.join(missing))
        return

    # Create the payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'], 'appeui': appeui}
    payload.update(args)
    
    # Perform a POST on /propertys endpoint
    url = 'http://{}/api/v{}/propertys'.format(server, str(version))
    if restRequest(server, url, 'post', payload, 201) is None:
        return
    
@property.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('appeui')
@click.pass_context
def set(ctx, appeui):
    """modify an application property.
    
    Args:
        ctx (Context): Click context
        appeui (str): Device EUI string
    """

    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)

    # Port (int) is mandatory
    if not 'port' in args.keys():
        click.echo("Missing the port argument.")
        return
    if not isinstance(args['port'], (int, long)):
        click.echo("Port argument must be an integer.")
        return
    
    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    for item in ctx.args:
        payload.update([item.split('=')])
        
    # Perform a PUT on /property/appeui endpoint
    url = 'http://{}/api/v1.0/property/{}'.format(server, appeui)
    if restRequest(server, url, 'put', payload, 200) is None:
        return

@property.command()
@click.argument('appeui')
@click.pass_context
def delete(ctx, appeui):
    """delete an application property.
    
    Args:
        ctx (Context): Click context
        appeui (str): Application EUI string
    """
    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))

    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)

    # Port (int) is mandatory
    if not 'port' in args.keys():
        click.echo("Missing the port argument.")
        return
    if not isinstance(args['port'], (int, long)):
        click.echo("Port argument must be an integer.")
        return

    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    payload.update([args['port'].split('=')])
        
    # Perform a DELETE on /property/appeui endpoint
    url = 'http://{}/api/v1.0/property/{}'.format(server, appeui)
    if restRequest(server, url, 'delete', payload, 200) is None:
        return
    
