import click
from floranet.util import euiString, devaddrString, intHexString, hexStringInt
from floranet.commands import version, restRequest
    
@click.group()
def device():
    pass

@device.command()
@click.pass_context
@click.argument('deveui', nargs=1)
def show(ctx, deveui):
    """show a device, or all devices.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """
    if '.' in deveui:
        deveui = str(hexStringInt(str(deveui)))
    
    # Form the url and payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    url = 'http://{}/api/v{}'.format(server, version)
    url += '/devices' if deveui == 'all' else '/device/{}'.format(deveui)
    
    # Make the request
    data = restRequest(server, url, 'get', payload, 200)
    if data is None:
        return
    
    # Single device
    if deveui != 'all':
        d = data
        indent = ' ' * 10
        enable = 'enabled' if d['enabled'] else 'disabled'
        drate = d['tx_datr'] if d['tx_datr'] else 'N/A'
        nwkid = hex(d['devaddr'] >> 25)
        snrav = '{0:.2f} dBm'.format(d['snr_average']) if d['snr_average'] else 'N/A'
        appname = d['appname'] if d['appname'] else 'N/A'
        lat = '{0:.4f}'.format(d['latitude']) if d['latitude'] else 'N/A'
        lon = '{0:.4f}'.format(d['longitude']) if d['longitude'] else 'N/A'
        activ = 'Over the air (OTAA)' if d['otaa'] else 'Personalization (ABP)'
        click.echo('Device EUI: ' + euiString(d['deveui']))
        click.echo(indent + 'device address ' + devaddrString(d['devaddr']) + \
                   ' nwkID ' + nwkid + ' ' + enable)
        click.echo(indent + 'name: ' + d['name'])
        click.echo(indent + 'class: ' + d['devclass'].upper())
        click.echo(indent + 'application EUI: ' + euiString(d['appeui']))
        click.echo(indent + 'activation: ' + activ)
        click.echo(indent + 'appname: ' + appname)
        click.echo(indent + 'latitude: ' + lat)
        click.echo(indent + 'longitude: ' + lon)
        if not d['otaa']:
            click.echo(indent + 'appskey: ' + intHexString(d['appskey'], 16))
            click.echo(indent + 'nwkskey: ' + intHexString(d['nwkskey'], 16))
        click.echo(indent + 'data rate: ' + drate)
        click.echo(indent + 'average SNR: ' + snrav)
        return
        
    # All devices
    click.echo('{:15}'.format('Device') + \
               '{:24}'.format('DeviceEUI') + \
               '{:12}'.format('DevAddr') + \
               '{:9}'.format('Enabled') + \
               '{:5}'.format('Act') + \
               '{:12}'.format('Average-SNR'))
    for i,d in data.iteritems():
        enable = 'Yes' if d['enabled'] else 'No'
        active = 'OTA' if d['otaa'] else 'ABP'
        snravg = '{0:.2f} dBm'.format(d['snr_average']) if d['snr_average'] else 'N/A'
        click.echo('{:14.14}'.format(d['name']) + ' ' + \
                   '{:23}'.format(euiString(d['deveui'])) +  ' ' + \
                   '{:12}'.format(devaddrString(d['devaddr'])) + \
                   '{:9}'.format(enable) + \
                   '{:5}'.format(active) + \
                   '{:12}'.format(snravg))

@device.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('deveui')
@click.pass_context
def add(ctx, deveui):
    """add a device.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """
    if '.' in deveui:
        deveui = str(hexStringInt(str(deveui)))
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    def check_missing(args, required):
        missing = [item for item in required if item not in args.keys()]
        if not missing:
            return True
        if len(missing) == 1:
            click.echo("Missing argument " + missing[0])
        else:
            click.echo("Missing arguments: " + ' '.join(missing))
        return False

    required = ['name', 'class', 'enabled', 'otaa', 'appeui']
    if not check_missing(args, required):
        return
        
    # Convert appeui 
    args['appeui'] = hexStringInt(str(args['appeui']))

    # Convert class
    args['devclass'] = args.pop('class').lower()
    
    # Enabled is a yes or no
    args['enabled'] = True if args['enabled'].lower() == 'yes' else False
        
    # If OTAA is false, we must have devaddr, nwkskey and appskey
    args['otaa'] = True if args['otaa'].lower() == 'yes' else False
    if not args['otaa']:
        required = ['appskey', 'nwkskey', 'devaddr']
        if not check_missing(args, required):
            return
        for r in required:
            args[r] = hexStringInt(str(args[r]))

    # Create the payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'], 'deveui': deveui}
    payload.update(args)
    
    # Perform a POST on /devices endpoint
    url = 'http://{}/api/v{}/devices'.format(server, version)
    if restRequest(server, url, 'post', payload, 201) is None:
        return
    
@device.command(context_settings=dict(
    ignore_unknown_options=True,
    allow_extra_args=True))
@click.argument('deveui')
@click.pass_context
def set(ctx, deveui):
    """modify a device.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """

    deveui = hexStringInt(str(deveui))
    
    # Translate kwargs to dict
    args = dict(item.split('=', 1) for item in ctx.args)
    
    # Enabled is a yes or no
    if 'enabled' in args:
        args['enabled'] = True if args['enabled'].lower() == 'yes' else False
    
    if 'class' in args:
        args['devclass'] = args.pop('class').lower()
        
    if 'nwkskey' in args:
        args['nwkskey'] = hexStringInt(str(args['nwkskey']))
    
    if 'appskey' in args:
        args['appskey'] = hexStringInt(str(args['appskey']))

    # Add the args to payload
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
    payload.update(args)
    
    # Perform a PUT on /device/deveui endpoint
    url = 'http://{}/api/v{}/device/{}'.format(server, version, deveui)
    if restRequest(server, url, 'put', payload, 200) is None:
        return

def state(ctx, deveui, enabled):
    """Issue a PUT request to enable or disable a device.
    
    Args:
        ctx (): Click context
        deveui (int): Device EUI
        enabled (bool): Enable/disable flag
    """
    if ':' in deveui:
        deveui = str(hexStringInt(str(deveui)))
        
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token'],
               'enabled': enabled}
    
    # Perform a PUT on /device/deveui endpoint
    url = 'http://{}/api/v{}/device/{}'.format(server, version, deveui)
    if restRequest(server, url, 'put', payload, 200) is None:
        return

    e = 'enabled' if enabled else 'disabled'
    
@device.command()
@click.pass_context
@click.argument('deveui', nargs=1)
def enable(ctx, deveui):
    """enable a device.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """
    state(ctx, deveui, True)
    
@device.command()
@click.pass_context
@click.argument('deveui', nargs=1)
def disable(ctx, deveui):
    """disable a device.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """
    state(ctx, deveui, False)

@device.command()
@click.argument('deveui')
@click.pass_context
def delete(ctx, deveui):
    """delete a device.
    
    Args:
        ctx (Context): Click context
        deveui (str): Device EUI string
    """
    if '.' in deveui:
        deveui = str(hexStringInt(str(deveui)))

    # Add the kwargs to payload as a dict
    server = ctx.obj['server']
    payload = {'token': ctx.obj['token']}
        
    # Perform a DELETE on /device/deveui endpoint
    url = 'http://{}/api/v{}/device/{}'.format(server, version, deveui)
    if restRequest(server, url, 'delete', payload, 200) is None:
        return
    
