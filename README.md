# SOFTENG 364 Assignment 2: CoconutTalk

A chatting program developed for SOFTENG 364 Assignment 2.

## Description

This is a chatting program which uses python to allow chatting between clients connected to a server. It supports full
encryption with the connection between clients and the server, and hence the chats between clients are also encrypted. 

The program allows clients to interact with other clients by direct chatting with them or creating, inviting, and 
joining group chats. This is done by a GUI program developed using PyQt5. 

## Getting Started

### Dependencies

- Python 3.7 or above
- PyQt5

### Installing

Clone the following repository using preferred method of Git commands, and the program will be contained inside 
the directory called "coconuttalk". 

Through terminal, you can do this by typing in the following command in the terminal opened to the
directory you want to install this program:

```bash
git clone https://github.com/SOFTENG-364-2021/assignment2_pychat-hpar461.git
```

### Executing program

Essentially, open terminal and run `main.py` in the `coconuttalk` directory inside the root directory of this repository.

Before running the program, make sure the command used to run python is actually python 3.
To do this, you can run the command: `python --version` to see what version of the python your computer is running.

**On Mac computers, python 3 can be run by using the command `python3` rather than `python`. Please use 
`python3 --version` to check python 3 version and use `python3` instead for every python operation of this application.*

Assuming Python is installed on your computer AND the current working directory of the terminal window is set to the 
root directory of the repository, the method to run this application through terminal is as follows:

```bash
python coconuttalk/main.py
```

In case of Mac, it's as follows:

```bash
python3 coconuttalk/main.py
```