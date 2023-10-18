#!/bin/python3
#
#
# Assistant - GGUF LLM client
# Copyright (C) 2023 James Andrus
# Email: jandrus@citadel.edu

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Client program for Assistant
"""

import os
import platform
import sys
import socket
from configparser import ConfigParser
from pathlib import Path
from termcolor import colored
from colorama import Fore, Style



def get_conf_file():
    """ Get config file location based on OS (str) """
    conf_dir = str(Path.home())
    system_name = platform.system()
    if system_name == "Linux":
        conf_dir += "/.config/gpt-client/"
    else:
        raise OSError("System not supported")
    if not os.path.isdir(conf_dir):
        os.makedirs(conf_dir)
    conf_file = f"{conf_dir}gpt.ini"
    if not os.path.isfile(conf_file):
        with open(conf_file, 'a', encoding="ascii") as _file:
            _file.write("[CLIENT]\n")
            _file.write("HOST = 127.0.0.1\n")
            _file.write("PORT = 6771\n")
        raise OSError(f"Config file ({conf_file}) created, please edit this file")
    return conf_file

def pprint(msg, color='green'):
    """ Valid colors -> grey, red, green, yellow, blue, magenta, cyan, white """
    print(colored(msg, color), end='', flush=True)

def receive_response(sock):
    """ Receive GPT output """
    response = ""
    blanks = 0
    try:
        while True:
            data = sock.recv(5).decode()
            response += data
            if "<END>" in response or "<BSY>" in response:
                print(data, end='', flush=True)
                break
            print(data, end='', flush=True)
            if data == '':
                blanks += 1
            else:
                blanks = 0
            if blanks > 12:
                print(f"\n{Fore.RED}TIMEOUT")
                break
    except Exception as exc:
        raise exc

def read_conf():
    """ Read configuration file """
    conf = ConfigParser()
    try:
        conf_file = get_conf_file()
        conf.read(conf_file)
        host_ = conf.get("CLIENT", "HOST")
        port_ = conf.getint("CLIENT", "PORT")
        return (host_, port_)
    except Exception as exc:
        pprint(f"Error: {exc}", "red")
        sys.exit(4)

try:
    host, port = read_conf()
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    s.settimeout(6.0)
    s.connect((host,port))
except:
    pprint(f"Cannot connect to server {host}:{port}", "red")
    sys.exit(1)
try:
    question = input(colored("Prompt: ", "blue")) + "<END>"
except:
    pprint("\nGoodbye")
    sys.exit(0)
try:
    s.sendall(question.encode())
    print(f"\n{Fore.CYAN}Response:{Fore.GREEN}")
    receive_response(s)
    print(Style.RESET_ALL)
    s.close()
except Exception as exc:
    pprint(exc, "red")
    sys.exit(2)
