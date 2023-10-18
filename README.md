# Assistant - GGUF LLM server and client (Commandline and GUI)


## Description  

Server and associated client programs to run open-source large language models (LLM) locally on your machine. Client programs allow access to query the LLM via commandline and a GUI application. If using Windows to run the client program, only use `gui/client_gui.pyw`.


## File Structure

### Server (Linux only)
* **Models:** Place models in `~/.local/share/assistant/models/`.
* **Logs:** Logs will be placed in `~/.local/share/assistant/logs/`.

### Client
* **Config:** Config file (`gpt.ini`) will be placed in `~/.config/gpt-client/`. *Note: This is the conf file for the commandline and GUI application.*
* **Database:** Used to hold conversations if saved in GUI application

## Setup

### Server

*Note*: Recommend using Pop-OS as GPU integration will be easier if desired. As is, the server uses the CPU for model processing. Performance will vary depending on CPU, RAM, etc..

1. Clone repository: `git clone https://github.com/jandrus/assistant` 
1. Install requirements:
   1. `pip install llama-cpp-python`
1. Create model directory: `mkdir -p ~/.local/share/assistant/models`
1. Navigate to model directory: `cd ~/.local/share/assistant/models`
1. Download desired model.
   1. Example: `wget https://huggingface.co/TheBloke/OpenOrca-Platypus2-13B-GGUF/resolve/main/openorca-platypus2-13b.Q4_K_M.gguf` *This model runs well, but a decent CPU and RAM are required. If this is too slow, use a 7B model.*
1. Navigate back to previous directory: `cd -`
1. Navigate to *assistant*: `cd assistant`
1. Execute Server: `python3 assistant.py`

*Note: Get the server ip address (`ip a`). This will be required by the client program.*

### Client (Separate machine from server)

1. Clone repository: `git clone https://github.com/jandrus/assistant`
1. Install requirements (Only required for terminal app `client.py`):
   1. Arch based: `sudo pacman -S python-termcolor python-colorama`
   1. Debian based: `sudo apt install python3-termcolor python3-colorama`
1. Navigate to *assistant*: `cd assistant`
1. Execute Client (Linux):
    1. Terminal: `python3 client.py`
    1. GUI: `python3 gui/client_gui.py`
1. Execute Client (Windows):
    1. Windows users will have to install python3, if not already installed. 
    1. Navigate to the `assistant/gui` folder and execute `client_gui.pyw`. 


## Donate  

* XMR: 84t9GUWQVJSGxF8cbMtRBd67YDAHnTsrdWVStcdpiwcAcAnVy21U6RmLdwiQdbfsyu16UqZn6qj1gGheTMkHkYA4HbVN4zS

* BTC: bc1q7y20wr2n5qt2fxe569llvz5a0qsnpsz4decplr


## TODO  

* Clean up error handling
* Modernize GUI


## License

Assistant - GGUF LLM server and client Copyright (C) 2023 James Andrus Email: jandrus@citadel.edu

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see http://www.gnu.org/licenses/.
