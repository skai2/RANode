#!/usrt/bin/env python3

from node import *
from enum import Enum
import time

waiting_peers = list()

class MessageType(Enum):
    Request = 0
    Reply = 1

class Message:
    def __init__(self, from_id=0, msg_type=MessageType.Request, timestamp=0):
        self.from_id = int(from_id)
        self.type = msg_type.value
        self.timestamp = int(timestamp)

    def fromString(self, message_string):
        split_str = message_string.split('-')
        self.from_id = int(split_str[0])
        self.type = int(split_str[1])
        self.timestamp = int(split_str[2])

    def toString(self):
        return str(self.from_id)+'-'+str(self.type)+'-'+str(self.timestamp)

class State(Enum):
    Free = 0
    Waiting = 1
    Using = 2

class RANode(Node):
    def __init__(self):
        self.current_state = State.Free
        self.HSN = 0
        self.OSN = 0
        super(RANode, self).__init__(debug=False)

    def handle_message(self, message, addr):
        handled_msg = super(RANode, self).handle_message(message, addr)
        if handled_msg:
            msg = Message()
            msg.fromString(handled_msg)
            if msg.type == MessageType.Request.value:
                self.handle_request(msg.from_id, msg.timestamp)
            elif msg.type == MessageType.Reply.value:
                self.handle_reply(msg.from_id, msg.timestamp)

    def use_resource(self):
        r =  random.randint(5,15)
        print('Using resource for', r, 'seconds')
        time.sleep(r)
        self.current_state = State.Free
        reply = Message(self.MYNAME, MessageType.Reply, self.OSN)
        for nodeid in waiting_peers:
            self.send_message(nodeid, reply.toString())
        waiting_peers.clear()
    
    def send_request(self):
        self.current_state = State.Waiting
        self.OSN = self.HSN+1
        for peer in self.peerlist.keys():
            if not self.replies[int(peer)]:
                print('Sending request to ', peer)
                request = Message(self.MYNAME, MessageType.Request, self.OSN)
                self.send_message(peer, request.toString())

    def check_replies(self):
        for peer in self.peerlist.keys():
            if not self.replies[int(peer)]:
                print('Peer', peer, 'did not reply yet')
                return False
        print('Got all replies')
        return True
    
    def handle_reply(self, from_id, timestamp):
        print('Handling reply from: ', from_id)
        if self.current_state != State.Waiting:
            #something wrong
            print('Received Reply and state != waiting')
        else:
            print('Reply from', from_id, 'set to true')
            self.replies[from_id] = True
            if self.check_replies():
                self.current_state = State.Using
                self.use_resource()
    
    def higher_priority(self, from_id, timestamp):
        if self.OSN < timestamp:
            return False
        elif self.OSN > timestamp:
            return True
        else:
            return myid < from_id
    
    def handle_request(self, from_id, timestamp):
        print('Handling request from: ', from_id)
        self.HSN = max(self.HSN, timestamp)
        self.replies[from_id] = False
        if self.current_state == State.Free:
            reply = Message(self.MYNAME, MessageType.Reply, self.OSN)
            print('Sending reply to', from_id)
            self.send_message(from_id, reply.toString())
        elif self.current_state == State.Waiting:
            if self.higher_priority(from_id, timestamp):
                reply = Message(self.MYNAME, MessageType.Reply, self.OSN)
                print('Sending reply to', from_id)
                self.send_message(from_id, reply.toString())
            else:
                waiting_list.append(from_id)
        else:
            waiting_list.append(from_id)

if __name__ == '__main__':
    node = RANode()
    time.sleep(random.randint(3,10))
    if random.randint(0,2) == 1:
        node.send_request()
