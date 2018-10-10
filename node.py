#!/usr/bin/env python

import socket
from threading import Thread, Event
from cmd import Cmd
import random
import time
import names



# VARS -------------------------------------------------------------------------
# ------------------------------------------------------------------------------

def getIP():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

MYNAME = names.get_first_name().lower()
DISCOVERY_HOST = '<broadcast>'
DISCOVERY_PORT = 12345
NODE_HOST = getIP()
NODE_PORT = random.randint(1025, 65535+1)
peers = {}



# LISTENERS ----------------------------------------------------------------------
# ------------------------------------------------------------------------------

def discoverer(discovering):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((DISCOVERY_HOST, DISCOVERY_PORT))
        s.settimeout(1)
        discovering.set()
        while discovering.is_set():
            try:
                message, addr = s.recvfrom(1024)
                Thread(target=handle_message, args=(message, addr,)).start()
            except socket.timeout as e:
                send_message('HeyBrah-'+NODE_HOST+'-'+str(NODE_PORT)+'-'+MYNAME, (DISCOVERY_HOST, DISCOVERY_PORT))
                time.sleep(random.random())
            except Exception as e:
                print(e)
        s.close()

def listener(listening):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((NODE_HOST, NODE_PORT))
        s.settimeout(1)
        listening.set()
        while listening.is_set():
            try:
                message, addr = s.recvfrom(1024)
                Thread(target=handle_message, args=(message, addr,)).start()
            except socket.timeout as e:
                pass
            except Exception as e:
                print(e)
        s.close()

def handle_message(message, addr):
    message = message.decode('utf-8')
    split = message.split('-')
    if split[0] == 'HeyBrah':
        if not (split[1] == NODE_HOST and int(split[2]) == NODE_PORT):
            peers[split[3]] = (split[1], int(split[2]))
    else:
        print('received', message, 'from', addr)



# SENDERS ----------------------------------------------------------------------
# ------------------------------------------------------------------------------

def send_message(message, addr):
    ip = addr[0]
    port = addr[1]
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((NODE_HOST, NODE_PORT))
            s.sendto(message.encode('utf-8'), (ip, port))
    except Exception as e:
        print(e)



# MAIN -------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class Node(Cmd):
    def do_quit(self, args):
        """Terminates the node."""
        self.discovering.clear()
        self.listening.clear()
        raise SystemExit

    def do_init(self, args=None):
        """Initializes the node."""
        self.discovering = Event()
        Thread(target=discoverer, args=(self.discovering,)).start()
        self.listening = Event()
        Thread(target=listener, args=(self.listening,)).start()
        print('--<<<[ (%s)-(%s, %d) ]>>>--' % (MYNAME, NODE_HOST, NODE_PORT))

    def do_peers(self, args):
        for peer in peers.keys():
            print("[(%s)-(%s, %d)]" % (peer, peers[peer][0], peers[peer][1]))

    def do_message(self, args):
        """Sends a message."""
        args = args.split()
        message = 'test'
        host = '<broadcast>'
        port = DISCOVERY_PORT
        if len(args) != 2:
            print('invalid arguments!')
            return
        else:
            try:
                ip = peers[args[0]][0]
                port = peers[args[0]][1]
            except KeyError:
                print('invalid peer!')
                return
            message = args[1]
        send_message(message, (ip, port))
        # if len(args) > 0:
        #     message = args[0]
        # if len(args) > 1:
        #     host = args[1]
        # if len(args) > 2:
        #     port = int(args[2])
        # if len(args) > 3:
        #     print('Too many arguments!')
        #     return
        # send_message(message, (host, port))


if __name__ == '__main__':
    node = Node()
    node.do_init()
    node.prompt = ''
    node.cmdloop('')
