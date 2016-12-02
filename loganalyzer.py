import os
import sys
import re
import copy
import datetime
import argparse
import json
import pymongo
from bson.code import Code

client = pymongo.MongoClient()
db = client.slglog

'''
Import user profiles to create an user collecton.
'''
def import_users(path):
    with open(path, 'r', encoding = 'utf-8') as f:

        users = json.load(f)
        for user in users:
            uname = user['uname']
            create_time = datetime.datetime.strptime(
                    user['create_time'], '%Y-%m-%d %H:%M:%S')
            login_time = datetime.datetime.strptime(
                    user['login_time'], '%Y-%m-%d %H:%M:%S')
            db.user.update_one(
                        {
                            'uname' : uname,
                        }, 
                        {
                            '$set' : { 
                                'create_time' : create_time,
                                'login_time' : login_time
                            }
                        },
                        upsert=True)
            print(','.join([uname, str(create_time)]))
     
        db.user.create_index('uname')
        db.user.create_index('create_time')
        db.user.create_index('login_time')

'''
Import redirect records to create a redirect collection.
'''
def import_redirects_json(path):
    print('Importing redirects from', path)

    with open(path, 'r', encoding = 'utf-8') as f:
        # Clean up
        db.redirect.drop()

        redirects = json.load(f)

        for redirect in redirects:
            uname = redirect['uname']
            uuid = redirect['uuid']
            redirect_time = datetime.datetime.strptime(
                redirect['redirect_time'], '%Y-%m-%d %H:%M:%S')
            db.redirect.insert(
                    {
                        'uname' : uname,
                        'uuid' : uuid,
                        'redirect_time' : redirect_time 
                    })

            print(','.join([uname, uuid, str(redirect_time)]))

        db.redirect.create_index('uname')
        db.redirect.create_index('redirect_time')

'''
Import redirect records to create a redirect collection.
'''
def import_redirects(path):
    print('Importing redirects from', path)

    with open(path, 'r', encoding = 'utf-8') as f:

        lines = f.readlines()

        for line in lines:
            print(line)
            redirect=json.loads(line)
            uname = redirect['uname']
            uuid = redirect['uuid']
            ip = redirect['ip']
            redirect_time = datetime.datetime.strptime(
                redirect['redirect_time'], '%Y-%m-%d %H:%M:%S.%f')
            db.redirect.update_one(
                    {
                        'uuid' : uuid
                    },
                    {
                        '$set' : {
                            'uname' : uname,
                            'uuid' : uuid,
                            'ip' : ip,
                            'redirect_time' : redirect_time
                        }
                    },
                    upsert=True)

            print(','.join([uname, uuid, ip, str(redirect_time)]))

        db.redirect.create_index('uname')
        db.redirect.create_index('ip')
        db.redirect.create_index('redirect_time')


'''
Import event definition file to create an event_def collection.
'''
def import_event_def(path):
    with open(path, 'r', encoding='utf-8') as f:
        # Clean up
        db.event_def.drop()
        
        event_def = json.load(f)

        order = 0
        for e in event_def:
            if 'name' not in e:
                e['name'] = e['pattern']
            e['order'] = order # Generate order for events
            order += 1
            db.event_def.insert_one(e) # name, pattern, order

        db.event_def.create_index('name')
        db.event_def.create_index('pattern')
        db.event_def.create_index('order')

'''
Import stage definition file to create an stage_def collection.
'''
def import_stage_def(path):
    with open(path, 'r', encoding='utf-8') as f:
        # Clean up
        db.stage_def.drop()
        
        stage_def = json.load(f)

        order = 0
        for s in stage_def:
            s['order'] = order
            db.stage_def.insert_one(s) # uname, enter_event, leave_event
            order += 1

        db.stage_def.create_index('uname')
        db.stage_def.create_index('enter_event')
        db.stage_def.create_index('leave_event')

'''
Clean up session and messages associated with the uuid and ip.
'''
def cleanup_session_and_messages(uuid, ip):

    db.session.delete_many({'uuid' : uuid, 'ip' : ip})
    db.message.delete_many({'uuid' : uuid, 'ip' : ip})
    
'''
Import session and messages to session and message collections.
'''
def import_session_and_messages(uuid, ip, lines):

    for line in lines:
        message = json.loads(line)

        # Append meta key
        message['uuid'] = uuid
        message['ip'] = ip

        if 'os' in message: # Use 'os' to check if it's a meta
            regulate_session(message)
            session = db.session.find_one(
                    {
                        'uuid' : uuid,
                    })
            if session:
                merge_session_fields(session, message)

                db.session.replace_one(
                        {
                            '_id' : session['_id']
                        },
                        session)    
            else:
                db.session.insert_one(message)

        else: 
            regulate_message(message)
            db.message.insert_one(message)

    session = db.session.find_one(
        {
            'uuid' : uuid
        })
    if not session:
        print('No session found for {0}. Create a stub one'.format(uuid))
        # Use the first message as the template
        message = json.loads(lines[0])
        regulate_message(message)
        db.session.insert_one(
                {
                    'uuid' : uuid, 
                    'uname' : message['uname'],
                    'create_time' : message['create_time'],
                    'os' : 'null', 'fp_type' : 'null', 'browser' : 'null', 
                    'fp_version' : 'null', 'fp_manufacturer' : 'null', 'url' : 'null'
                })

    for field in ['uuid', 'uname', 'create_time', 'os', 'browser', 'url', 
                'fp_type', 'fp_version', 'fp_manufacturer']:
        db.session.create_index(field)
    for field in ['uuid', 'ip', 'create_time', 'memory', 'fps', 'quality']:
        db.message.create_index(field)


def get_distinct_meta(field):
    return collection.find(
            {'os' : {'$exists' : True},
             field : {'$exists': True}},
            {field : True}).distinct(field)

def print_distinct_unames():
    posts = get_distinct_meta('uName')
    for post in posts:
        print(post) 


''' 
Import log files to meta and message collections.
'''
def import_logs(paths):

    for folder in paths:
        for filename in os.listdir(folder):
            if filename[-4:] != '.log':
                print('!!! File name does not end with .log! ' + filename)
                continue

            try:
                uuid, ip = parse_uuid_ip(filename)
            except Exception as e:
                print(e)
                continue

            path =  os.path.join(folder, filename)
            with open(path, 'r', encoding='utf-8') as f:

                cleanup_session_and_messages(uuid, ip)

                try:
                    lines = f.readlines()
                except Exception as e:
                    print(e)
                    continue
                
                cleanup_session_and_messages(uuid, ip)
                import_session_and_messages(uuid, ip, lines)

            print('### File imported:' + filename)

'''
Utility to parse uuid and ip.
'''
def parse_uuid_ip(filename):

    m = re.search('^(\d+\.\d+\.\d+\.\d+)_(.*).log$', filename)

    if m is None:
        raise Exception('!!! Failed to parse IP or UUID!  ' + filename)

    ip = m.group(1)
    uuid = m.group(2)

    # Check new UUID format
    m = re.search('^[0-9a-z]{32}$', uuid)
    if m is None:
        # Check old UUID format
        m = re.search('^kw_[\d]+', uuid)
        if m is None:
            raise Exception('!!! Invalid UUID!  ' + uuid)

    return uuid,ip

'''
Utility to guess uname from uuid.
'''
def guess_uname(uuid):
    # Have fun
    for pattern in [
                '^(kw_\d{4}\d+)147\d*\d{10}$', 
                '^(kw_\d{4}\d+)148\d*\d{10}$',
                '^(kw_\d{4}\d+)14\d*\d{11}$',
                '^(kw_\d{4}\d+)1\d{14}$', 
                '^(kw_\d{4}\d+)1\d{13}$']:
            m = re.search(pattern, uuid)
            if m:
                print('Guess uname from uuid:' + uuid + ' -> ' + m.group(1))
                return  m.group(1) 
            else:
                None

'''
Try to guess and update unames if they are missing.
'''
def update_unames():

    sessions = db.session.find(
            {'os' : {'$exists' : True},
             'uname' : {'$exists': False}},
            modifiers = {"$snapshot" : True})
    for session in sessions:
        uuid = session['uuid']
        uname = guess_uname(session['uuid'])
        if uname:
            db.session.update_one(
                    {
                        '_id' : session['_id']
                    },
                    {
                        '$set': {'uname' : uname}
                    })
        else:
            print('??? Could not determine uname: ' + uuid)

'''
Try to update create_time for sessions with earliest log create time.
'''
def update_session_create_time():
    data_set = db.message.aggregate(
            [{
                '$group' : {
                    '_id' : '$uuid', 
                    'min_create_time' : {'$min' : '$create_time'}
                }
            }])
    for e in data_set:
        session = db.session.find_one(
                {
                    'uuid' : e['_id']
                })
        if session is not None \
                and session['create_time'] > e['min_create_time']:
            print('session ' + session['uuid'] \
                    + ' create time ' + str(session['create_time']) \
                    + ' -> ' + str(e['min_create_time']))
            db.session.update_one(
                    {
                        '_id' : session['_id']
                    },
                    {
                        '$set' : {'create_time' : e['min_create_time']}
                    })


'''
Utility to regulate session fields.
'''
def regulate_session(message):
    mapping = {
            "user_name" : "uname",
            "uName" : "uname",
            "urlPath" : "url",
            "webBrowser" : "browser",
            "version" : "fp_version",
            "playerType" : "fp_type",
            "manufacturer" : "fp_manufacturer",
            "createDate" : "create_time"
    }

    for key in mapping:
        if key in message:
            new_key = mapping[key]
            message[new_key] = message.pop(key)

    message['create_time'] = datetime.datetime.strptime(
            message['create_time'], '%Y-%m-%d %H:%M:%S.%f')
    
'''
Utility to regulate message fields.
'''
def regulate_message(message):
    mapping = {
            "uName" : "uname",
            "nowFrameNum" : "fps",
            "nowFrameQualityNum" : "quality",
            "createDate" : "create_time"
    }

    for key in mapping:
        if key in message:
            new_key = mapping[key]
            message[new_key] = message.pop(key)

    message['create_time'] = datetime.datetime.strptime(
            message['create_time'], '%Y-%m-%d %H:%M:%S.%f')

    m = re.search('(.+)/.+M,.+/.+M', message['memory'])
    if m:
        message['memory'] = float(m.group(1))
    else:
        message['memory'] = -1 

    message['fps'] = float(message['fps'])
    message['quality'] = int(message['quality'])

'''
Utility to merge session fields.
'''
def merge_session_fields(session, field):
    for key in field:
        if key in session and session[key] == 'null' or key not in session:
            if key == 'create_time':
                session[key] = min(session[key], field[key])
            else:
                session[key] = field[key]
            print('Merge meta field ' + key + ' with ' \
                    + field[key] + ' -> ' + session[key])

'''
Utility to find event in messages by pattern matching.
'''
def find_event_in_messages(uuid, pattern):
    e = db.message.find_one(
                {
                    'uuid' : uuid,
                    'message' : {'$regex' : pattern}
                })
    return e

'''
Utility to find events in messages by pattern matching.
'''
def find_events_in_messages(uuid, pattern):
    e = db.message.find(
                {
                    'uuid' : uuid,
                    'message' : {'$regex' : pattern}
                }).sort('create_date', 1)
    return e 

'''
Get sessions in a timeframe.
'''
def get_sessions(start_time, end_time, ips_excluded=[]):
    if start_time and end_time:
        sessions = db.session.find({
                'create_time' : {
                    '$gte' : start_time,
                    '$lt' : end_time
                },
                'ip' : {'$nin' : ips_excluded}
            })
    else:
        sessions = db.session.find({})
    return sessions

'''
Update stage collection for each uuid.
'''
def update_stages(start_time, end_time):
    print('### Update stages')
    sessions = get_sessions(start_time, end_time)

    stage_defs = list(db.stage_def.find({}))
    for session in sessions:
        for stage_def in stage_defs:
            uuid = session['uuid']
            stage_name = stage_def['name']
            enter_event = find_event_in_messages(uuid, stage_def['enter'])
            leave_event = find_event_in_messages(uuid, stage_def['leave'])
            enter_time = enter_event['create_time'] if enter_event else None 
            leave_time = leave_event['create_time'] if leave_event else None 

            result = db.stage.update_one(
                {
                    'uuid' : uuid,
                    'stage_name' : stage_name
                },
                {
                    '$set' : {
                        'uuid' : uuid,
                        'stage_name' : stage_name,
                        'enter_time' : enter_time,
                        'leave_time' : leave_time
                    }
                },
                upsert=True)  
            #print(result.raw_result)
    db.stage.create_index('uuid')
    db.stage.create_index('stage_name')
    db.stage.create_index('enter_time')
    db.stage.create_index('leave_time')

'''
Update event collection for each uuid.
'''
def update_events(start_time, end_time, drop=False): 
    print('### Update events')
    if drop:
        db.event.drop()

    sessions = get_sessions(start_time, end_time)

    event_defs = list(db.event_def.find({}))
    for session in sessions:
        print('Processing session: ', session['uuid'])
        last_events = []
        for event_def in event_defs:
            event_name = event_def['name']
            event_order = event_def['order']
            events = find_events_in_messages(
                    session['uuid'], event_def['pattern'])
            if events.count() > 0:
                current_event = events[0]
                if last_events:
                    interval = -1 
                    current_time = current_event['create_time']
                    # Get the closest interval
                    for e in last_events:
                        if e['create_time'] > current_time:
                            break
                        interval = (current_time 
                                - e['create_time']).total_seconds()

                    if interval >=0 :
                        if drop:
                            result = db.event.insert_one(
                                {
                                    'uuid' : session['uuid'],
                                    'event_name' : event_name,
                                    'uname' : session['uname'],
                                    'event_order' : event_order,
                                    'create_time' : current_time,
                                    'interval' : interval
                                }) 
                        else:  
                            result = db.event.update_one(
                                {
                                    'uuid' : session['uuid'],
                                    'event_name' : event_name,
                                },
                                {
                                    '$set' : {
                                        'uname' : session['uname'],
                                        'event_order' : event_order,
                                        'create_time' : current_time,
                                        'interval' : interval
                                    }
                                },
                                upsert = True) 
                        
            last_events = list(events)

    db.event.create_index('uuid')
    db.event.create_index('uname')
    db.event.create_index('event_name')
    db.event.create_index('event_order')
    db.event.create_index('create_time')
    db.event.create_index('interval')

'''
Update progress collection for each session.
'''
def update_session_progress(start_time, end_time):
    print('### Update session_progress')
    sessions = get_sessions(start_time, end_time)

    for session in sessions:
        progress = -1 
        score_card=[] # record event hit
        interval_card=[] # record interval
        last_event_time = session['create_time']

        event_defs = list(db.event_def.find({}) \
                .sort('order', pymongo.ASCENDING))
        for event_def in event_defs:
            e =  db.event.find_one(
                    {
                        'uuid' : session['uuid'],
                        'event_name' : event_def['name']
                    })
            if e:
                score_card.append(1)
                progress = event_def['order'] 
                if last_event_time:
                    interval = (e['create_time'] 
                            - last_event_time).total_seconds()
                    if interval >=0:
                        interval_card.append((e['create_time'] 
                                - last_event_time).total_seconds())
                    else:
                        interval_card.append(-3)
                else:
                    interval_card.append(-2)
                last_event_time = e['create_time']
            else:
                score_card.append(0)
                interval_card.append(-1)
                last_event_time = None # reset last event

        print(session['uuid'], session['uname'], progress, score_card)
        result = db.session_progress.update_one(
                {
                    'uuid' : session['uuid'],
                },
                {
                    '$set' : {
                        'uname' : session['uname'],
                        'create_time' : session['create_time'],
                        'progress' : progress,
                        'score_card' : score_card,
                        'interval_card' : interval_card
                    }
                },
                upsert=True)
        #print(result.raw_result)

    db.session_progress.create_index('uuid')
    db.session_progress.create_index('uname')
    db.session_progress.create_index('create_time')
    db.session_progress.create_index('progress')
    db.session_progress.create_index('event_name')

'''
Update user_progress collection for each user.
'''
def update_user_progress(start_time, end_time):
    print('### Update users progress')
    # Clean up user_progress collection
    db.user_progress.drop()

    pipeline = []
    if start_time and end_time:
        pipeline.append(
            {
                '$match' : {
                    'create_time' : {
                        '$gte' : start_time,
                        '$lt' : end_time
                    }
                }
            })

    pipeline.append(
        {
                '$group' : {
                    '_id' : '$uname', 
                    'progress' : {'$max' : '$progress'},
                    'uuids' : {'$push' : '$uuid'}
                }
        })

    progress = db.session_progress.aggregate(pipeline)

    for p in progress:
        print(p['_id'] + ',' + str(p['progress']))
        db.user_progress.insert_one(
                {
                    'uname' : p['_id'],
                    'progress' : p['progress'],
                    'uuids' : p['uuids']
                })

    db.user_progress.create_index('uname')
    db.user_progress.create_index('progress')

'''
Update memory collection for each session.
'''
def update_memory(start_time, end_time, new_users_only=True):
    print('### Update memory')
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    for uuid in uuids:
        print('Processing', uuid)
        stages = db.stage.find(
                {
                    'uuid' : uuid
                })
        for stage in stages:
            
            if stage['enter_time'] is None:
                continue
            if stage['leave_time'] is None:
                stage['leave_time'] = datetime.datetime.max 

            data_set = db.message.aggregate([
                    {'$match' : {
                        'uuid' : uuid, 
                        'memory' : {'$gt' : 0},
                        'create_time' : {
                            '$gte' : stage['enter_time'], 
                            '$lt' : stage['leave_time']
                        }
                    }},
                    {'$group' : {
                        '_id' : '$uuid', 
                        'min' : {'$min' : '$memory'},
                        'max' : {'$max' : '$memory'},
                        'avg' : {'$avg' : '$memory'}
                    }}
                ])
            for memory in data_set:
                db.memory.update_one(
                        {
                            'uuid' : uuid,
                        },
                        {
                            '$set' : {
                                'stage_name' : stage['stage_name'],
                                'min' : memory['min'],
                                'max' : memory['max'],
                                'avg' : memory['avg']
                            }
                        },
                        upsert=True)


    for field in ['uuid', 'min', 'max', 'avg', 'stage_name']:
        db.memory.create_index(field)

          
'''
Update fps collection for each session.
'''
def update_fps(start_time, end_time, new_users_only=True, ips_excluded=[]):
    print('### Update fps')
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')


    for uuid in uuids:
        print('Processing', uuid)
        stages = db.stage.find(
                {
                    'uuid' : uuid
                })
        for stage in stages:
            if stage['enter_time'] is None:
                continue
            if stage['leave_time'] is None:
                stage['leave_time'] = datetime.datetime.max 
            
            data_set = db.message.aggregate([
                    {'$match' : {
                        'uuid' : uuid, 
                        'fps' : {'$gt' : 0},
                        'create_time' : {
                            '$gte' : stage['enter_time'], 
                            '$lt' : stage['leave_time']
                        }
                    }},
                    #{'$sort' : {
                    #    'create_time' : 1
                    #}},
                    {'$group' : {
                        '_id' : '$uuid', 
                        'fps_list' : {'$push' :'$fps'},
                        #'create_time_list' : {'$push' :'$create_time'},
                        'min' : {'$min' : '$fps'},
                        'max' : {'$max' : '$fps'},
                        'avg' : {'$avg' : '$fps'}
                    }}
                ])
            for fps in data_set:
                if not fps['fps_list']:
                    continue

                # Calculate upper average fps by remove the half lowest values
                sorted_fps_list = sorted(fps['fps_list'])
                half_count = int(len(sorted_fps_list)/2)
                upper_fps_list = sorted_fps_list[half_count:]
                upper_avg = sum(upper_fps_list)/len(upper_fps_list)

                db.fps.update_one(
                        {
                            'uuid' : fps['_id'],
                        },
                        {
                            '$set' : {
                                'stage_name' : stage['stage_name'],
                                'stage_enter_time' : stage['enter_time'],
                                'stage_leave_time' : stage['leave_time'],
                                'fps_list' : fps['fps_list'],
                                #'create_time_list' : fps['create_time_list'],
                                'min' : fps['min'],
                                'max' : fps['max'],
                                'avg' : fps['avg'],
                                'upper_avg' : upper_avg 
                            }
                        },
                        upsert=True)


    for field in ['uuid', 'min', 'max', 'avg', 'upper_avg', 
            'stage_name', 'stage_enter_time', 'stage_leave_time']:
        db.fps.create_index(field)

'''
Update quality collection for each session.
'''
def update_quality(start_time, end_time, new_users_only=True):
    print('### Update quality')
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    for uuid in uuids:
        print('Processing', uuid)
        stages = db.stage.find(
                {
                    'uuid' : uuid
                })
        for stage in stages:
            if stage['enter_time'] is None:
                continue
            if stage['leave_time'] is None:
                stage['leave_time'] = datetime.datetime.max 

            data_set = db.message.aggregate([
                    {'$match' : {
                        'uuid' : uuid, 
                        'quality' : {'$gte' : 0},
                        'create_time' : {
                            '$gte' : stage['enter_time'], 
                            '$lt' : stage['leave_time']
                        }
                    }},
                    {'$group' : {
                        '_id' : '$uuid', 
                        'min' : {'$min' : '$quality'},
                        'max' : {'$max' : '$quality'}
                    }}
                ])
            for quality in data_set:
                db.quality.update_one(
                        {
                            'uuid' : uuid,
                        },
                        {
                            '$set' : {
                                'stage_name' : stage['stage_name'],
                                'min' : quality['min'],
                                'max' : quality['max']
                            }
                        },
                        upsert=True)


    for field in ['uuid', 'min', 'max', 'stage_name']:
        db.quality.create_index(field)

'''
Update Context3D related info.
'''
def update_context3d_info(start_time, end_time):
    print('### Update Context3D info')
    find_pattern_and_update_session(start_time, end_time, 
            'agal', '设置成AGAL', '设置成AGAL(\d)')
    find_pattern_and_update_session(start_time, end_time, 
            'driver_info', '当前driverInfo', '当前driverInfo:(.*)')
    update_user_disabled_cases(start_time, end_time)

def update_user_disabled_cases(start_time, end_time):
    if start_time and end_time:
        sessions = db.session.find(
            {
                'create_time' : {'$gte' : start_time, '$lt' : end_time},
                'driver_info' : {'$regex' : 'userDisabled'}
            })
    else:
        sessions = db.session.find(
            {
                'driver_info' : {'$regex' : 'userDisabled'}
            })

    for session in sessions:
        print("DriverInfo UserDisabled", session['uname'], session['uuid'], session['create_time'])
        if start_time and end_time:
            other_session = db.session.find_one({
                'uname' : session['uname'],
                'create_time' : {'$gte' : start_time, '$lt' : end_time},
                'driver_info' : {
                    '$exists' : True, '$ne' : session['driver_info']}
            })
        else:
            other_session = db.session.find_one(
            {
                'uname' : session['uname'],
                'driver_info' : {
                    '$exists' : True, '$ne' : session['driver_info']}
            })

        if other_session:
            print(other_session)
            print("Find new driver_info", other_session['driver_info'])
            new_driver_info =  other_session['driver_info']
            if new_driver_info.find('->') < 0:
                new_driver_info = 'userDisabled -> ' + other_session['driver_info']

            db.session.update_one(
                    {
                        '_id' : session['_id'],
                    },
                    {
                        '$set' : {
                            'driver_info' : new_driver_info
                        }
                    })



'''
Find the match pattern in message and update corresponding field in session.
The matach pattern is used by mongodb's regex so that itshould be plain text.
'''
def find_pattern_and_update_session(start_time, end_time, 
            field_name, match_pattern, search_pattern):
    sessions = get_sessions(start_time, end_time)
    for session in sessions:
        uuid = session['uuid']
        message = db.message.find_one(
                {
                    'uuid' : uuid,
                    'message' : {'$regex' : match_pattern}
                })
        if message:
            m = re.search(search_pattern, message['message'])
            if m:
                session[field_name] = m.group(1)
            else:
                session[field_name] = None
            db.session.update_one(
                    {
                        'uuid' : uuid
                    },
                    {
                        '$set' : {field_name : session[field_name]}
                    })

    db.session.create_index(field_name)

 
'''
Return redirect records within a timeframe.
'''
def get_redirects(start_time, end_time):
    return db.redirect.find(
            {
                'redirect_time' : {'$gte' : start_time, '$lt' : end_time}
            })

'''
Return progress records for a uuid.
'''
def get_progress(uuid):
    return db.progress.find_one({'uuid' : uuid})

'''
Return new users based on create_time and timeframe.
'''
def get_new_users(start_time, end_time, unames):
    return db.user.find(
            {
                'uname' : {'$in' : unames},
                'create_time' : {'$gte': start_time, '$lt': end_time}
            })

'''
Return verteran users based on create_time and timeframe.
'''
def get_verteran_users(start_time, end_time, unames):
    return db.user.find(
            {
                'uname' : {'$in' : unames},
                'create_time' : {'$lt': start_time}
            })

'''
Return time travelers based on create_time and timeframe.
Time travelers are users who created after the timeframe.
They may be regarded as missing users for reporting.
'''
def get_time_travelers(start_time, end_time, unames):
    return db.user.find(
            {
                'uname' : {'$in' : unames},
                'create_time' : {'$gte': end_time}
            })
'''
Return mssing users based on create_time and timeframe.
'''
def get_missing_users(start_time, end_time, unames):
    # The uname is in redirects but not in user collection.
    missing_users_with_logs = []

    # The uname is neither in redirects nor in user collection.
    missing_unames_without_logs = []

    for uname in unames:
        found_in_user  = db.user.find_one(
            {
                'uname' : uname,
                'create_time' : {'$lt' : end_time}
            }) 
        found_in_session  = db.session.find_one(
            {
                'uname' : uname,
                'create_time' : {'$gte' : start_time, '$lt' : end_time}
            })
            
        if not found_in_user:
            if found_in_session:
                missing_users_with_logs.append(found_in_session)
            else:
                missing_unames_without_logs.append(uname)
    return missing_users_with_logs, missing_unames_without_logs
        
'''
Get unames of new users (including missing users) within a timeframe
'''
def get_unames_of_new_users(start_time, end_time, unames):
    new_users = get_new_users(start_time, end_time, unames)
    missing_users_with_logs, missing_unames_without_logs = \
            get_missing_users(start_time, end_time, unames)

    return  new_users.distinct('uname') \
            + [user['uname'] for user in missing_users_with_logs] \
            + missing_unames_without_logs

'''
Get redirects of new users (including missing users) within a timeframe.
'''
def get_redirects_of_new_users(start_time, end_time):
    redirects = get_redirects(start_time, end_time)
    unames = redirects.distinct('uname')

    new_unames = get_unames_of_new_users(start_time, end_time, unames)

    return db.redirect.find(
            {
                'uname' : {'$in': new_unames},
                'redirect_time' : {'$gte': start_time, '$lt' : end_time}
            })


'''
Get uuids of new users (including missing users) within a timeframe.
'''
def get_uuids_of_new_users(start_time, end_time):
    return get_redirects_of_new_users(start_time, end_time).distinct('uuid')

'''
Analyze and return user groups.
'''
def get_user_groups(start_time, end_time, unames):
    new_users = get_new_users(start_time, end_time, unames)
    verteran_users = get_verteran_users(start_time, end_time, unames)
    time_travelers = get_time_travelers(start_time, end_time, unames)
    
    missing_users_with_logs, missing_unames_without_logs \
            = get_missing_users(start_time, end_time, unames)
    '''
    recorded_unames = new_users.distinct('uname') \
            + verteran_users.distinct('uname') \
            + time_travelers.distinct('uname')

    missing_unames = [u for u in unames if u not in recorded_unames]
    '''
    return new_users, verteran_users, time_travelers, \
        missing_users_with_logs, missing_unames_without_logs

'''
Generate report of users.
'''
def report_users(start_time, end_time, ips_excluded=[]):
    redirects = get_redirects(start_time, end_time)

    unames = redirects.distinct('uname')
    print('Redirected unames:', str(len(unames)))
    print('------------------------------')

    new_users, verteran_users, time_travelers, \
            missing_users_with_logs, missing_unames_without_logs = \
            get_user_groups(start_time, end_time, unames)

    print('New users:', str(new_users.count()))
    for user in new_users:
        print(user['uname'] + ',' + str(user['create_time']))
    print('------------------------------')

    print('Verteran users:', str(verteran_users.count()))
    for user in verteran_users:
        print(user['uname'] + ',' + str(user['create_time']))
    print('------------------------------')

    print('Time travelers: ' + str(time_travelers.count()))
    for user in time_travelers:
        print(user['uname'] + ',' + str(user['create_time']))
    print('------------------------------')

    print('Missing users with logs: ' + str(len(missing_users_with_logs)))
    for user in missing_users_with_logs:
        print(user['uname']+ ',' + str(user['create_time']))
    print('------------------------------')

    print('Missing unames without logs:', 
        str(len(missing_unames_without_logs)))
    for uname in missing_unames_without_logs:
        print(uname)

def round_to_hour(dt):
    return datetime.datetime(dt.year, dt.month, dt.day, dt.hour)

'''
Generate report of redirects.
'''
def report_redirects(start_time, end_time, ips_excluded=[]):
    redirects = get_redirects(start_time, end_time)

    report = {}
    start_hour = round_to_hour(start_time)
    end_hour = round_to_hour(end_time)

    current_hour = start_hour
    delta = datetime.timedelta(hours=1)
    while current_hour <= end_hour:
        next_hour = current_hour + delta
        report[current_hour] = set() 
        current_hour = next_hour 

   
    print ('Redirect records from {0} to {1}: total {2}'.format(
            start_time, end_time, redirects.count()))
    print (','.join(['uname', 'uuid', 'redirect_time']))
    for redirect in redirects:
        print(','.join([redirect['uname'], redirect['uuid'], 
                str(redirect['redirect_time'])]))
        redirect_hour = round_to_hour(redirect['redirect_time'])
        report[redirect_hour].add(redirect['uname'])

    unames = redirects.distinct('uname') 
    print ('Distinct unames: ', len(unames))
    for uname in unames:
        print(uname)



    current_hour = start_hour
    delta = datetime.timedelta(hours=1)
    while current_hour <= end_hour:
        next_hour = current_hour + delta
        print('{0},{1}'.format(current_hour, len(report[current_hour])))
        current_hour = next_hour 



'''
Generate report of session progress within a timeframe.
'''
def generate_session_progress_report(uuids):
    session_progress = db.session_progress.find(
            {
                'uuid' : {'$in' : uuids}
            })

    uuids_with_progress = session_progress.distinct('uuid') 
    sessions_with_progress_report = [] 
    for p in session_progress:
        record = ','.join([str(p[f]) for f in ['uuid', 'uname', 'progress']])
        record += ',' + ','.join([str(score) for score in p['score_card']])
        sessions_with_progress_report.append(record)

    uuids_without_progress_report = \
            [e for e in uuids if e not in uuids_with_progress] 

    return sessions_with_progress_report, uuids_without_progress_report

'''
Generate report of session within a timeframe.
'''
def generate_session_report(uuids):
    sessions_with_progress = db.session_progress.find(
            {
                'uuid' : {'$in' : uuids}
            })

    uuids_with_progress = sessions_with_progress.distinct('uuid') 
    sessions_with_progress_report = [] 
    for progress in sessions_with_progress:
        session_meta = db.session.find_one(
                {
                    'uuid' : progress['uuid'] 
                })
        session_report = progress['uuid']
        for f in ['ip', 'uname', 'create_time', 'os', 'fp_version',
                    'browser', 'url', 'fp_manufacturer', 'fp_type', 
                    'agal', 'driver_info']:
            if f in session_meta:
                session_report += ',"' + str(session_meta[f]) + '"'
            else:
                session_report += ',NULL'


        progress_report = ','.join([
                str(progress['progress']),
                ','.join([str(score) for score in progress['score_card']]),
                ','.join([str(interval) for interval in progress['interval_card']]),
                ])


        sessions_with_progress_report.append(','.join([
            session_report, progress_report]))


    uuids_without_progress_report = \
            [e for e in uuids if e not in uuids_with_progress] 

    return sessions_with_progress_report, uuids_without_progress_report

'''
Generate detailed report of session.
'''
def report_sessions(start_time, end_time, new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    print('Sessions total: ' + str(len(uuids))) 
    print('------------------------------')

    sessions_with_progress_report, uuids_without_progress_report = \
            generate_session_report(uuids)
    print('Sessions with progress: {0}'.format(
            len(sessions_with_progress_report))) 

    for s in sessions_with_progress_report:
        print(s)
    print('------------------------------')

    print('Uuids without progress: {0}'.format(
            len(uuids_without_progress_report))) 
    for uuid in uuids_without_progress_report:
        print(uuid) 

'''
Report events.
'''
def report_event_elapsed_time(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')
    for uuid in uuids:
        event = db.event.find_one(
            {
                'uuid' : {'$in' : uuids}
            })
        print(event)

    elapsed_data_set = db.event.aggregate([
            {
                '$match' : {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group' : {
                    '_id' : '$event_name', 
                    'avg' : {'$avg' : '$elapsed'} 
                }
            }])


    event_defs = db.event_def.find({}).sort('order', pymongo.ASCENDING)
    event_names = [e['name'] for e in event_defs]

    result = []
    elapsed_list = list(elapsed_data_set)
    for i in range(0, len(event_names)):
        event_name = event_names[i]
        avg = -1
        for e in elapsed_list:
            if event_name  == e['_id']:
                avg = e['avg']
                break
        print('"' + event_name + '"' +  ',' + str(avg))



'''
Generate report of session progress.
'''
def report_session_progress(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    print('Sessions total: ' + str(len(uuids))) 
    print('------------------------------')

    sessions_with_progress_report, uuids_without_progress_report = \
            generate_session_progress_report(uuids)
    print('Sessions with progress: {0}'.format(
            len(sessions_with_progress_report))) 

    for s in sessions_with_progress_report:
        print(s)
    print('------------------------------')

    print('Uuids without progress: {0}'.format(
            len(uuids_without_progress_report))) 
    for uuid in uuids_without_progress_report:
        print(uuid) 


'''
Generate report of user progress.
'''
def report_user_progress(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    unames = get_redirects(start_time, end_time).distinct('uname')
    if new_users_only:
        unames = get_unames_of_new_users(start_time, end_time, unames)

    print('Unames total: ' + str(len(unames))) 
    print('------------------------------')

    user_progress = db.user_progress.find(
            {
                'uname' : {'$in' : unames}
            })

    unames_with_progress = user_progress.distinct('uname') 
    print('Unames with progress: ' + str(len(unames_with_progress))) 

    unames_without_progress = [
            e for e in unames if e not in unames_with_progress] 

    for p in user_progress:
        print(p['uname'] + ',' + str(p['progress']))
    print('------------------------------')

    print('Unames without progress: ' + str(len(unames_without_progress))) 
    for uname in unames_without_progress:
        print(uname)



'''
Generate report of event distribution by session.
'''
def report_session_event(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    progress_distribution = db.session_progress.aggregate([
            {
                '$match' : {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group' : {
                    '_id' : '$progress', 
                    'count' : {'$sum' : 1}, 
                    'uuids' : {'$push' : '$uuids'}
                }
            }])

    progress_distribution = list(progress_distribution)
    progress_distribution = dict([(
            e['_id'], e['count']) for e in progress_distribution])

    print(progress_distribution)
    event_defs = db.event_def.find({}).sort('order', pymongo.ASCENDING)
    event_names = [e['name'] for e in event_defs]

    result = []
    session_count = 0
    for i in range(len(event_names) - 1, -1, -1):
        if i in progress_distribution:
            session_count += progress_distribution[i]
        result.insert(0,(event_names[i], session_count))

    print('redirect,' + str(len(uuids)))
    for name, count in result:
        print('"' + name + '"' +  ',' + str(count))

'''
Get event distribution by user.
'''
def get_event_user_distribution(unames):
    progress_distribution = db.user_progress.aggregate([
            {'$match' : {
                    'uname' : {'$in' : unames}
                }
            },
            {'$group' : {
                    '_id' : '$progress', 
                    'count' : {'$sum' : 1}, 
                    'unames' : {'$push' : '$uname'}
                }
            },
        ])

    progress_distribution = list(progress_distribution)
    progress_distribution = dict([(
            e['_id'], e['count']) for e in progress_distribution])

    print(progress_distribution)
    event_defs = db.event_def.find({}).sort('order', pymongo.ASCENDING)
    event_names = [e['name'] for e in event_defs]

    result = []
    user_count = 0
    for i in range(len(event_names) - 1, -1, -1):
        if i in progress_distribution:
            user_count += progress_distribution[i]
        result.insert(0,(event_names[i], user_count))

    return result


    
'''
Generate report of event distribution by user.
'''
def report_user_event(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    unames = get_redirects(start_time, end_time).distinct('uname')
    if new_users_only:
        unames = get_unames_of_new_users(start_time, end_time, unames)

    print('redirect,' + str(len(unames)))

    result = get_event_user_distribution(unames)
    for name, count in result:
        print('"' + name + '"|' + str(count))

'''
Generate report of a compatibility field.
'''
def generate_compatibility_field_report(uuids, field_name):
    groups = db.session.aggregate([
            {
                '$match' : {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group' : {
                    '_id' : {
                        field_name : '$' + field_name 
                    },
                    'count' : {'$sum' : 1} 
                   
                }
            },
            {
                '$sort' : {
                    '_id.' + field_name : 1
                }
            }])

    l = list(groups)

    result = '{0}: {1}\n'.format(field_name, len(l))
    for g in l:
        result += '"{0}",{1}\n'.format(g['_id'][field_name], g['count'])
    
    return result

'''
Generate report of compatibility.
'''
def report_compatibility(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    print(generate_compatibility_field_report(uuids, 'agal'))
    print(generate_compatibility_field_report(uuids, 'os'))
    print(generate_compatibility_field_report(uuids, 'fp_version'))


'''
Generate comma seperated report by stage.
'''
def generate_report_by_stage(max_range, step, groups, field_name): 
    num = int(max_range / step)
    result= [] 
    stage_mapping = {'novice' : 0, 'main' : 1, 'worldmap' : 2, 'battle' : 3}
    for i in range(0, num + 1):
        result.append([0,0,0,0])
    
    for g in list(groups):
        group =  int(g['_id'][field_name] / step)  
        stage_name =  g['_id']['stage_name']  
        stage_order = stage_mapping[stage_name]  
        if group > num:
            result[num][stage_order] = g['count']
        else:
            result[group][stage_order] += g['count']
    for i in range(0, num + 1): 
        print(str(i * step) + ',' + ','.join([str(e)for e in result[i]]))
    
'''
Generate report of memory usage.
'''
def report_memory(start_time, end_time, new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.memory.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {   
                '$project': {
                    'stage_name': 1,
                    'avg_group' : 
                    {
                        '$subtract' : [ 
                            '$avg', 
                            {'$mod' : ['$avg', 50]},
                         ]
                    }
                }
            },
            {
                '$group': {
                    '_id' : {
                        'avg_group' : '$avg_group',
                        'stage_name' : '$stage_name'
                    },
                    'count' : {'$sum' : 1}
                }
            },
            {
                '$sort' : {'_id.avg_group' : 1, '_id.stage_name' : 1}
            }])
    generate_report_by_stage(600, 50, groups, 'avg_group')

'''
Generate report of fps.
'''
def report_fps(start_time, end_time, new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.fps.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {   
                '$project': {
                    'stage_name' : 1, 
                    'upper_avg_group' : 
                    {
                        '$subtract' : [ 
                            '$upper_avg', 
                            {'$mod' : ['$upper_avg', 5]},
                         ]
                    }
                }
            },
            {
                '$group': {
                    '_id' : {
                        'upper_avg_group' : '$upper_avg_group',
                        'stage_name' : '$stage_name'
                    },
                    'count' : {'$sum' : 1}
                }
            },
            {
                '$sort' : {
                    '_id.upper_avg_group' : 1, '_id.stage_name' : 1}
            }])

    generate_report_by_stage(60, 5, groups, 'upper_avg_group')
                    

'''
Generate report of graphic quality.
'''
def report_quality(start_time, end_time, new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.quality.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {   
                '$project': {
                    'stage_name' : 1, 
                    'min_group' : 
                    {
                        '$subtract' : [ 
                            '$min', 
                            {'$mod' : ['$min', 1]},
                         ]
                    }
                }
            },
            {
                '$group': {
                    '_id' : {
                        'min_group' : '$min_group',
                        'stage_name' : '$stage_name'
                    },
                    'count' : {'$sum' : 1}
                }
            },
            {
                '$sort' : {'_id.min_group' : 1, '_id.stage_name' : 1}
            }])

    for uuid in uuids:
        record = uuid
        for stage_name in ['novice', 'main', 'worldmap', 'battle']:
            quality = db.quality.find_one(
                {
                    'uuid' : uuid,
                    'stage_name' : stage_name
                })
            if quality: 
                record += ',' + str(quality['min'])
            else:
                record += ',-'
        print(record)

    generate_report_by_stage(3, 1, groups, 'min_group')

'''
Report Context3D info
'''
def report_context3d_info(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.session.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group': {
                    '_id' : {
                        'uname' : '$uname',
                        'ip' : '$ip',
                        'browser' : '$browser'
                    },
                    'driver_info' : {'$addToSet' : '$driver_info'}
                }
            }])
    enabled = 0
    scores = [0, 0, 0, 0, 0 ,0]
    keys = ['DirectX9', 'OpenGL', 'DirectX11', 
            'Software Hw_disabled--userDisabled',
            'Software Hw_disabled--unavailable', 
            'Software Hw_disabled--oldDriver'] 
    l = list(groups)
    for g in l:
        s = str(g['driver_info'])
        print(g['_id']['uname'], s)
        for i in range(0, 6):
            if s.find('userDisabled ->') >= 0:
                enabled += 1
            if s.find(keys[i]) >= 0:
                scores[i] += 1
                break
    scores.append(len(l) - sum(scores))
    print(scores)
    print('软件渲染重新开启硬件加速:', enabled)

'''
Report OS info
'''
def report_os_info(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.session.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group': {
                    '_id' : {
                        'uname' : '$uname',
                        'ip' : '$ip',
                        'browser' : '$browser'
                    },
                    'os' : {'$addToSet' : '$os'}
                }
            }])
    scores = [0, 0, 0, 0, 0 ,0, 0]
    keys = ['Windows 10', 'Windows 8.1', 'Windows 8', 
            'Windows 7', 'Windows Vista', 'Windows XP',
            'null'] 
    l = list(groups)
    for g in l:
        s = str(g['os'])
        print(g['_id']['uname'], s)
        for i in range(0, 7):
            if s.find(keys[i]) >= 0:
                scores[i] += 1
                break
    scores[2] = scores[2] - scores[1]
    print(keys)
    print(scores)

'''
Report FP info
'''
def report_fp_version_info(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.session.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group': {
                    '_id' : {
                        'uname' : '$uname',
                        'ip' : '$ip',
                        'browser' : '$browser'
                    },
                    'fp_version' : {'$addToSet' : '$fp_version'}
                }
            }])
    scores = [0, 0, 0, 0, 0 ,0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    keys = ['24,', '23,', '22,', '21,', '20,', '19,', '18,', '17,', '16,', 
            '15,', '14,', '13,', '12,', '11,', 'null'] 
    l = list(groups)
    for g in l:
        s = str(g['fp_version'])
        print(g['_id']['uname'], s)
        for i in range(0, 15):
            if s.find(keys[i]) >= 0:
                scores[i] += 1
                break
    print(keys)
    print(scores)

'''
Report Browser info
'''
def report_browser_info(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')

    groups = db.session.aggregate([
            {
                '$match': {
                    'uuid' : {'$in' : uuids}
                }
            },
            {
                '$group': {
                    '_id' : {
                        'uname' : '$uname',
                        'ip' : '$ip',
                        'browser' : '$browser'
                    },
                    'browser' : {'$addToSet' : '$browser'}
                }
            }])
    scores = [0, 0, 0, 0, 0, 0]
    keys = ['MSIE', 'Chrome', 'Firefox', 'rv:11', 'AIR', 'null'] 
    l = list(groups)
    for g in l:
        s = str(g['browser'])
        print(g['_id']['uname'], s)
        for i in range(0, 6):
            if i == 0:
                if s.find(keys[i]) >= 0 and s.find('rv:11') == -1 and \
                   s.find('Firefox') == -1 and s.find('Chrome') == -1:
                    scores[i] += 1
                    break
            else:
                if s.find(keys[i]) >= 0:
                    scores[i] += 1
                    break
    print(keys)
    print(scores)


'''
Merge duplicate redirects by uname and ip.
'''
def merge_redirects_by_uname_and_ip(redirects):
    groups = []
    for redirect in redirects:
        uname = redirect['uname']
        ip = redirect['ip']

        found = False
        for g in groups:
            if ip in g['ips'] or uname in g['unames']:
                g['ips'].add(ip)
                g['unames'].add(uname)
                found = True
                break
        if not found:
            g = {'ips' : set([ip]), 'unames' : set([uname])}
            groups.append(g)
    return groups


def report_retention_redirects_by_uname_and_ip(groups, second_day_start):
    for group in groups:
        for uname in group['unames']:
            second_day_redirect = db.redirect.find_one(
                {
                    'uname' : uname,
                    'redirect_time' : {'$gte' : second_day_start}
                 })
            if second_day_redirect:
                group['second_day_retention'] = 1
    
    retained_unames = [group['unames'] for group in groups if \
        'second_day_retention' in group and group['second_day_retention'] > 0]     

    print('首日跳转的新用户独立IP数:{0}'.format(len(groups)))
    print('次日仍有跳转的IP数:{0}'.format(len(retained_unames)))
    print('次日跳转IP留存率:{0:.1%}'.format(
        len(retained_unames) / len(groups)))

    print('------------------------------------')


 
def report_retention_redirects(unames, second_day_start):
    first_day_redirects = set()
    second_day_retained_redirects = set() 

    for uname in unames:
        # redirects
        first_day_redirects.add(uname)

        second_day_redirects = db.redirect.find(
                {
                    'uname' : uname,
                    'redirect_time' : {'$gte' : second_day_start},
                 })
        for redirect in second_day_redirects:
                second_day_retained_redirects.add(uname)

    print('首日跳转用户数:{0}'.format(len(first_day_redirects)))
    print('次日仍有跳转的用户数:{0}'.format(len(second_day_retained_redirects)))
    print('次日跳转留存率:{0:.1%}'.format(
        len(second_day_retained_redirects) / len(first_day_redirects)))

    print('------------------------------------')

def report_retention_connections_by_uname_and_ip(groups, start_time, end_time, second_day_start):
    for group in groups:
        for uname in group['unames']:
            session_progress = db.session_progress.find_one(
                {
                    'uname' : uname,
                    'create_time' : {'$gte' : start_time, '$lt' : end_time},
                    'progress' : {'$gte' : 0}
                })
            if session_progress:
                group['first_day_users'] = 1
                second_day_retention = db.session_progress.find_one(
                    {
                        'uname' : uname,
                        'create_time' : {'$gte' : second_day_start},
                        'progress' : {'$gte' : 0}
                    })
                if second_day_retention:
                    group['second_day_retention'] = 1
    
    first_day_unames = [group['unames'] for group in groups if \
        'first_day_users' in group and group['first_day_users'] > 0]     
    retained_unames = [group['unames'] for group in groups if \
        'second_day_retention' in group and group['second_day_retention'] > 0]     

    print('首日展示的新用户独立IP数:{0}'.format(len(first_day_unames)))
    print('次日仍有展示的IP数:{0}'.format(len(retained_unames)))
    print('次日展示IP留存率:{0:.1%}'.format(
        len(retained_unames) / len(first_day_unames)))

    print('------------------------------------')


def report_retention_connections(unames, start_time, end_time, second_day_start):
    
    first_day_connections = []
    second_day_retained_connections = []

    for uname in unames:
        # users with progress
        session_progress = db.session_progress.find_one(
                {
                    'uname' : uname,
                    'create_time' : {'$gte' : start_time, '$lt' : end_time},
                    'progress' : {'$gte' : 0}
                })
        if session_progress:
            first_day_connections.append(uname)
            p = db.session_progress.find_one(
                {
                    'uname' : uname,
                    'create_time' : {'$gte' : second_day_start},
                    'progress' : {'$gte' : 0}
                })
            if p:
                second_day_retained_connections.append(uname)

    print('首日进入页面展示的用户数:{0}'.format(len(first_day_connections)))
    print('次日仍有进入页面展示的用户数:{0}'.format(len(second_day_retained_connections)))
    print('次日页面展示留存率:{0:.1%}'.format(
        len(second_day_retained_connections) / len(first_day_connections)))

    print('------------------------------------')

def report_retention_registered_by_uname_and_ip(groups, start_time, end_time, second_day_start):
    for group in groups:
        for uname in group['unames']:
            user = db.user.find_one(
                {
                    'uname' : uname
                })
            if user and user['create_time'] >= start_time \
                    and user['create_time'] <= end_time:
                group['first_day_users'] = 1
                if user['login_time'] >= second_day_start:
                    group['second_day_retention'] = 1
    
    first_day_unames = [group['unames'] for group in groups if \
        'first_day_users' in group and group['first_day_users'] > 0]     
    retained_unames = [group['unames'] for group in groups if \
        'second_day_retention' in group and group['second_day_retention'] > 0]     

    print('首日注册的新用户独立IP数:{0}'.format(len(first_day_unames)))
    print('次日仍有登录的用户独立IP数:{0}'.format(len(retained_unames)))
    print('次日注册用户登录独立IP留存率:{0:.1%}'.format(
        len(retained_unames) / len(first_day_unames)))

    print('------------------------------------')


def report_retention_registered(unames, start_time, end_time, second_day_start):
    first_day_users = []
    second_day_retained_users = []

    for uname in unames:
        # registered users
        user = db.user.find_one(
                {
                    'uname' : uname
                })
        if user and user['create_time'] >= start_time \
                and user['create_time'] <= end_time:
            first_day_users.append(uname)
            if user['login_time'] >= second_day_start:
                second_day_retained_users.append(uname)

    print('首日注册用户数:{0}'.format(len(first_day_users)))
    print('次日仍登录进游戏的用户数:{0}'.format(len(second_day_retained_users)))
    print('次日注册用户登录留存率:{0:.1%}'.format(
        len(second_day_retained_users) / len(first_day_users)))

    print('------------------------------------')

'''
Generate retention rate report.
'''
def report_retention(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):

    first_day_start = datetime.datetime(
            start_time.year, start_time.month, start_time.day, 0, 0, 0)
    second_day_start = first_day_start + datetime.timedelta(days=1)

    if end_time > second_day_start:
        print('timeframe must within one day')
        return


    if new_users_only:
        redirects = get_redirects_of_new_users(start_time, end_time) 
    else:
        redirects = get_redirects(start_time, end_time)


    groups = merge_redirects_by_uname_and_ip(redirects)

    unames = redirects.distinct('uname')

    report_retention_redirects(unames, second_day_start)
    report_retention_redirects_by_uname_and_ip(copy.deepcopy(groups), second_day_start)

    report_retention_connections(unames, start_time, end_time, second_day_start)
    report_retention_connections_by_uname_and_ip(copy.deepcopy(groups), start_time, end_time, second_day_start)

    report_retention_registered(unames, start_time, end_time, second_day_start)
    report_retention_registered_by_uname_and_ip(copy.deepcopy(groups), start_time, end_time, second_day_start)

'''
Generate interval report.
'''
def report_intervals(start_time, end_time, 
        new_users_only=True, ips_excluded=[]):
    unames = get_redirects(start_time, end_time).distinct('uname')
    if new_users_only:
        unames = get_unames_of_new_users(start_time, end_time, unames)

    all = []
    median = [] 
    event_defs = list(db.event_def.find({}).sort('order', 1))
    #max_event = len(event_defs) 
    max_event = 72 
    novice_loadings = []
    main_loadings = []

    for i in range(0, max_event):
        all.append([])

    for uname in unames:
        novice_loading = 0
        novice_consecutive = True
        main_loading = 0
        main_consecutive = True
        for i in range(0, max_event):
            event_def = event_defs[i]
            event_name = event_def['name']
            event_order = event_def['order']

            e = db.event.find(
                    {
                        'uname' : uname,
                        'event_order' : event_order,
                        'create_time' : {'$gte' : start_time, '$lt' : end_time},
                        'interval' : {'$gte' : 0}
                    }).sort('create_time', 1).limit(1)
            
            if e.count() and e[0]['interval'] >= 0:
                all[i].append(e[0]['interval'])
                if i > 1  and i <= 30:
                    novice_loading += e[0]['interval']
                if i > 69  and i <= 71:
                    main_loading += e[0]['interval']
            else:
                if i > 1 and i <= 30:
                    novice_consecutive = False
                if i > 69 and i <= 71:
                    main_consecutive = False
        if novice_consecutive and novice_loading > 0:
           novice_loadings.append((uname, novice_loading))
        if main_consecutive and main_loading > 0:
           main_loadings.append((uname, main_loading))
        print('{0},{1},{2}'.format(uname, 
                novice_loading if novice_consecutive else 0, 
                main_loading if main_consecutive else 0))

            
    for i in range(0, max_event):
        if all[i]:
            sl = sorted(all[i])
            median.append(sl[int(len(sl)/2)])
        else:
            median.append(-1)
        print('"{0}",{1}'.format(event_defs[i]['name'], median[i]))

    print('### novice loadings')
    for uname, loading in novice_loadings:
        print('{0},{1}'.format(uname, loading))
    print('### main loadings')
    for uname, loading in main_loadings:
        print('{0},{1}'.format(uname, loading))



'''
Generate error report.
'''
def report_errors(start_time, end_time, new_users_only=True, ips_excluded=[]):
    if new_users_only:
        uuids = get_uuids_of_new_users(start_time, end_time) 
    else:
        uuids = get_redirects(start_time, end_time).distinct('uuid')
    errors = db.message.find(
            {
                'message' : {
                    '$regex' : 'Error'
                },
                'uuid' : {
                    '$in' : uuids
                }
            })
    for error in errors:
        print(error)

def update_datetime():
    posts = collection.find(
            {'createDate' : {'$exists' : True}},
            modifiers = {"$snapshot" : True})
    for post in posts:
        if 'createDate' in post:
            post['createDate'] = datetime.datetime.strptime(
                post['createDate'], '%Y-%m-%d %H:%M:%S.%f')
            collection.update_one(
                    {'_id' : post['_id']},
                    {'$set': {'createDate' : post['createDate']}})

'''
Handle import options.
'''
def handle_import(args):
    if args.defaults:
        import_users('users.json')
        import_redirects('redirects/dispatcher.log')
        import_event_def('event_def.json')
        import_stage_def('stage_def.json')
    else:
        if args.users:
            import_users(args.users)
        if args.redirects_json:
            import_redirects_json(args.redirects_json)
        if args.redirects:
            import_redirects(args.redirects)
        if args.event_def:
            import_event_def(args.event_def)
        if args.stage_def:
            import_stage_def(args.stage_def)
        if args.logs:
            import_logs(args.logs)

'''
Handle update options.
'''
def handle_update(args):
    start_time = datetime.datetime.strptime(args.start_time, '%Y-%m-%d %H:%M') \
        if args.start_time else None
    end_time = datetime.datetime.strptime(args.end_time, '%Y-%m-%d %H:%M') \
        if args.end_time else None

    if args.all:
        update_stages(start_time, end_time)
        update_events(start_time, end_time, args.drop)
        update_unames()
        update_session_create_time()
        update_session_progress(start_time, end_time)
        update_user_progress(start_time, end_time)
        update_memory(start_time, end_time)
        update_fps(start_time, end_time)
        update_quality(start_time, end_time)
        update_context3d_info(start_time, end_time)
    else:
        if args.stages:
            update_stages(start_time, end_time)
        if args.events:
            update_events(start_time, end_time, args.drop)
        if args.unames:
            update_unames()
        if args.session_create_time:
            update_session_create_time()
        if args.session_progress:
            update_session_progress(start_time, end_time)
        if args.user_progress:
            update_user_progress(start_time, end_time)
        if args.memory:
            update_memory(start_time, end_time)
        if args.fps:
            update_fps(start_time, end_time)
        if args.quality:
            update_quality(start_time, end_time)
        if args.context3d_info:
            update_context3d_info(start_time, end_time)

'''
Handle report options.
'''
def handle_report(args):
    start_time = datetime.datetime.strptime(args.start_time, '%Y-%m-%d %H:%M')
    end_time = datetime.datetime.strptime(args.end_time, '%Y-%m-%d %H:%M')
    ips_excluded = args.exclude_ips
    if args.all:
        report_users(start_time, end_time, ips_excluded)
        report_redirects(start_time, end_time, ips_excluded)
        report_sessions(start_time, end_time, args.new_users_only, ips_excluded)
        report_event_elapsed_time(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_session_progress(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_user_progress(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_compatibility(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_memory(start_time, end_time, args.new_users_only, ips_excluded)
        report_fps(start_time, end_time, args.new_users_only, ips_excluded)
        report_quality(start_time, end_time, args.new_users_only, ips_excluded)
        report_session_event(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_user_event(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_context3d_info(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_retention(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_intervals(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_errors(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_os_info(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_fp_version_info(start_time, end_time, 
                args.new_users_only, ips_excluded)
        report_browser_info(start_time, end_time, 
                args.new_users_only, ips_excluded)
        
    else:
        if args.users:
            report_users(start_time, end_time, ips_excluded)
        if args.redirects:
            report_redirects(start_time, end_time, ips_excluded)
        if args.sessions:
            report_sessions(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.event_elapsed_time:
            report_event_elapsed_time(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.session_progress:
            report_session_progress(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.user_progress:
            report_user_progress(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.compatibility:
            report_compatibility(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.memory:
            report_memory(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.fps:
            report_fps(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.quality:
            report_quality(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.session_event:
            report_session_event(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.user_event:
            report_user_event(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.context3d_info:
            report_context3d_info(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.retention:
            report_retention(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.intervals:
            report_intervals(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.errors:
            report_errors(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.os_info:
            report_os_info(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.fp_version_info:
            report_fp_version_info(start_time, end_time, 
                    args.new_users_only, ips_excluded)
        if args.browser_info:
            report_browser_info(start_time, end_time, 
                    args.new_users_only, ips_excluded)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title='subcommands')

    imp = subparsers.add_parser('import', aliases=['imp', 'i'])
    upd = subparsers.add_parser('update', aliases=['upd', 'u'])
    rpt = subparsers.add_parser('report', aliases=['rpt', 'r'])

    # Import options
    imp.set_defaults(func=handle_import)
    imp.add_argument('-d', '--defaults', action='store_true')
    imp.add_argument('-u', '--users', action='store')
    imp.add_argument('-r', '--redirects', action='store')
    imp.add_argument('-rj', '--redirects-json', action='store')
    imp.add_argument('-e', '--event-def', action='store')
    imp.add_argument('-s', '--stage-def', action='store')
    imp.add_argument('-l', '--logs', nargs = '*', action='store')

    # Update options
    upd.set_defaults(func=handle_update)
    upd.add_argument('-a', '--all', action='store_true')
    upd.add_argument('-d', '--drop', action='store_true')
    upd.add_argument('start_time', action='store', 
            metavar='yyyy-mm-dd hh:mm', nargs='?')
    upd.add_argument('end_time', action='store', 
            metavar='yyyy-mm-dd hh:mm', nargs='?')
    upd.add_argument('-s', '--stages', action='store_true')
    upd.add_argument('-e', '--events', action='store_true')
    upd.add_argument('-u', '--unames', action='store_true')
    upd.add_argument('-t', '--session-create-time', action='store_true')
    upd.add_argument('-sp', '--session-progress', action='store_true')
    upd.add_argument('-up', '--user-progress', action='store_true')
    upd.add_argument('-m', '--memory', action='store_true')
    upd.add_argument('-f', '--fps', action='store_true')
    upd.add_argument('-q', '--quality', action='store_true')
    upd.add_argument('-c', '--context3d-info', action='store_true')

    # Report options
    rpt.set_defaults(func=handle_report)
    rpt.add_argument('-a', '--all', action='store_true')
    rpt.add_argument('-n', '--new-users-only', action='store_true')
    rpt.add_argument('start_time', action='store', metavar='yyyy-mm-dd hh:mm')
    rpt.add_argument('end_time', action='store', metavar='yyyy-mm-dd hh:mm')
    rpt.add_argument('-ex', '--exclude-ips', nargs='*', action='store')
    rpt.add_argument('-u', '--users', action='store_true') 
    rpt.add_argument('-r', '--redirects', action='store_true')
    rpt.add_argument('-s', '--sessions', action='store_true')
    rpt.add_argument('-e', '--event-elapsed-time', action='store_true')
    rpt.add_argument('-sn', '--sessions-new-users', action='store_true')
    rpt.add_argument('-sp', '--session-progress', action='store_true') 
    rpt.add_argument('-up', '--user-progress', action='store_true')
    rpt.add_argument('-se', '--session-event', action='store_true')
    rpt.add_argument('-ue', '--user-event', action='store_true')
    rpt.add_argument('-m', '--memory', action='store_true')
    rpt.add_argument('-f', '--fps', action='store_true')
    rpt.add_argument('-q', '--quality', action='store_true')
    rpt.add_argument('-c', '--compatibility', action='store_true')
    rpt.add_argument('-err', '--errors', action='store_true')
    rpt.add_argument('-co', '--context3d-info', action='store_true')
    rpt.add_argument('-ret', '--retention', action='store_true')
    rpt.add_argument('-i', '--intervals', action='store_true')
    rpt.add_argument('-os', '--os-info', action='store_true')
    rpt.add_argument('-fpv', '--fp-version-info', action='store_true')
    rpt.add_argument('-br', '--browser-info', action='store_true')

    # Other options
    parser.add_argument('-o', '--output', action='store')
    parser.add_argument('-t', '--test', action='store_true')

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    
