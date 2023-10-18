#!/bin/python3
#
#
# Assistant - GGUF LLM server
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
LLM Assistant (GGUF)
"""


import os
import time
import socket
import threading
from _thread import start_new_thread
from datetime import datetime
from llama_cpp import Llama


# MODEL PARAMS
MODEL_PATH  = f"{os.environ['HOME']}/.local/share/assistant/models/openorca-platypus2-13b.Q4_K_M.gguf"
THREADS     = 20
# LOG PARAMS
LOG_DIR     = f"{os.environ['HOME']}/.local/share/assistant/logs/"
# TCP PARAMS
PORT        = 6771
IP          = "0.0.0.0"
# SIGNAL PARAMS
TO_SIGNAL   = b"<TMT>"
BUSY_SIGNAL = b"<BSY>"
END_SIGNAL  = b"<END>"
OK_SIGNAL   = b"<OK_>"
MAX_BLANK   = 10


def to_time_format(timestamp):
    """ Return MIL formatted date WITH HOUR MIN from UNIX timestamp """
    return datetime.fromtimestamp(timestamp).strftime('%d%b%Y')

def to_iso_format(timestamp):
    """ Return ISO formatted string of timestamp (in seconds) provided """
    return datetime.fromtimestamp(timestamp).isoformat(sep='T', timespec='auto')

def log_event(message):
    """ Log events """
    log_file = f"{LOG_DIR}assistant.log"
    if not os.path.isdir(LOG_DIR):
        os.makedirs(LOG_DIR)
    with open(log_file, 'a', encoding="ascii") as file_:
        file_.write(f"{to_iso_format(time.time())}: {message}\n")


class GPTServer:
    """ Server for open-source GPT models """

    def __init__(self):
        log_event("Server startup")
        self.llm = Llama(model_path=MODEL_PATH, n_threads=THREADS, verbose=False)
        self.gpt_lock = threading.Lock()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def server_loop(self):
        """ Main loop """
        while True:
            try:
                self.sock.bind((IP, PORT))
                self.sock.listen(5)
                log_event(f"Server bound to {IP}:{PORT}")
                break
            except Exception as exc:
                log_event(f"ERROR [server_loop|1]: {exc}")
                time.sleep(5)
                continue
        while True:
            try:
                con, addr = self.sock.accept()
                log_event(f"Client connected: {addr[0]}:{addr[1]}")
                if self.gpt_lock.locked():
                    log_event("GPT already locked")
                    con.sendall(BUSY_SIGNAL)
                    con.close()
                    continue
                self.gpt_lock.acquire()
                con.sendall(OK_SIGNAL)
                start_new_thread(self._process_client, (con,))
            except:
                log_event(f"ERROR [server_loop|2]: {exc}")
                self.sock.close()
                break

    def _process_client(self, conn):
        """ Process client request """
        try:
            log_event("Processing Client")
            while True:
                request = ""
                while "<END>" not in request:
                    data = conn.recv(1024).decode()
                    if not data:
                        log_event("Client disconnected")
                        break
                    request += data
                if request == "":
                    break
                log_event(f"Client asked: {request}")
                self._process_question(conn, request)
                log_event("Response sent")
            self._drop_client(conn)
        except Exception as exc:
            log_event(f"ERROR [_process_client]: {exc}")
            self._drop_client(conn)

    def _drop_client(self, conn):
        """ Drop client and reset state params """
        conn.close()
        log_event("Connection closed")
        self.llm.reset()
        log_event("LLM reset")
        self.gpt_lock.release()
        log_event("Lock released")

    def _process_question(self, conn, question):
        """ Generate response """
        connected = True
        for token in self.llm(f"Q: {question}. A: ", max_tokens=256, stop=["Q:", "<END>"], stream=True):
            try:
                if connected:
                    conn.sendall(token["choices"][0]["text"].encode())
            except Exception as exc:
                connected = False
                log_event(f"Client disconnected: ERROR {exc}")
                conn.close()
        if connected:
            conn.sendall(b"\n" + END_SIGNAL)


server = GPTServer()
server.server_loop()
