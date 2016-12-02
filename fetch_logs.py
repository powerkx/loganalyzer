import os
import re
import argparse
import datetime

from paramiko import * 
from scp import SCPClient

def fetch_files(host, username, password, src_folder, dst_folder, targets):
    ssh = SSHClient()
    ssh.set_missing_host_key_policy(AutoAddPolicy())

    print('Connecting to ', host)
    ssh.connect(host, username=username, password=password)
    print('Host connected. ', host)

    scp = SCPClient(ssh.get_transport())

    if not os.path.exists(dst_folder):
        os.makedirs(dst_folder)

    for target in targets: 
        src_path = src_folder + target 
        print('Fetching file ', src_path, ' -> ', dst_folder)
        scp.get(src_path, dst_folder, recursive=True, preserve_times=True)

    scp.close()
    print('Connection closed.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--dst-folder', action='store', default='logs')
    parser.add_argument('targets', nargs='*', action='store', default=['*'])
    args = parser.parse_args()

    host = '58.68.249.250'
    #username = 'huyu'
    #password = 'qifunt3st3r'
    username = 'root'
    password = 'chinacache@123.com'
    src_folder = '/opt/tomcat8/webapps/ROOT/client_message/'
    
    fetch_files(host, username, password, 
            src_folder, args.dst_folder, args.targets)
