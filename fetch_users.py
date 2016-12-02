import re
import datetime
import pymysql
import argparse

'''
Import user profiles to create an user collecton.
'''
def import_from_sql_dump(path):
    with open(path, 'r', encoding = 'utf-8') as f:

        records=[]
        lines = f.readlines()
        for line in lines:
            m = re.search("\s+\(\d+, '(.+)', \d+, \d+, \d+, '([0-9\-\: ]+)', "
                    + "", line)
            if m:
                uname = m.group(1)
                create_time = datetime.datetime.strptime(
                        m.group(2), '%Y-%m-%d %H:%M:%S')

                records.append('{"uname":"' + uname \
                    + '","create_time":"' + str(create_time) + '"}')
        return '[' + ',\n'.join(records) + ']'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--import_from_sql_dump', action='store')
    parser.add_argument('-o', '--output', action='store', default='users.json')
    args = parser.parse_args()

    if args.import_from_sql_dump:
        result = import_from_sql_dump(args.import_from_sql_dump)

    else:
        host = '58.68.249.183'
        user = 'qifun'
        passwd = 'oNEfbCcc'
        db = 'slg_game1'

        conn = pymysql.connect(host=host,user=user,passwd=passwd,db=db,port=3306,charset='utf8') 
        cur = conn.cursor()

        cur.execute("SELECT account,create_date,login_date FROM player_account")

        result = []
        for row in cur.fetchall():
            result.append('{{"uname":"{0}","create_time":"{1}","login_time":"{2}"}}\n'.format(*row))
        result = '[' + ','.join(result) + ']'

        cur.close()
        conn.close()

    with open(args.output, 'w', encoding = 'utf-8') as f:
        f.write(result)

