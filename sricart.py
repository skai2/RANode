#!/usr/bin/env python3

from node import *
from enum import Enum
from queue import Empty
import time
from threading import Lock



DEBUGnode = False
DEBUGricart = True
lock = Lock()

def debug_print(*args, **kwargs):
    if DEBUGricart:
        print(*args, **kwargs)

class MessageType(Enum):
    Request = 0
    Reply = 1

class Message:
    def __init__(self, from_id='', msg_type=MessageType.Reply, timestamp=0):
        self.from_id = from_id
        self.type = msg_type.value
        self.timestamp = int(timestamp)

    def fromString(self, message_string):
        split_str = message_string.split('-')
        self.from_id = split_str[0]
        self.type = int(split_str[1])
        self.timestamp = int(split_str[2])

    def toString(self):
        return str(self.from_id)+'-'+str(self.type)+'-'+str(self.timestamp)

class State(Enum):
    Free = 0
    Waiting = 1
    Using = 2

class RANode():
    def __init__(self):
        self.node = Node(debug=DEBUGnode)
        self.willing_to_use = False
        self.current_state = State.Free
        self.HSN = 0
        self.OSN = 0
        self.msg = Message()
        self.reply_count = 0
        self.waiting_peers = list()
        Thread(target=self.free).start()

    def free(self):
        while self.current_state == State.Free:
            try:
                msg_string = self.node.messages.get(block=True,timeout=0.55)
                self.msg.fromString(msg_string)
                if self.msg.type == MessageType.Request.value:
                    debug_print(self.node.ID,self.current_state,'| request received. Replying to',self.msg.from_id)
                    self.HSN = max(self.HSN, self.msg.timestamp) + 1
                    self.send_reply(self.msg.from_id)
                self.node.messages.task_done()
            except Empty as e:
                if self.willing_to_use:
                    self.current_state = State.Waiting
                    self.OSN = self.HSN+1
                    self.HSN = self.OSN
                    self.reply_count = len(self.node.peerlist)
                    for nodeid in self.node.peerlist.keys():
                        self.send_request(nodeid)
            except Exception as e:
                print(e)
        self.waiting()

    def waiting(self):
        while self.current_state == State.Waiting:
            msg_string = self.node.messages.get()
            self.msg.fromString(msg_string)
            if self.msg.type == MessageType.Request.value:
                self.HSN = max(self.HSN, self.msg.timestamp) + 1
                if self.my_priority():
                    debug_print(self.node.ID,self.current_state,'| request received. Deferred',self.msg.from_id)
                    self.waiting_peers.append(self.msg.from_id)
                else:
                    debug_print(self.node.ID,self.current_state,'| request received. Replying to',self.msg.from_id)
                    self.send_reply(self.msg.from_id)
            elif self.msg.type == MessageType.Reply.value:
                self.reply_count -= 1
                debug_print(self.node.ID,self.current_state,'| reply received from',self.msg.from_id,'. Left:',self.reply_count)
                if self.reply_count == 0:
                    self.current_state = State.Using
            self.node.messages.task_done()
        self.using()

    def using(self):
        print ('------------')
        for i in range(0, 10):
            print("using: (%d)%2d" % (self.OSN, i))
            time.sleep(0.5)
        print ('------------')
        self.current_state = State.Free
        for nodeid in self.waiting_peers:
            debug_print(self.node.ID,self.current_state,'| sending deferred reply to',self.msg.from_id)
            self.send_reply(nodeid)
        self.waiting_peers.clear()
        self.willing_to_use = False
        self.free()

    def send_request(self, peer):
        debug_print('Sending request to ', peer)
        request = Message(self.node.ID, MessageType.Request, self.OSN)
        self.node.send_message(peer, request.toString())

    def send_reply(self, peer):
        reply = Message(self.node.ID, MessageType.Reply)
        self.node.send_message(peer, reply.toString())

    def my_priority(self):
        if self.OSN < self.msg.timestamp:
            return True
        elif self.OSN > self.msg.timestamp:
            return False
        else:
            return self.node.ID < self.msg.from_id

if __name__ == '__main__':
    node = RANode()
    while 1:
        time.sleep(random.randint(3,16))
        if random.randint(0,2) == 1:
            node.willing_to_use = True
