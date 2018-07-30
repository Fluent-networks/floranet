import click
from floranet.util import euiString, devaddrString, intHexString, hexStringInt
from floranet.commands import version, restRequest
    
@click.group()
def interface():
    pass

@interface.command()
@click.pass_context
@click.argument('id', nargs=1)
def show(ctx, id):
    """show an interface, or all interfaces.
    
    Args:
        ctx (Context): Click context
        id (int): Application interface ID
    """
    # Form the url and payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    url = 'http://{}/api/v{}'.format(server, str(version))
    url += '/interfaces' if id == 'all' else '/interface/{}'.format(id)
    
    # Make the request
    data = restRequest(server, url, 'get', payload, 200)
    if data is None:
        return
    
    # All interfaces
    if id == 'all':
        click.echo('{:4}'.format('ID') + \
                   '{:24}'.format('Name') + \
                   '{:15}'.format('Type'))
        for i,a in sorted(data.iteritems()):
            if a['type'] == 'AzureIotHttps':
                a['type'] = 'Azure HTTPS'
            elif a['type'] == 'AzureIotMqtt':
                a['type'] = 'Azure MQTT'
            elif a['type'] == 'FileTextStore':
                a['type'] = 'Text File'
            click.echo('{:3}'.format(a['id']) + ' ' + \
                       '{:23}'.format(a['name']) +  ' ' + \
                       '{:14}'.format(a['type']))
        return

    # Single interface
    i = data
    indent = ' ' * 10
    started = 'Started' if i['started'] else 'Stopped'
    
    if i['type'] == 'Reflector':
        click.echo('{}name: {}'.format(indent, i['name']))
        click.echo('{}type: {}'.format(indent, i['type']))
        click.echo('{}status: {}'.format(indent, started))
    
    elif i['type'] == 'FileTextStore':
        click.echo('{}name: {}'.format(indent, i['name']))
        click.echo('{}type: {}'.format(indent, i['type']))
        click.echo('{}status: {}'.format(indent, started))
        click.echo('{}file: {}'.format(indent, i['file']))
        
    elif i['type'] == 'AzureIotHttps':
        protocol = 'HTTPS'
        click.echo('{}name: {}'.format(indent, i['name']))
        click.echo('{}protocol: {}'.format(indent, protocol))
        click.echo('{}key name: {}'.format(indent, i['keyname']))
        click.echo('{}key value: {}'.format(indent, i['keyvalue']))
        click.echo('{}Polling interval: {} minutes'.
                   format(indent, i['poll_interval']))
        click.echo('{}status: {}'.format(indent, started))
        
    elif i['type'] == 'AzureIotMqtt':
        protocol = 'MQTT'
        click.echo('{}name: {}'.format(indent, i['name']))
        click.echo('{}protocol: {}'.format(indent, protocol))
        click.echo('{}key name: {}'.format(indent, i['keyname']))
        click.echo('{}key value: {}'.format(indent, i['keyvalue']))
        click.echo('{}status: {}'.format(indent, started))
    return
        
@interface.command(context_settings=dict(
    ignore_unknown_options=True, allow_extra_args=True))
@click.argument('type')
@click.pass_context
def add(ctx, type):
    """add an interface.
    
    Args:
        ctx (Context): Click context
        iftype (str): Application interface type
    """
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    iftype = type.lower()
    types = {'reflector', 'azure', 'filetext'}
    
    # Check for required args
    if not iftype in types:
        click.echo("Unknown interface type")
        return
    
    required = {'reflector': ['name'],
                'filetext': ['name', 'file'],
                'azure': ['protocol', 'name' , 'iothost', 'keyname',
                          'keyvalue']
                }
    
    missing = [item for item in required[iftype] if item not in args.keys()]
    
    if type == 'azure' and 'protocol' == 'https' and not 'pollinterval' in args.keys():
        missing.append('pollinterval')
    
    if missing:
        if len(missing) == 1:
            click.echo("Missing argument " + missing[0])
        else:
            click.echo("Missing arguments: " + ' '.join(missing))
        return

    # Create the payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'], 'type': iftype}
    payload.update(args)
    
    # Perform a POST on /apps endpoint
    url = 'http://{}/api/v{}/interfaces'.format(server, str(version))
    if restRequest(server, url, 'post', payload, 201) is None:
        return
    
@interface.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('id')
@click.pass_context
def set(ctx, id):
    """Modify an interface.
    
    Args:
        ctx (Context): Click context
        id (str): App interface id
    """

    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    for item in ctx.args:
        payload.update([item.split('=')])
    
    # Enabled is a yes or no
    if 'enabled' in payload:
        payload['enabled'] = payload['enabled'].lower() == 'yes'
        
    # Perform a PUT on /app/appeui endpoint
    url = 'http://{}/api/v1.0/interface/{}'.format(server, id)
    if restRequest(server, url, 'put', payload, 200) is None:
        return

@interface.command()
@click.argument('id')
@click.pass_context
def delete(ctx, id):
    """delete an interface.
    
    Args:
        ctx (Context): Click context
        id (str): Application interface id
    """
    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
        
    # Perform a DELETE on /interface/id endpoint
    url = 'http://{}/api/v1.0/interface/{}'.format(server, id)
    if restRequest(server, url, 'delete', payload, 200) is None:
        return
