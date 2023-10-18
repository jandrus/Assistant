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
import socket
import sys
import tkinter
import time
import sqlite3
from configparser import ConfigParser
from hashlib import md5
from pathlib import Path
from tkinter import scrolledtext
from tkinter import simpledialog
from tkinter import messagebox
from tkinter import font
from threading import Thread
from datetime import datetime

DARK_BLUE   = "#001d3c"
LIGHT_BLUE  = "#015bbb"
YELLOW      = "#fed500"
BUTTON      = ("#fed500", "#015bbb")
BANNER_FONT = ("Helvetica", 12)

SIGNAL_BUSY = "<BSY>"
SIGNAL_OK   = "<OK>"



def get_conf_file():
    """ Get config file location based on OS (str) """
    conf_dir = str(Path.home())
    system_name = platform.system()
    if system_name == "Linux":
        conf_dir += "/.config/gpt-client/"
    elif system_name == "Windows":
        conf_dir += "/AppData/gpt-client/"
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

def to_iso_format(timestamp):
    """ Return ISO formatted string of timestamp (in seconds) provided (str) """
    return datetime.fromtimestamp(timestamp).isoformat(sep='T', timespec='auto')

def hash_of(text):
    """ hex md5 hash (str) """
    text = text.replace("\n", "")
    hasher = md5()
    hasher.update(text.encode())
    return hasher.hexdigest()



class Client:
    """ Client class for gui and socket """

    def __init__(self):
        self.read_conf()
        self.is_receiving = False
        self.is_connected = False
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.gui_loop()

    def read_conf(self):
        """ Read configuration file """
        conf = ConfigParser()
        try:
            conf_file = get_conf_file()
            conf.read(conf_file)
            self.chat_db = conf_file.replace("gpt.ini", "chat.db")
            self.host = conf.get("CLIENT", "HOST")
            self.port = conf.getint("CLIENT", "PORT")
        except Exception as exc:
            tkinter.messagebox.showerror("Error", f"Error: {exc}")
            sys.exit(4)

    def gui_loop(self):
        """ UI loop (void) """
        self.win = tkinter.Tk()
        self.win.title("GPT")
        self.win.configure(bg=DARK_BLUE)
        left_frame = tkinter.Frame(self.win, width=200, height=450, bg=LIGHT_BLUE)
        left_frame.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        right_frame = tkinter.Frame(self.win, width=650, height=450, bg=LIGHT_BLUE)
        right_frame.grid(row=0, column=1, columnspan=2, padx=5, pady=10)
        input_frame = tkinter.Frame(self.win, width=655, height=50, bg=LIGHT_BLUE)
        input_frame.grid(row=1, column=1, padx=10, pady=5)
        tkinter.Label(left_frame, text="Previous Chats", font=BANNER_FONT, bg=LIGHT_BLUE, fg=YELLOW).grid(row=0, column=0, padx=5, pady=5)
        self.prev_chat_listbox = tkinter.Listbox(left_frame, width=20, height=29)
        self.prev_chat_listbox.grid(row=1, column=0, padx=0, pady=5)
        prev_chat_sb = tkinter.Scrollbar(left_frame)
        prev_chat_sb.grid(row=1, column=1, padx=0, pady=5, sticky=tkinter.NS)
        self.prev_chat_listbox.config(yscrollcommand=prev_chat_sb.set)
        prev_chat_sb.config(command=self.prev_chat_listbox.yview)
        self.update_prev_chats()
        restore_button = tkinter.Button(left_frame, text="Restore", bg=BUTTON[0], fg=BUTTON[1], command=self.restore)
        restore_button.grid(row=2, column=0, columnspan=2, padx=2, pady=5)
        tkinter.Label(right_frame, text="Chat", font=BANNER_FONT, bg=LIGHT_BLUE, fg=YELLOW).grid(row=0, column=3, padx=5, pady=5)
        exit_button = tkinter.Button(right_frame, text="Exit", bg=BUTTON[0], fg=BUTTON[1], command=self.prompt_stop)
        exit_button.grid(row=0, column=5, padx=2, pady=5)
        self.text_area = tkinter.scrolledtext.ScrolledText(right_frame)
        self.text_area.grid(row=1, column=1, columnspan=5, padx=20, pady=5)
        self.text_area.config(state="disabled")
        save_button = tkinter.Button(right_frame, text="Save", bg=BUTTON[0], fg=BUTTON[1], command=self.save)
        save_button.grid(row=2, column=2, columnspan=2, padx=2, pady=5)
        clear_button = tkinter.Button(right_frame, text="Clear", bg=BUTTON[0], fg=BUTTON[1], command=self.prompt_clear)
        clear_button.grid(row=2, column=3, columnspan=2, padx=2, pady=5)
        self.input_area = tkinter.Text(input_frame, height=3)
        self.input_area.grid(row=3, column=1, padx=5, pady=5)
        self.input_area.focus()
        send_button = tkinter.Button(input_frame, text=" Ask ", bg=BUTTON[0], fg=BUTTON[1], command=self.ask)
        send_button.grid(row=3, column=3, padx=5, pady=5)
        self.win.bind("<Return>", lambda event=None: send_button.invoke())
        self.win.protocol("WM_DELETE_SELF.WINDOW", self.prompt_stop)
        self.win.wm_attributes("-topmost", True)
        self.win.mainloop()

    def restore(self):
        """ Restore prev chat (void) """
        if self.is_receiving:
            return
        try:
            index = self.prev_chat_listbox.curselection()
            label = self.prev_chat_listbox.get(index)
            content = self.get_chat(label)
            existing_content = self.text_area.get("1.0", tkinter.END)[0:-1]
            if not len(existing_content.strip()) > 0:
                self.add_msg(content)
                return
            if self.chat_exists(existing_content):
                self.clear_chat()
                self.add_msg(content)
                return
            save = tkinter.messagebox.askyesno("Warning", "Save current content?", parent=self.win)
            if save:
                self.save()
            self.clear_chat()
            self.add_msg(content)
        except Exception as exc:
            return

    def prompt_clear(self):
        """ clear chat area with prompt if not empty (void) """
        if self.is_receiving:
            return
        content = self.text_area.get("1.0", tkinter.END)[0:-1]
        if not len(content.strip()) > 0:
            return
        if self.chat_exists(content):
            self.clear_chat()
            return
        save = tkinter.messagebox.askyesno("Warning", "Save current content?", parent=self.win)
        if save:
            self.save()
        self.clear_chat()

    def clear_chat(self):
        """ Clear text area (void) """
        self.text_area.config(state="normal")
        self.text_area.delete("1.0", tkinter.END)
        self.text_area.config(state="disable")

    def save(self):
        """ Save Chat (void) """
        if self.is_receiving:
            return
        content = self.text_area.get("1.0", tkinter.END)
        if not len(content.strip()) > 0:
            return
        if self.chat_exists(content[0:-1]):
            return
        label = tkinter.simpledialog.askstring("Chat Label", "What would you like to label this conversation?", parent=self.win)
        if label is None:
            return
        digest = hash_of(content)
        conn = sqlite3.connect(self.chat_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chats (label TEXT, hash TEXT, content TEXT)")
        cursor.execute("INSERT INTO chats VALUES (?, ?, ?)", (label, digest, content))
        conn.commit()
        conn.close()
        self.update_prev_chats()

    def update_prev_chats(self):
        """ Update listbox (void) """
        chat_labels = self.get_chat_labels()
        self.prev_chat_listbox.delete(0, tkinter.END)
        for index, item in enumerate(chat_labels):
            self.prev_chat_listbox.insert(index, item[0])

    def prompt_stop(self):
        """ Stop client with prompt to save (void) """
        self.is_connected = False
        self.prompt_clear()
        self.stop()

    def stop(self, exit_code=0):
        """ Stop client (void) """
        self.is_connected = False
        self.sock.close()
        self.win.destroy()
        sys.exit(exit_code)

    def ask(self):
        """ Ask server question (void) """
        try:
            if self.is_receiving:
                return
            input_txt = self.input_area.get("1.0", "end").replace("\n", "")
            if input_txt == "":
                return
            if not self.is_connected:
                self.connect()
                if not self.is_connected:
                    return
            msg = f"{input_txt}<END>"
            self.input_area.delete("1.0", "end")
            self.add_msg(f"{to_iso_format(int(time.time()))}: {input_txt}\n\n")
            self.sock.sendall(msg.encode())
            recv_thread = Thread(target=self.recv)
            recv_thread.start()
        except Exception as exc:
            print(exc)
            self.stop(2)

    def recv(self):
        """ Receive message from server (void) """
        self.is_receiving = True
        self.input_area.config(state="disabled")
        try:
            response = ""
            while True:
                if not self.is_connected:
                    self.is_receiving = False
                    return
                data = self.sock.recv(5).decode()
                response += data
                if "<END>" in response:
                    self.add_msg(data + "\n")
                    break
                if response == "\n":
                    response = ""
                else:
                    self.add_msg(data)
            self.add_msg("\n")
            self.input_area.config(state="normal")
            self.is_receiving = False
        except ConnectionAbortedError:
            print("Connection aborted by server")
            self.stop(1)
        except Exception as exc:
            print(exc)
            self.stop(1)

    def add_msg(self, msg):
        """ Add message to text area (void) """
        self.text_area.config(state="normal")
        self.text_area.insert("end", msg)
        self.text_area.yview("end")
        self.text_area.config(state="disabled")

    def connect(self):
        """" Connect to server (void) """
        try:
            self.sock.connect((self.host, self.port))
            resp = self.sock.recv(5).decode()
            if resp == SIGNAL_BUSY:
                self.add_msg("Server is busy.\n\n")
                self.sock.close()
                self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            else:
                self.is_connected = True
        except Exception as exc:
            print(f"Error: {exc}")
            self.stop(3)

    def get_chat_labels(self):
        """ Get labels from DB ([[str, str, str]]) """
        conn = sqlite3.connect(self.chat_db)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS chats (label TEXT, hash TEXT, content TEXT)")
        cursor.execute("SELECT label, hash FROM chats")
        chat_lables = cursor.fetchall()
        conn.close()
        return chat_lables

    def chat_exists(self, chat):
        """ Does chat exist in DB (bool) """
        digest = hash_of(chat)
        labels = self.get_chat_labels()
        for label in labels:
            if digest == label[1]:
                return True
        return False

    def get_chat(self, label):
        """ Get chat from DB with label=label (str) """
        conn = sqlite3.connect(self.chat_db)
        cursor = conn.cursor()
        cursor.execute(f"SELECT content FROM chats WHERE label='{label}'")
        content = cursor.fetchall()[0][0]
        conn.close()
        return content



client = Client()
