import click
from floranet.util import euiString, hexStringInt
from floranet.commands import version, restRequest

@click.group()
def gateway():
    pass

@gateway.command()
@click.pass_context
@click.argument('host', nargs=1)
def show(ctx, host):
    """show a gateway, or all gateways
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    # Form the url and payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    if host == 'all':
        url = 'http://' + server + '/api/v' + str(version) + \
              '/gateways'
    else:
        url = 'http://' + server + '/api/v' + str(version) + \
              '/gateway/' + host
    
    # Make the request
    data = restRequest(server, url, 'get', payload, 200)
    if data is None:
        return
    
    # Print a gateway
    if host != 'all':
        g = data
        status = 'enabled' if g['enabled'] else 'disabled'
        indent = ' ' * 10
        click.echo(g['host'] + ': ' + g['name'])
        click.echo(indent + 'eui ' + euiString(g['eui']))
        click.echo(indent + 'power: ' + str(g['power']) + ' dBm')
        click.echo(indent + 'status: ' + status)
        return
    
    # Print all gateways
    click.echo('{:15}'.format('Gateway') + '{:17}'.format('IP-Address') + \
               '{:24}'.format('EUI') + \
               '{:9}'.format('Enabled') + '{:12}'.format('Power-dBm'))
    for i,g in data.iteritems():
        enabled = 'Yes' if g['enabled'] else 'No'
        click.echo('{:14.14}'.format(g['name']) + ' ' + \
                   '{:17}'.format(g['host']) + \
                   '{:24}'.format(euiString(g['eui'])) + \
                   '{:9}'.format(enabled) + \
                   '{:2}'.format(g['power']))

@gateway.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('host')
@click.pass_context
def add(ctx, host):
    """add a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    # Translate args to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    required = {'name' , 'eui', 'enabled', 'power'}
    missing = [item for item in required if item not in args.keys()]
    if missing:
        if len(missing) == 1:
            click.echo("Missing argument " + missing[0])
        else:
            click.echo("Missing arguments: " + ' '.join(missing))
        return
    
    args['enabled'] = True if args['enabled'] == 'yes' else False
    args['eui'] = hexStringInt(str(args['eui']))
    
    # Create the payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'], 'host': host}
    payload.update(args)
    
    # Perform a POST on /gateways endpoint
    url = 'http://' + server + '/api/v1.0/gateways'
    if restRequest(server, url, 'post', payload, 201) is None:
        return
    
@gateway.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('host')
@click.pass_context
def modify(ctx, host):
    """modify a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    server = ctx.obj['server'] 
    # Add the kwargs to payload as a dict
    payload = {'token': ctx.obj['token']}
    for item in ctx.args:
        payload.update([item.split('=')])
    
    # Convert EUI to integer
    if 'eui' in payload:
         payload['eui'] = hexStringInt(str(payload['eui']))
         
    # Enabled is a yes or no
    if 'enabled' in payload:
        payload['enabled'] = payload['enabled'].lower() == 'yes'
        
    # Perform a PUT on /gateway/host endpoint
    url = 'http://' + server + '/api/v1.0/gateway/' + host
    if restRequest(server, url, 'put', payload, 200) is None:
        return
    
def state(ctx, host, enabled):
    """Enable or disable a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
        enabled (bool): Enable/disable flag
    """
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'],
               'enabled': enabled}
    
    # Perform a PUT on /gateway/host endpoint
    url = 'http://' + ctx.obj['server'] + '/api/v1.0/gateway/' + host
    if restRequest(server, url, 'put', payload, 200) is None:
        return
    
    e = 'enabled' if enabled else 'disabled'

@gateway.command()
@click.pass_context
@click.argument('host', nargs=1)
def enable(ctx, host):
    """enable a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    state(ctx, host, True)
    
@gateway.command()
@click.pass_context
@click.argument('host', nargs=1)
def disable(ctx, host):
    """disable a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    state(ctx, host, False)

@gateway.command()
@click.argument('host')
@click.pass_context
def delete(ctx, host):
    """delete a gateway.
    
    Args:
        ctx (Context): Click context
        host (str): Gateway IP address
    """
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    
    # Perform a DELETE on /gateway/host endpoint
    url = 'http://' + server + '/api/v1.0/gateway/' + host
    if restRequest(server, url, 'delete', payload, 200) is None:
        return
    
