import node
from enum import Enum

waiting_peers = list()

OSN = 0
HSN = 0

class MessageType(Enum):
    Request = 0
    Reply = 1

class Message:
    def __init__(self, message_string):
        split_str = message.split('-')
        self.from_id = int(split_str[0])
        self.type = int(split_str[1])
        self.timestamp = int(split_str[2])

    def __init__(self, from_id, msg_type, timestamp):
        self.from_id = from_id
        self.type = msg_type
        self.timestamp = timestamp

    def toString():
        return str(self.from_id)+'-'+str(self.type)+'-'+str(self.timestamp)

class State(Enum):
    Free = 0
    Waiting = 1
    Using = 2

def use_resource():
    while random.randint(0,100) > 1:
        sleep(1)
    current_state = State.Free
    Message reply(Type::Reply, OSN)
    for nodeid in waiting_peers:
        send(reply, nodeid)
    waiting_peers.clear()

def send_request():
    current_state = State.Waiting
    OSN = HSN+1
    for node in peers:
        if not replies[node.id]:
            Message msg(Type::Request, OSN)
            send(msg, node)

def handle_reply(from_id, timestamp):
    if current_state != State.Waiting:
        #something wrong
    else:
        replies[from_id] = True
        if everyonereplied:
            current_state = State.Using
            use_resource()

def higher_priority(from_id, timestamp):
    if OSN < timestamp:
        return False
    elif OSN > timestamp:
        return True
    else:
        return myid < from_id

def handle_request(from_id, timestamp):
    HSN = max(HSN, timestamp)
    replies[from_id] = False
    if current_state == State.Free:
        Message reply(Type::Reply, OSN)
        send(reply, from_id)
    elif current_state == State.Waiting:
        if higher_priority(from_id, timestamp):
            send(reply, from_id)
        else:
            waiting_list.append(from_id)
    else:
        waiting_list.append(from_id)

def parse_message(message_string):
    Message msg(message_string)
    if msg.type == MessageType.Request:
        handle_request(msg.from_id, msg.timestamp)
    elif msg.type == MessageType.Reply:
        handle_reply(msg.from_id, msg.timestamp)
    else:
        throw exception

class RANode(Node):
    def handle_message(lasbddaslb):
        Node.handle_message(alsjbdasjdb)
        parse_message(string)

if __name__ == '__main__':
    node = Node()
