import click
import requests
version = 1.0

def restRequest(server, url, txn, payload, expected):
    """Send a request to the server
    
    Args:
        server (str): host:port string
        url (str): Request URL
        txn (str): HTTP verb
        payload (dict): Parameters for JSON payload
        expected (int): Successful response code
    
    Returns:
        data dict on success, None otherwise
    """
    # Make the request
    try:
        r = getattr(requests, txn)(url, json=payload)
    except requests.exceptions.ConnectionError:
        click.echo('Could not connect to the server at '
                   '{}'.format(server))
        return None
    
    data = r.json()
    if r.status_code == expected:
        return data
    
    elif r.status_code == 400:
        if len(data['message']) > 1:
            click.echo('The following errors occurred:')
            indent = ' ' * 10
            for m in data['message'].itervalues():
                click.echo(indent + m)
        else:
            click.echo('Error: ' + data['message'].itervalues().next())
    elif r.status_code == 401:
        click.echo('Authentication failure: check credentials.')
    elif r.status_code == 404:
        click.echo('Error: ' + data['message'].itervalues().next())
    elif r.status_code == 500:
        click.echo('An internal server error occurred.')
    else:
        click.echo('An unknown error occurred: status code = '
                   '{}'.format(r.status_code))
    return None
