import os
import sys
import pymongo

from pyramid.settings import asbool
from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging

from devel import get_buildout_path

buildout_path = get_buildout_path()
users = open('{}/config/.authorized_users'.format(buildout_path)).read().split('\n')
users = [a for a in users if a.strip()]

default_security = {'roles': {"Manager": users}}


def init_security(settings):
    if not asbool(settings.get('mongodb.cluster', False)):
        db_uri = settings['mongodb.url']
        conn = pymongo.MongoClient(db_uri)
    else:
        hosts = settings.get('mongodb.hosts', '')
        replica_set = settings.get('mongodb.replica_set', '')
        conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

    # Authenticate to mongodb if auth is enabled
    if settings.get('mongodb.auth', False):
        mongodb_username = settings.get('mongodb.username', '')
        mongodb_password = settings.get('mongodb.password', '')
        mongodb_auth_db = settings.get('mongodb.authdb', settings['mongodb.db_name'])

        # If we have valid username and password, authorize on
        # specified database
        if mongodb_username and mongodb_password:
            auth_db = conn[mongodb_auth_db]
            auth_db.authenticate(mongodb_username, mongodb_password)

    db = conn[settings['mongodb.db_name']]

    if not [items for items in db.security.find({})]:
        db.security.insert(default_security)
        print("Created default security info in MAXDB.\n"
              "Remember to restart max process!")


def usage(argv):
    cmd = os.path.basename(argv[0])
    print('usage: %s <config_uri>\n'
          '(example: "%s development.ini")' % (cmd, cmd))
    sys.exit(1)


def main(argv=sys.argv):
    if len(argv) != 2:
        usage(argv)
    config_uri = argv[1]
    setup_logging(config_uri)
    settings = get_appsettings(config_uri)
    init_security(settings)
