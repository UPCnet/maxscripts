"""MAX Database initializer

Sets a user to own the Manager role inside max

Usage:
    max.security add <username>... [options]
    max.security reset [options]


Options:

    -c <maxini>, --config <maxini>            INI file with max configuration [default: config/max.ini]
"""
from docopt import docopt
from pyramid.paster import get_appsettings
from pyramid.settings import asbool
from maxutils.mongodb import get_connection
from maxutils.mongodb import get_database
import pymongo.errors
import sys


def main():
    arguments = docopt(__doc__, version='MAX Database initialized')
    maxini = arguments.get('--config')
    reset = arguments.get('reset', False)
    add = arguments.get('add', False)
    usernames = arguments.get('<username>')

    settings = get_appsettings(maxini)
    default_security = {'roles': {"Manager": []}}

    # Get configuration from settings
    dbname = settings['mongodb.db_name']
    cluster_enabled = asbool(settings.get('mongodb.cluster', False))
    replica_set = settings.get('mongodb.replica_set', '')
    mongodb_username = settings.get('mongodb.username', '')
    mongodb_password = settings.get('mongodb.password', '')
    mongodb_auth_db = settings.get('mongodb.authdb', dbname)
    auth_enabled = asbool(settings.get('mongodb.auth', False))
    mongodb_uri = settings.get('mongodb.hosts', '') if cluster_enabled else settings['mongodb.url']

    try:
        conn = get_connection(
            mongodb_uri,
            use_greenlets=True,
            cluster=replica_set if cluster_enabled else None)
    except pymongo.errors.ConnectionFailure:
        print "Error connecting to mongodb, is it started?"
        sys.exit(1)

    db = get_database(
        conn,
        dbname,
        username=mongodb_username if auth_enabled else None,
        password=mongodb_password if auth_enabled else None,
        authdb=mongodb_auth_db if auth_enabled else None)

    if reset:
        db.security.remove({})
        db.security.insert(default_security)
        print "Max security settings has been reseted"

    if add:
        security = db.security.find_one({})
        if security is None:
            security = db.security.insert(default_security)
        for user in usernames:
            if user not in security['roles']['Manager']:
                db.security.update({'_id': security['_id']}, {'$push': {'roles.Manager': user}})
                print " + Added {} to Manager role".format(user)

    if reset or add:
        print "Remember to restart max process!"


if __name__ == '__main__':
    main()
