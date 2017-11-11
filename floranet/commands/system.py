import click
from floranet.commands import version, restRequest
from floranet.util import intHexString, devaddrString, hexStringInt

@click.group()
def system():
    pass

@system.command()
@click.pass_context
def show(ctx):
    """show the system configuration.
    
    Args:
        ctx (Context): Click context
    """
    
    # Form the url and payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    url = 'http://{}/api/v{}/system'.format(server, str(version))
    
    # Make the request
    data = restRequest(server, url, 'get', payload, 200)
    if data is None:
        return
    
    # Single application
    c = data
    indent = ' ' * 10
    click.echo('System: {} at {}'.format(c['name'], server))
    click.echo('{}Network interface: {}'.format(indent, c['listen']))
    click.echo('{}LoraWAN port: {}'.format(indent, c['port']))
    click.echo('{}Web server port: {}'.format(indent, c['webport']))
    click.echo('{}Frequency band: {}'.format(indent, c['freqband']))
    click.echo('{}Network ID: 0x{}'.format(indent,
                                intHexString(c['netid'], 3, sep=2)))
    click.echo('{}OTAA Address Range: 0x{} - 0x{}'.format(indent,
            devaddrString(c['otaastart']), devaddrString(c['otaaend'])))
    t = 'Yes' if c['adrenable'] else 'No'
    click.echo('{}ADR enabled: {}'.format(indent, t))
    if c['adrenable']:
        click.echo('{}ADR margin: {} dB'.format(indent, c['adrmargin']))
        click.echo('{}ADR cycle time: {} s'.format(indent, c['adrcycletime']))
        click.echo('{}ADR message time: {} s'.format(indent,
                                    c['adrmessagetime']))
    t = 'Yes' if c['fcrelaxed'] else 'No'
    click.echo('{}Relaxed frame count: {}'.format(indent, t))
    t = 'Yes' if c['macqueueing'] else 'No'
    click.echo('{}MAC queueing: {}'.format(indent, t))
    if c['macqueueing']:
        click.echo('{}MAC queue limit: {} s'.format(indent,
                                    c['macqueuelimit']))
    return

@system.command(context_settings=dict(
    ignore_unknown_options=True, allow_extra_args=True))
@click.pass_context
def set(ctx):
    """set system configuration parameters.
    
    Args:
        ctx (Context): Click context
    """
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    if not args:
        return
    
    # Check for valid args
    valid = {'name', 'listen', 'port', 'webport', 'apitoken', 'freqband',
             'netid', 'duplicateperiod', 'fcrelaxed', 'otaastart', 'otaaend',
             'macqueueing', 'macqueuelimit', 'adrenable', 'adrmargin',
             'adrcycletime', 'adrmessagetime'}
    bool_args = {'fcrelaxed', 'adrenable', 'macqueueing'}
    for arg,param in args.items():
        if not arg in valid:
            click.echo('Invalid argument: {}'.format(arg))
            return
        if arg in bool_args:
            args[arg] = True if param.lower() == 'yes' else False
        if arg in {'netid', 'otaastart', 'otaaend'}:
            args[arg] = hexStringInt(str(param))
        
    # Form the url and payload
    server = ctx.obj['server']
    url = 'http://{}/api/v{}/system'.format(server, str(version))
    payload = {'token': ctx.obj['token']}
    payload.update(args)
    
    # Make the request
    data = restRequest(server, url, 'put', payload, 200)
    if data is None:
        return
