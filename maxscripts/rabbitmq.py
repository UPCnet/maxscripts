import argparse
import ConfigParser
import pika
import pymongo
import requests
import sys


class InitAndPurgeRabbitServer(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.config = ConfigParser.ConfigParser()
        self.config.read(self.options.configfile)

        try:
            self.cluster = self.config.get('app:main', 'mongodb.cluster')
            self.standaloneserver = self.config.get('app:main', 'mongodb.url')
            self.clustermembers = self.config.get('app:main', 'mongodb.hosts')
            self.dbname = self.config.get('app:main', 'mongodb.db_name')
            self.replicaset = self.config.get('app:main', 'mongodb.replica_set')

            self.talk_server = self.config.get('app:main', 'max.talk_server')

        except:
            print('You must provide a valid configuration .ini file.')
            sys.exit()

    def run(self):
        # Connect to the database
        if not self.cluster in ['true', 'True', '1', 1]:
            db_uri = self.standaloneserver
            conn = pymongo.MongoClient(db_uri)
        else:
            hosts = self.clustermembers
            replica_set = self.replicaset
            conn = pymongo.MongoReplicaSetClient(hosts, replicaSet=replica_set)

        db = conn[self.dbname]

        rabbit_con = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=self.talk_server
            )
        )
        channel = rabbit_con.channel()
        current_conversations = set(db.conversations.find({}))
        req = requests.get('http://{}:15672/api/exchanges'.format(self.talk_server), auth=('victor.fernandez', ''))
        if req.status_code != 200:
            print('Error getting current exchanges from RabbitMQ server.')
        current_exchanges = req.json()
        current_exchanges = set([exchange.get('name') for exchange in current_exchanges])

        to_add = current_conversations - current_exchanges
        to_delete = current_exchanges - current_conversations

        # Exclude the default Rabbit exchange
        to_delete = to_delete - set([u''])

        # Delete orphaned exchanges in RabbitMQ
        for exdel in to_delete:
            if not exdel.startswith('amq') and not exdel.startswith('new'):
                channel.exchange_delete(exdel)
                print("Added exchange {}".format(exdel))

        # Add missing exchanges in RabbitMQ
        for exadd in to_add:
            channel.exchange_declare(exchange=exadd,
                                     durable=True,
                                     type='fanout')
            print("Added exchange {}".format(exadd))

        # Create default exchange if not created yet
        if not u'new' in current_exchanges:
            channel.exchange_declare(exchange='new',
                                     durable=True,
                                     type='topic')
            print("Added 'new' exchange.")

        print("Purged RabbitMQ server.")


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Initialize and purge if needed RabbitMQ server."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument('-c', '--config',
                      dest='configfile',
                      type=str,
                      required=True,
                      help=("Configuration file"))
    options = parser.parse_args()

    command = InitAndPurgeRabbitServer(options, quiet)
    return command.run()
