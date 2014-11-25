from maxscripts.loadtest.scenarios import GeventRateLoadTest as RateLoadTest


class MaxMessagesLoadTest(RateLoadTest):

    def setup(self, *args, **kwargs):
        """
            Creates 2 users in a conversation
        """
        super(MaxMessagesLoadTest, self).setup(*args, **kwargs)

        users = self.maxhelper.create_users('max_messages_user_', 2)
        self.conversation = self.maxhelper.create_conversation('test_messages', users)
        self.client = self.maxhelper.get_client_as(self.conversation['creator'])
        self.sender_username = users[-1]
        self.endpoint = self.client.conversations[self.conversation['id']].messages

    def request(self):
        """
            Inserts a message in the conversation
        """
        self.endpoint.post(object_content='I am a conversation message')


class MaxTimelineLoadTest(RateLoadTest):

    def setup(self, *args, **kwargs):
        """
            Creates 1000 messages
        """
        super(MaxTimelineLoadTest, self).setup(*args, **kwargs)

        users = self.maxhelper.create_users('max_messages_user_', 2)
        for i in range(100):
            self.maxhelper.create_activity('Random text for activity', users[0])
        self.client = self.maxhelper.get_client_as(users[0])
        self.endpoint = self.client.people[users[0]].timeline

    def request(self):
        """
            Gets a user timeline
        """
        self.endpoint.get()
