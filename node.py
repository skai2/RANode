#!/usr/bin/env python3

import socket
from threading import Thread, Event
from cmd import Cmd
import random
import time


class Node():
# MAIN -------------------------------------------------------------------------
# ------------------------------------------------------------------------------
    def __init__(self):
        self.MYNAME = str(random.randint(111111, 999999))
        self.DISCOVERY_HOST = '<broadcast>'
        self.DISCOVERY_PORT = 12345
        self.NODE_HOST = Node.getIP()
        self.NODE_PORT = random.randint(1025, 65535+1)
        self.peerlist = {}
        self.reversepeer = {}

        self.discovering = Event()
        self.listening = Event()
        Thread(target=self.discoverer, args=(self.discovering,)).start()
        Thread(target=self.listener, args=(self.listening,)).start()
        print('---<<<[ (%s)-(%s, %d) ]>>>---' % \
            (self.MYNAME, self.NODE_HOST, self.NODE_PORT))

    def kill(self):
        self.discovering.clear()
        self.listening.clear()

    def peers(self):
        print("-----------------------------------------------")
        for peer in self.peerlist.keys():
            print("[(%s)-(%s, %d)]" % \
                (peer, self.peerlist[peer][0], self.peerlist[peer][1]))
        print("-----------------------------------------------")

# LISTENERS ----------------------------------------------------------------------
# ------------------------------------------------------------------------------

    def discoverer(self, discovering):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.DISCOVERY_HOST, self.DISCOVERY_PORT))
            s.settimeout(1)
            discovering.set()
            while discovering.is_set():
                try:
                    message, addr = s.recvfrom(1024)
                    Thread(target=self.handle_message, args=(message, addr,)).start()
                except socket.timeout as e:
                    self.send_message(0, 'HeyBrah-'+self.NODE_HOST+'-'+str(self.NODE_PORT)+'-'+self.MYNAME)
                    time.sleep(random.random())
                except Exception as e:
                    print(e)
            s.close()

    def listener(self, listening):
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.NODE_HOST, self.NODE_PORT))
            s.settimeout(1)
            listening.set()
            while listening.is_set():
                try:
                    message, addr = s.recvfrom(1024)
                    Thread(target=self.handle_message, args=(message, addr,)).start()
                except socket.timeout as e:
                    pass
                except Exception as e:
                    print(e)
            s.close()

    def handle_message(self, message, addr):
        message = message.decode('utf-8')
        split = message.split('-')
        if split[0] == 'HeyBrah':
            if not (split[1] == self.NODE_HOST and int(split[2]) == self.NODE_PORT):
                self.peerlist[split[3]] = (split[1], int(split[2]))
                self.reversepeer[(split[1], int(split[2]))] = split[3]
        else:
            print("from %s %s" % (self.reversepeer[addr], message))

# SENDERS ----------------------------------------------------------------------
# ------------------------------------------------------------------------------

    def getIP():
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]

    def send_message(self, id, message):
        if id == 0:
            ip = self.DISCOVERY_HOST
            port = self.DISCOVERY_PORT
        else:
            try:
                ip = self.peerlist[str(id)][0]
                port = self.peerlist[str(id)][1]
            except KeyError as e:
                print('--- <Invalid peer!>', e)
                return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.NODE_HOST, self.NODE_PORT))
                s.sendto(message.encode('utf-8'), (ip, port))
        except Exception as e:
            print(e)



# CMD --------------------------------------------------------------------------
# ------------------------------------------------------------------------------

class NodeCMD(Cmd):
    def do_quit(self, args):
        """Terminates the node."""
        self.node.kill()
        raise SystemExit

    def do_init(self, args=None):
        """Initializes the node."""
        self.node = Node()

    def do_peers(self, args):
        '''Lists all peers.'''
        self.node.peers()

    def do_send(self, args):
        """Sends a message."""
        args = args.split()
        message = 'test'
        id = 0
        if len(args) >= 1:
            id = args[0]
        if len(args) >= 2:
            message = args[1]
        if len(args) >= 3:
            for arg in args[2:]:
                message = message + ' ' + arg
        self.node.send_message(id, message)

if __name__ == '__main__':
    node = NodeCMD()
    node.do_init()
    node.prompt = ''
    node.cmdloop('')
