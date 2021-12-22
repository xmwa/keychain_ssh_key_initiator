#!/usr/bin/env python3
import subprocess as sp
from pathlib import Path
import os, sys, string, random

def write_to_clipboard(output):
    process = sp.Popen('pbcopy', env={'LANG': 'en_US.UTF-8'}, stdin=sp.PIPE)
    process.communicate(output.encode('utf-8'))

def print_help():
    print("Usage: ssh_key_initiator <key file path> <key comment> <user@server.com> <config file host alias> [port]")
    print("Usage: ssh_key_initiator -g <key file path> <key comment> => generate a ssh key and store the passphrase to keychain, public key shall be copied to clipboard")
    exit(1)

if Path("/System/Applications/Utilities/Keychain Access.app").exists():
    ext="_keychain_rsa"
else:
    ext="_rsa"
if len(sys.argv) == 1:
    print_help()
if sys.argv[1]=="-g":
    if len(sys.argv)<4:
        print_help()
    gen_mode=True
    filename=os.path.expanduser(sys.argv[2])+ext
    comment=sys.argv[3]
else:
    if len(sys.argv)<5:
        print_help()
    gen_mode=False
    filename=os.path.expanduser(sys.argv[1])+ext
    comment=sys.argv[2]
    server=sys.argv[3]
    hostalias=sys.argv[4]
    if len(sys.argv)==5:
        port=str(22)
    else:
        port=sys.argv[-1]
if Path(filename).exists():
    print("The key file"+filename+" already exists. Please remove it first.")
    exit(1)
pw_len=1023#max size to be 1023
pw=''.join(random.choices(string.ascii_letters + string.digits, k = pw_len))
sp.run(["ssh-keygen","-b", "4096", "-C", comment, "-f", filename, "-t", "rsa", "-q", "-N", pw], check=True)
write_to_clipboard(pw)
#may not have to install brew install theseal/ssh-askpass/ssh-askpass
print("[Paste the password to the ssh-add command prompt]")
sp.run(["ssh-add","--apple-use-keychain",filename], check=True)
sp.run(["ssh-add","--apple-load-keychain",filename], check=True)
if gen_mode:
    with open(filename+".pub", "r") as f:
        pubkey=f.read()
    print("[Public key copied to clipboard]")
    write_to_clipboard(pubkey)
    exit()
copy_id=sp.run(["ssh-copy-id", "-p", str(port), "-i", filename, "-o", "StrictHostKeyChecking=no", "-o", "UserKnownHostsFile=/dev/null", server], check=True)
if not copy_id.returncode==0:
   print("[ssh-copy-id failed]")
   exit(1)

username=server.split("@")[0]
serverip=server.split("@")[1]
config_str="Host "+hostalias+"\n\tHostName "+serverip+"\n\tPort "+str(port)+"\n\tUser "+username+"\n\tIdentityFile "+filename+"\n\tUseKeychain yes\n\t"+"IdentitiesOnly yes\n\tStrictHostKeyChecking no\n\tUserKnownHostsFile /dev/null\n\tLogLevel ERROR\n"
sp.run("echo '"+config_str+"' >> ~/.ssh/config", shell=True, check=True)
if Path("/opt/homebrew/bin/code").exists():
    sp.run("/opt/homebrew/bin/code -n ~/.ssh/config", shell=True, check=True)
else:
    sp.run("vi ~/.ssh/config", shell=True, check=True)