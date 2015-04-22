#!/usr/bin/env ./bin/python
DEFAULT_HUB_SERVER = 'https://hub.ulearn.upcnet.es'
DEFAULT_MAX_SERVER = 'http://max.upcnet.es'
DEFAULT_OAUTH_SERVER = 'https://oauth.upcnet.es'
DEFAULT_USERNAME = 'restricted'

MOTD = """

    ******************************************************
    *                                                    *
    *   Welcome !                                        *
    *                                                    *
    *   Use it like:                                     *
    *                                                    *
    *       client.resourcename['resource'].get()        *
    *                                                    *
    ******************************************************

"""

__maxcli__doc__ = """MAX Client terminal utility

Usage:
    maxcli [<domain> --maxserver <maxserver> --username <username> --password <password>] [options]
    maxcli -h

Options:
    -m <domain>, --domain <domain>                  The domain to use to authenticate, this will override maxserver
    -s <maxserver>, --maxserver <maxserver>         The url of a max server [default: {default_maxserver}]
    -u <username>, --username <username>            The username to authenticate on max [default: {default_username}]
    -p <password>, --password <password>            The user's password, will be prompted if missing
    -o <oauthserver>, --oauthserver <oauthserver>   Oauth server url to override the one provided by max
    -b <hubserver>, --hubserver <hubserver>         The url of a hub server from where to read domains [default: {default_hubserver}]
    -d , --debug                                    Turn on debug request dump

""".format(
    default_maxserver=DEFAULT_MAX_SERVER,
    default_username=DEFAULT_USERNAME,
    default_hubserver=DEFAULT_HUB_SERVER)

from docopt import docopt
import ipdb
from maxclient.rest import MaxClient
from maxclient.client import BadUsernameOrPasswordError


def maxcli():
    arguments = docopt(__maxcli__doc__, version='MAX Client terminal utility')
    domain = arguments.get('<domain>')
    maxserver = arguments.get('--maxserver')
    username = arguments.get('--username')
    password = arguments.get('--password')

    hubserver = arguments.get('--hubserver')
    oauthserver = arguments.get('--oauthserver')
    debug = arguments.get('--debug')

    if domain is not None:
        # Authenticate using domain
        client = MaxClient.from_hub_domain(domain, hub=hubserver, debug=debug)
    else:
        # or directlly use a maxserver
        client = MaxClient(maxserver, oauth_server=oauthserver, debug=debug)

    print
    print '  Connecting to {}'.format(client.url)
    print '-' * 60
    print

    succesfull_login = False
    while not succesfull_login:
        try:
            client.login(username, password)
        except BadUsernameOrPasswordError as error:
            print "Bad username or password, try again"
            # After getting the username once, use it while the user is trying
            # non empty passwords. On an empty password, ask for the user again
            username = error.username if error.password else None
        else:
            succesfull_login = True

    print MOTD
    ipdb.set_trace()

__maxhub__doc__ = """ULearn HUB Client terminal utility

Usage:
    maxhub <domain> [><username> <password>] [options]
    maxhub -h

Options:
    -m <domain>, --domain <domain>                  The domain to use to authenticate
    -u <username>, --username <username>            The username to authenticate on max [default: {default_username}]
    -p <password>, --password <password>            The user's password, will be prompted if missing
    -b <hubserver>, --hubserver <hubserver>         The url of a hub server from where to read domains [default: {default_hubserver}]
    -d , --debug                                    Turn on debug request dump

""".format(
    default_hubserver=DEFAULT_HUB_SERVER,
    default_username=DEFAULT_USERNAME)


def hubcli():
    arguments = docopt(__maxhub__doc__, version='ULearn HUB Client terminal utility 1.0')
    domain = arguments.get('<domain>')
    username = arguments.get('<username>')
    password = arguments.get('<password>')

    hubserver = arguments.get('--hubserver')
    debug = arguments.get('--debug')

    client = MaxClient.from_hub_domain(domain, hub=hubserver, debug=debug)

    print
    print '  Connecting to {}'.format(client.url)
    print '-' * 60
    print

    succesfull_login = False
    while not succesfull_login:
        try:
            client.login(username, password)
        except BadUsernameOrPasswordError as error:
            print "Bad username or password, try again"
            # After getting the username once, use it while the user is trying
            # non empty passwords. On an empty password, ask for the user again
            username = error.username if error.password else None
        else:
            succesfull_login = True

    print MOTD
    ipdb.set_trace()
