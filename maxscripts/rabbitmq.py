from maxclient import MaxClient

import argparse
import ConfigParser
import json
import pika
import pymongo
import requests
import os
import re
import sys


class InitAndPurgeRabbitServer(object):  # pragma: no cover

    def __init__(self, options, quiet=False):
        self.quiet = quiet
        self.options = options

        self.common = ConfigParser.ConfigParser()
        self.common.read(self.options.commonfile)

        self.instances = ConfigParser.ConfigParser()
        self.instances.read(self.options.instancesfile)

        try:
            self.cluster = self.common.get('mongodb', 'cluster')
            self.standaloneserver = self.common.get('mongodb', 'url')
            self.clustermembers = self.common.get('mongodb', 'hosts')
            self.replicaset = self.common.get('mongodb', 'replica_set')
            self.rabbitmq_url = self.common.get('rabbitmq', 'server')
            self.rabbitmq_manage_url = self.common.get('rabbitmq', 'manage')
            self.maxserver_names = [maxserver for maxserver in self.instances.sections() if maxserver.startswith('max_')]

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

        rabbit_con = pika.BlockingConnection(
            pika.URLParameters(self.rabbitmq_url)
        )

        for dbname in self.maxserver_names:
            print('')
            print('Initializing and purging RabbitMQ server for "{}" max instance'.format(dbname.split('_')[-1]))
            print('')

            db = conn[dbname]
            channel = rabbit_con.channel()

            current_conversations = set([unicode(conv['_id']) for conv in db.conversations.find({}, {'_id': 1})])
            req = requests.get('{}/api/exchanges'.format(self.rabbitmq_manage_url), auth=('guest', 'guest'))
            if req.status_code != 200:
                print('  > Error getting current exchanges from RabbitMQ server.')
            current_exchanges = req.json()

            current_exchanges = set([exchange.get('name') for exchange in current_exchanges])

            to_add = current_conversations - current_exchanges

            # to_delete = current_exchanges - current_conversations

            # Exclude the default Rabbit exchange
            # to_delete = to_delete - set([u''])

            # Delete orphaned exchanges in RabbitMQ
            # for exdel in to_delete:
            #     if not exdel.startswith('amq') and not exdel.startswith('new') \
            #        and not exdel.startswith('twitter'):
            #         channel.exchange_delete(exdel)
            #         print("  > Added exchange {}".format(exdel))

            # Create the default push queue
            channel.queue_declare("push", durable=True)
            print("  > Declared 'push' queue.")

            # Add missing exchanges in RabbitMQ
            for exadd in to_add:
                channel.exchange_declare(exchange=exadd,
                                         durable=True,
                                         type='fanout')
                channel.queue_bind(exchange=exadd, queue="push")
                print("  > Added exchange {}".format(exadd))

            # Create default exchange if not created yet
            channel.exchange_declare(exchange='new',
                                     durable=True,
                                     type='direct')
            print("  > Declared 'new' exchange.")

            # Create twitter exchange if not created yet
            channel.exchange_declare(exchange='twitter',
                                     durable=True,
                                     type='fanout')
            print("  > Declared 'twitter' exchange.")
            # Create the default twitter queue
            channel.queue_declare("twitter", durable=True)
            print("  > Declared 'twitter' queue.")
            channel.queue_declare("tweety_restart", durable=True)
            print("  > Declared 'tweety_restart' queue.")
            channel.queue_bind(exchange="twitter", queue="twitter")
            print("  > Binded 'twitter' queue to 'twitter' exchange.")

            print('  > Done.')
            print('')


def main(argv=sys.argv, quiet=False):  # pragma: no cover
    description = "Initialize and purge if needed RabbitMQ development server."
    parser = argparse.ArgumentParser(description=description)

    parser.add_argument(
        '-i', '--instances',
        dest='instancesfile',
        type=str,
        default='config/instances.ini',
        help=("Max instances configuration file"))
    parser.add_argument(
        '-c', '--config',
        dest='commonfile',
        type=str,
        default='config/common.ini',
        help=("Common configuration file"))
    options = parser.parse_args()

    command = InitAndPurgeRabbitServer(options, quiet)
    return command.run()
