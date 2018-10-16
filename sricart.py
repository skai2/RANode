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
        self.pending_replies = set()
        self.waiting_peers = list()
        Thread(target=self.free).start()

    def free(self):
        while self.current_state == State.Free:
            try:
                msg_string = self.node.messages.get(block=True,timeout=0.55)
                self.msg.fromString(msg_string)
                if self.msg.type == MessageType.Request.value:
                    debug_print(self.pretty_header(),'Request received. Replying to',self.msg.from_id)
                    self.HSN = max(self.HSN, self.msg.timestamp) + 1
                    self.send_reply(self.msg.from_id)
                self.node.messages.task_done()
            except Empty as e:
                if self.willing_to_use:
                    self.current_state = State.Waiting
                    self.OSN = self.HSN+1
                    self.HSN = self.OSN
                    for nodeid in self.node.peerlist.keys():
                        self.pending_replies.add(nodeid)
                        self.send_request(nodeid)
            except Exception as e:
                print(e)
        self.waiting()

    def waiting(self):
        while self.current_state == State.Waiting:
            try:
                msg_string = self.node.messages.get(block=True,timeout=5)
                self.msg.fromString(msg_string)
                if self.msg.type == MessageType.Request.value:
                    self.HSN = max(self.HSN, self.msg.timestamp) + 1
                    if self.my_priority():
                        debug_print(self.pretty_header(),'Request received. Deferred',self.msg.from_id)
                        self.waiting_peers.append(self.msg.from_id)
                    else:
                        debug_print(self.pretty_header(),'Request received. Replying to',self.msg.from_id)
                        self.send_reply(self.msg.from_id)
                elif self.msg.type == MessageType.Reply.value:
                    self.pending_replies.discard(self.msg.from_id)
                    debug_print(self.pretty_header(),'Reply received from',self.msg.from_id,'. Left:',len(self.pending_replies),self.pending_replies)
                    if len(self.pending_replies) == 0:
                        self.current_state = State.Using
                self.node.messages.task_done()
            except Empty as e:
                debug_print('Request/reply probably got lost. Re-sending request to pending nodes.')
                for nodeid in self.pending_replies:
                    self.send_request(nodeid)

        self.using()

    def using(self):
        print ('------------')
        for i in range(0, 10):
            print("Using: (%d)%2d" % (self.OSN, i))
            time.sleep(0.5)
        print ('------------')
        self.current_state = State.Free
        for nodeid in self.waiting_peers:
            debug_print(self.pretty_header(),'Sending deferred reply to',self.msg.from_id)
            self.send_reply(nodeid)
        self.waiting_peers.clear()
        self.willing_to_use = False
        self.free()

    def send_request(self, peer):
        debug_print(self.pretty_header(),'Sending request to', peer)
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

    def pretty_header(self):
        header = "<\033[34m"+self.node.ID+"\x1b[0m,"
        if self.current_state == State.Free:
            header = header+"\x1b[1;32;40mFree"+"\x1b[0m>"
        elif self.current_state == State.Waiting:
            header = header+"\033[33mWaiting"+"\x1b[0m>"
        elif self.current_state == State.Using:
            header = header+"\x1b[1;31;40mUsing"+"\x1b[0m>"
        return header


if __name__ == '__main__':
    node = RANode()
    while 1:
        time.sleep(random.randint(3,16))
        if random.randint(0,2) == 1:
            node.willing_to_use = True
