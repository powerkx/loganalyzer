'''
Created on Nov 23, 2016

Copy all csv result files of the newest folder in dir to dest
  dir: loganalyzer_export/result_csv
  dest: slg_osprey/result_csv

@author: David Wang
'''

import os
import glob
import shutil
import re

# Create 
def create_json(csv_filename, periods, items, items_length, item_name):
    list_results = [[] for i in range(items_length)]
    content = ''
    json = '['
    i = 0
    j = 0
    k = 0
    
    with open(csv_filename, 'r') as f:
        for line in f:
            search_default = re.search(r'(.*?,\d+,\d+,\d+,\d+)', line, re.M|re.I)
            if search_default == None: continue
            content += search_default.group(1) + '\n'

    for line in content.split('\n'):
        result = re.search( r'(.*?),(\d+),(\d+),(\d+),(\d+)', line, re.M|re.I)
        if result:
            list_results[i].append(result.group(1))
            list_results[i].append(int(result.group(2)))
            list_results[i].append(int(result.group(3)))
            list_results[i].append(int(result.group(4)))
            list_results[i].append(int(result.group(5)))
            print(list_results[i])
            i += 1
    
    for j in range(4):

        json += '{"id":'+str(j+1)+',"period":"'+periods[j]+'","'+item_name+'":['
        for k in range(items_length):
            json += '{"name":"'+items[k]+'","value":'+str(list_results[k][j+1])+'},'
            k += 1
        json += ']},'
        j += 1
    json += ']'
    json = json.replace('},]', '}]').replace('\\', '')
    return json

def get_value(pattern, content):
    m = re.search(pattern, content)
    if m:
        return m.group(1)
    else:
        return ''

dir = "/home/wangmeng/loganalyzer_export/result_csv"
dest = "/home/wangmeng/loganalyzer_export/slg_osprey/result_csv"
dist = "/home/wangmeng/loganalyzer_export/slg_osprey/data"


newest_result_csv_folder = max(glob.glob(os.path.join(dir, '*/')), key=os.path.getmtime)
newest_result_csv_files = os.listdir(newest_result_csv_folder)

for f in newest_result_csv_files:
    full_f_name = os.path.join(newest_result_csv_folder, f)
    if (os.path.isfile(full_f_name)): shutil.copy(full_f_name, dest)

    
# create update info file
new_name = newest_result_csv_folder.replace(dir, "").replace("/", "")
searchObj = re.search( r'(\d+?)-(\d+?)-(\d+?)-(\d\d)00', new_name, re.M|re.I)
if searchObj:
    year = searchObj.group(1)
    month = searchObj.group(2)
    day = searchObj.group(3)
    hour = searchObj.group(4)
else:
    print ("Nothing found!!")

content = year+"年"+month+"月"+day+"日00:00至"+hour+":00"
with open(dist+'/update_info.txt', 'w') as f:
    f.write(content)

'''   
Create users.json for filling data table
  data source: result_csv/users.csv
'''
flag_patterns = [
    'Redirected unames: (\d+)',
    'New users: (\d+)',
    'Verteran users: (\d+)', 
    'Missing users with logs: (\d+)',
    'Missing unames without logs: (\d+)'
]
progress = [
    '跳转快玩用户数',
    '跳转新用户数（创建时间在区间内）',
    '跳转老用户数（创建时间在区间外）',
    '有日志的丢失用户（未创角）',
    '没有日志的丢失用户'
]

record = ''
content = '['
total = '0'
i = 1

with open(dest+'/users.csv', 'r') as f:
    try:
        record = f.read()
    except:
        print("读取users.csv错误")

total = float(re.search( r'Redirected unames: (\d+)', record, re.M|re.I).group(1))

for pattern in flag_patterns:
    value = float(get_value(pattern, record))
    if total !=0: 
        percentage = '%.2f' % ((value/total)*100)
    else:
        percentage = 0
    print(percentage)
    content += '{"id":'+str(i)+',"progress":"'+progress[i-1]+'","value":'+str(value)+',"percentage":"'+str(percentage)+'%"},'
    i += 1

content += "]"
content = content.replace('},]', '}]').replace('\\', '')

with open(dist+'/users.json', 'w') as f:            
    f.write(content)

'''
Create user-event.json for filling user_event bar chart 
  data source: result_csv/user-event.csv
'''
content = '['
i = 1
with open(dest+'/user_event.csv', 'r') as f:
    for line in f:
        if re.search( r'{(.*?)}', line, re.M|re.I): continue
        
        search_redirect = re.search(r'redirect,(\d+)', line, re.M|re.I)
        search_default = re.search(r'(.*?)\|(\d+)', line, re.M|re.I)
        if search_redirect:
            content += '{"id":'+str(i)+',"event":"跳转","value":"'+str(search_redirect.group(1))+'"},'
        elif search_default:
            content += '{"id":'+str(i)+',"event":"'+str(search_default.group(1).replace('"', ''))+'","value":"'+str(search_default.group(2))+'"},'
        else:
            print("错误的user_event的csv格式，第"+i+"行。")
        i += 1        
    
content += "]"
content = content.replace('},]', '}]').replace('\\', '')

with open(dist+'/user_event.json', 'w') as f:            
    f.write(content)
    
'''
Create quality.json for filling quality bar/pie chart 
  data source: result_csv/quality.csv
'''
periods = ['新手关', '主城', '世界地图', '战斗']
items = ['流畅', '标准', '优质', '精美']
quality_json = create_json(dest+'/quality.csv', periods, items, len(items), 'quality')
print(quality_json)
with open(dist+'/quality.json', 'w') as f:            
    f.write(quality_json)

'''
Create fps.json for filling fps bar/pie chart 
  data source: result_csv/fps.csv
'''
periods = ['新手关', '主城', '世界地图', '战斗']
items = ['0-5', '5-10', '10-15', '15-20', '20-25', '25-30', '30-35', '35-40', '40-45', '45-50', '50-55', '55-60', '60以上']
fps_json = create_json(dest+'/fps.csv', periods, items, len(items), 'fps')
print(fps_json)
with open(dist+'/fps.json', 'w') as f:            
    f.write(fps_json)

'''
Create memory.json for filling memory bar/pie chart 
  data source: result_csv/memory.csv
'''
periods = ['新手关', '主城', '世界地图', '战斗']
items = ['0-50', '50-100', '100-150', '150-200', '200-250', '250-300', '300-350', '350-400', '400-450', '450-500', '500-550', '550-600', '600以上']
memory_json = create_json(dest+'/memory.csv', periods, items, len(items), 'memory')
print(memory_json)
with open(dist+'/memory.json', 'w') as f:            
    f.write(memory_json)



