from maxscripts.loadtest.scenarios import RateLoadTest


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
