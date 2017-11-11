import click
from floranet.util import euiString, devaddrString, intHexString, hexStringInt
from floranet.commands import version, restRequest
    
@click.group()
def app():
    pass

@app.command()
@click.pass_context
@click.argument('appeui', nargs=1)
def show(ctx, appeui):
    """show an application, or all applications.
    
    Args:
        ctx (Context): Click context
        appeui (str): Application EUI
    """
    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))
    
    # Form the url and payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    url = 'http://{}/api/v{}'.format(server, str(version))
    url += '/apps' if appeui == 'all' else '/app/{}'.format(appeui)
    
    # Make the request
    data = restRequest(server, url, 'get', payload, 200)
    if data is None:
        return
    
    # Single application
    if appeui != 'all':
        a = data
        indent = ' ' * 10
        if a['appinterface_id'] == 0:
            a['appinterface_id'] = '-'
        if a['domain'] is None:
            a['domain'] = '-'
        click.echo('Application EUI: ' + euiString(a['appeui']))
        click.echo('{}name: {}'.format(indent, a['name']))
        click.echo('{}domain: {}'.format(indent, a['domain']))
        click.echo('{}fport: {}'.format(indent, a['fport']))
        click.echo('{}interface: {}'.format(indent, a['appinterface_id']))
        if a['appinterface_id'] != '-':
            click.echo('{}Properties:'.format(indent))
            properties = sorted(a['properties'].values(), key=lambda k: k['port'])
            for p in properties:
                click.echo('{}  {}  {}:{}'.format(indent, p['port'], p['name'], p['type']))
        return
        
    # All applications
    click.echo('{:14}'.format('Application') + \
               '{:24}'.format('AppEUI') + \
               '{:15}'.format('Domain') + \
               '{:6}'.format('Fport') + \
               '{:10}'.format('Interface'))
    for i,a in data.iteritems():
        if a['appinterface_id'] == 0:
            a['appinterface_id'] = '-'
        if a['domain'] is None:
            a['domain'] = '-'
        click.echo('{:13.13}'.format(a['name']) + ' ' + \
                   '{:23}'.format(euiString(a['appeui'])) +  ' ' + \
                   '{:14.14}'.format(a['domain']) + ' ' + \
                   '{:5.5}'.format(str(a['fport'])) + ' ' + \
                   '{:10}'.format(str(a['appinterface_id'])))

@app.command(context_settings=dict(
    ignore_unknown_options=True, allow_extra_args=True))
@click.argument('appeui')
@click.pass_context
def add(ctx, appeui):
    """add an application.
    
    Args:
        ctx (Context): Click context
        appeui (str): Application EUI string
    """
    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    # Check for required args
    required = ['name', 'appnonce', 'appkey', 'fport']
    
    missing = [item for item in required if item not in args.keys()]
    if missing:
        if len(missing) == 1:
            click.echo("Missing argument " + missing[0])
        else:
            click.echo("Missing arguments: " + ' '.join(missing))
        return

    args['appnonce'] = int('0x' + str(args['appnonce']), 16)
    args['appkey'] = hexStringInt(str(args['appkey']))
    
    # Create the payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'], 'appeui': appeui}
    payload.update(args)
    
    # Perform a POST on /apps endpoint
    url = 'http://{}/api/v{}/apps'.format(server, str(version))
    if restRequest(server, url, 'post', payload, 201) is None:
        return
    
@app.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('appeui')
@click.pass_context
def set(ctx, appeui):
    """modify an application.
    
    Args:
        ctx (Context): Click context
        appeui (str): Device EUI string
    """

    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))

    args = dict(item.split('=', 1) for item in ctx.args)
    if 'appkey' in args:
        args['appkey'] = hexStringInt(str(args['appkey']))

    # Enabled is a yes or no
    if 'enabled' in args:
        args['enabled'] = args['enabled'].lower() == 'yes'

    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    
    for item in args:
        payload.update(args)
        
    # Perform a PUT on /app/appeui endpoint
    url = 'http://{}/api/v1.0/app/{}'.format(server, appeui)
    if restRequest(server, url, 'put', payload, 200) is None:
        return

@app.command()
@click.argument('appeui')
@click.pass_context
def delete(ctx, appeui):
    """delete an application.
    
    Args:
        ctx (Context): Click context
        appeui (str): Application EUI string
    """
    if '.' in appeui:
        appeui = str(hexStringInt(str(appeui)))

    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
        
    # Perform a DELETE on /app/appeui endpoint
    url = 'http://{}/api/v1.0/app/{}'.format(server, appeui)
    if restRequest(server, url, 'delete', payload, 200) is None:
        return
    
