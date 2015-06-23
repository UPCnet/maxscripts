"""MAX Database initializer

Sets a user to own the Manager role inside max

Usage:
    max.initialize <username> -c <maxini> -o

Options:

    -c <maxini>, --config <maxini>            INI file with max configuration [default: config/max.ini]
    -o, --override                            Overwrite current seurity settings
"""
from docopt import docopt
from pyramid.paster import get_appsettings
from pyramid.settings import asbool
from maxutils.mongodb import get_connection
from maxutils.mongodb import get_database
from maxcarrot import RabbitClient
import datetime


def main():
    arguments = docopt(__doc__, version='MAX Database initialized')
    maxini = arguments.get('--config')
    override = arguments.get('--override', False)
    username = arguments.get('<username>')
    users = [username]

    settings = get_appsettings(maxini)
    default_security = {'roles': {"Manager": users}}

    # Get configuration from settings
    dbname = settings['mongodb.db_name']
    cluster_enabled = asbool(settings.get('mongodb.cluster', False))
    replica_set = settings.get('mongodb.replica_set', '')
    mongodb_username = settings.get('mongodb.username', '')
    mongodb_password = settings.get('mongodb.password', '')
    mongodb_auth_db = settings.get('mongodb.authdb', dbname)
    auth_enabled = asbool(settings.get('mongodb.auth', False))
    mongodb_uri = settings.get('mongodb.hosts', '') if cluster_enabled else settings['mongodb.url']

    conn = get_connection(
        mongodb_uri,
        use_greenlets=True,
        cluster=replica_set if cluster_enabled else None)

    db = get_database(
        conn,
        dbname,
        username=mongodb_username if auth_enabled else None,
        password=mongodb_password if auth_enabled else None,
        authdb=mongodb_auth_db if auth_enabled else None)

    if override:
        db.security.remove({})

    if not [items for items in db.security.find({})]:
        db.security.insert(default_security)
        print("Created default security info in MAXDB.\n"
              "Remember to restart max process!")

    server = RabbitClient(settings['app:main']['max.rabbitmq'])
    server.declare()

    # Create default users
    for username in users:
        if not db.users.find_one({'username': username}):
            db.users.insert({
                'username': username,
                '_owner': username,
                '_creator': username,
                'objectType': 'person',
                'subscribedTo': [],
                'following': [],
                'talkingIn': [],
                'published': datetime.datetime.utcnow()})
        server.create_user(username)

    server.disconnect()


if __name__ == '__main__':
    main()
