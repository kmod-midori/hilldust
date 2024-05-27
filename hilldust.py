#!/usr/bin/env python3

import sys, time, subprocess, socket, argparse, json
import hillstone

if sys.version_info.major == 2:
    exec('print "This program cannot be run in Python 2."')
    exit(1)

arg_parser = argparse.ArgumentParser(description='HillDust VPN Client')
arg_parser.add_argument('config', help='Path to JSON configuration file', type=argparse.FileType('r'))
args = arg_parser.parse_args()

import os
if os.getuid() != 0:
    print('Need to be root.')
    exit(1)

config = json.load(args.config)
args.config.close()

target = config['server']
delim_index = target.rindex(':')
host, port = target[:delim_index], target[delim_index+1:]

c = hillstone.ClientCore()
c.connect(host, int(port))
print('Connected.')
c.auth(config['username'], config['password'], '', '')
print('Authentication completed.')
c.client_info()
c.wait_network()
print('Got network configuration.')
c.new_key()
print('Key exchanging completed.')

local_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
local_udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
local_udp_socket.setsockopt(socket.IPPROTO_UDP, 100, 2) # UDP_ENCAP = UDP_ENCAP_ESPINUDP
local_udp_socket.bind(('0.0.0.0', 0))

tmp_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
tmp_udp_socket.connect((c.server_host, c.server_udp_port))
local_ip = tmp_udp_socket.getsockname()[0]
tmp_udp_socket.close()

local_port = local_udp_socket.getsockname()[1]
print("Local", local_ip, local_port)

import platform_linux
platform_linux.set_network(c, local_ip, local_port, config['routes'])
print('Network configured.')

print("Remote", c.ip_ipv4.ip)

try:
    while True:
        time.sleep(30)
        subprocess.call(["ping", "-c", "2", str(c.gateway_ipv4)])
except KeyboardInterrupt:
    pass

print('Logout.')
c.logout()
platform_linux.restore_network(c)
print('Network restored.')
