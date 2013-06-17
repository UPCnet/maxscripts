import os
import sys
import pymongo

from pyramid.settings import asbool
from pyramid.paster import get_appsettings
from pyramid.paster import setup_logging


default_security = {'roles': {"Manager": ["victor.fernandez",
                                          "carles.bruguera",
                                          "usuari.atenea",
                                          "usuari.somupc"
                                          ]
                              }
                    }


def init_security(settings):
    if not asbool(settings.get('mongodb.cluster', False)):
        db_uri = settings['mongodb.url']
        conn = pymongo.MongoClient(db_uri)
    else:
        hosts = settings.get('mongodb.hosts', '')
        replica_set = settings.get('mongodb.replica_set', '')
        conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

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
