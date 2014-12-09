import click

from maxscripts import query_yes_no
from maxutils.mongodb import get_connection
from maxutils.mongodb import get_database
from maxclient.rest import MaxClient

MAXUPC = {'servers': 'mongo1.max.d.upc.edu:27017,mongo2.max.d.upc.edu:27017,mongo3.max.d.upc.edu:27017',
          'cluster_name': 'maxcluster',
          'maxserver': 'https://max.upc.edu',
          'oauth_server': 'https://oauth.upc.edu'}


@click.command()
@click.option('--maxinf', prompt=u'MAX infrastructure name. e.g "MAXUPC" or "MAXEXTERNS"', help=u'This is the common name for the MAX infrastructure we want to make the change.')
@click.option('--username', prompt=u'Username for the MAX infrastructure.', help=u'The username of the privileged user on the MAX infrastructure.')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=False)
@click.option('--client', prompt=u'Name of the client. e.g. "UPC"', help=u'')
@click.option('--origin_url', prompt=u'Origin URL', help=u'')
@click.option('--target_url', prompt=u'Target URL', help=u'')
def main(maxinf, username, password, client, origin_url, target_url):
    if maxinf not in ['MAXUPC', 'MAXEXTERNS']:
        return
    maxinf = globals()[maxinf]
    conn = get_connection(maxinf['servers'], cluster=maxinf['cluster_name'])
    db = get_database(conn, 'max_' + client, username=username, password=password, authdb='admin')

    # Find contexts with the origin_url
    origin_contexts = db.contexts.find({'url': {'$regex': origin_url}}, {'url': 1})
    origin_contexts = [a['url'] for a in origin_contexts]

    print('Changing {} contexts:'.format(len(origin_contexts)))
    for url in origin_contexts:
        print('{} -> {}'.format(url, url.replace(origin_url, target_url)))
    really_want_it = query_yes_no('Are you sure to make this changes?')

    if really_want_it:
        maxclient = MaxClient(maxinf['maxserver'], oauth_server=maxinf['oauth_server'], debug=True)
        maxclient.login()

        for url in origin_contexts:
            maxclient.contexts[url].put(url=url.replace(origin_url, target_url))
