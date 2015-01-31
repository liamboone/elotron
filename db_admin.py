#!/usr/bin/env python
import sys
import time
import subprocess
import os
import argparse

db_data = {}
path = '.'

time_stamp = time.strftime("%Y_%m_%d")

def get_path(db_name):
    out_dir = path + '/' + db_name + '/' + time_stamp + '/' 
    return out_dir

def get_db_descriptions():
    with open(path + '/db_desc.txt', 'r') as f:
        for line in f:
            print line
            words = line.split() 
            if len(words) == 0 or words[0] == '#':
                continue

            name = words[0]
            uri = words[1]
            db_name = words[2]
            user = words[3]
            pw = words[4]

            db_data[name] = {'uri': uri,
                        'db_name':db_name,
                        'user':user,
                        'pw':pw}

def backup(args):
    print args

    if args['dbs'] == '*':
        args['dbs'] = db_data.keys()


    for db_name in args['dbs']:
        db = db_data[db_name]
        out_dir = get_path(db_name) 
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        cmdstring = ['mongodump',
                '-h', db['uri'],
                '--db', db['db_name'],
                '-o', out_dir]

        if db['user'] != 'None':
            cmdstring += ['-u' + db['user']]
        if db['pw'] != 'None':
            cmdstring += ['-p' + db['pw']]

        print cmdstring
        subprocess.call(cmdstring)

def copy(args):
    print args

    source = args['src']
    dest = args['dest']

    bk_args = {}
    bk_args['dbs'] = [source, dest]

    backup(bk_args)

    source_dir = get_path(source)

    dest_db = db_data[dest]

    cmdstring = ['mongorestore',
                '--drop',
                '-h', dest_db['uri'],
                '--db', dest_db['db_name']]

    if dest_db['user'] != 'None':
        cmdstring += ['-u', dest_db['user']]
    if dest_db['pw'] != 'None':
        cmdstring += ['-p', dest_db['pw']]
    cmdstring += [source_dir + '/' + db_data[source]['db_name'] + '/.']
    print cmdstring
    subprocess.call(cmdstring)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Automates database administration operations')

    subparsers = parser.add_subparsers(help='sub-command help')
    parser.add_argument('--backup_path', required=True,
                            help='Directory to store backups')
    parser_bk = subparsers.add_parser('backup', help='backup help')
    parser_copy = subparsers.add_parser('copy', help='copy help')

    parser_bk.add_argument('dbs', default='*', nargs='*')
    parser_copy.add_argument('--src', required=True, 
                            help='Source database')
    parser_copy.add_argument('--dest', required=True,
                            help='Destination database (WILL BE OVERWRITTEN)')

    parser_bk.set_defaults(func=backup)
    parser_copy.set_defaults(func=copy)
    args = parser.parse_args(sys.argv[1:])
    path = args.backup_path
    get_db_descriptions()
    
    args.func(vars(args)) 
    #backup(sys.argv[1])
