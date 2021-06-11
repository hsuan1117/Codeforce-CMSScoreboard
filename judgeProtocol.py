import getpass, re, json
from requests import Session
from hashlib import sha512
from urllib.parse import urlencode
from time import time
import os
import pathlib
from _datetime import datetime
from dotenv import load_dotenv
load_dotenv()

def login(s, handle, password):
    res = s.get('https://codeforces.com/enter')
    csrf_token = re.findall('<meta name="X-Csrf-Token" content="(.{32})"/>', res.text)[0]
    data = {
        'csrf_token': csrf_token,
        'action': 'enter',
        'ftaa': '',
        'bfaa': '',
        'handleOrEmail': handle,
        'password': password
    }
    res = s.post('https://codeforces.com/enter', data = data)
    assert 'Logout' in res.text

def get_submission_detail(s, ID):
    cache_file = pathlib.Path(f"cache/submission-{ID}.w3")

    if not cache_file.exists():
        res = s.get('https://codeforces.com')
        csrf_token = re.findall('<meta name="X-Csrf-Token" content="(.{32})"/>', res.text)[0]
        data = {
            'csrf_token': csrf_token,
            'submissionId': ID,
        }
        res = s.post('https://codeforces.com/group/HELkcZPVHX/data/judgeProtocol', data = data) # CHANGE IT
        with open(f"cache/submission-{ID}.w3", 'w') as tmp:
            tmp.write(res.text)
        return res.text
    else:
        with open(f"cache/submission-{ID}.w3", 'r') as tmp:
            return tmp.read()

def logout(s):
    res = s.get('https://codeforces.com')
    link = re.findall('<a href="(/.{32}/logout)">Logout</a>', res.text)[0]
    res = s.get('https://codeforces.com' + link)
    assert 'Logout' not in res.text

def get_users(s, contestId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    cache_file = pathlib.Path('cache/users.json')
    user_list = {}

    if not cache_file.exists() or int(time()) - int(cache_file.stat().st_mtime) >= 10*60:
        f = open('cache/users.json',"w")
        data = urlencode({
            'apiKey': key,
            'contestId': contestId,
            # 'count': 100,
            # 'from': 1,
            'time': int(time())
        })

        methods = 'contest.status'
        apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
        res = s.get(f'https://codeforces.com/api/{methods}?{data}', params={'apiSig': '123456' + apiSig})
        api_json = json.loads(res.text)
        users = api_json['result']
        # print(api_json['result'])

        for user in users:
            #print(user['author'])
            user_list[user['author']['members'][0]['handle']] = {
                "f_name": user['author']['members'][0]['handle'],
                "l_name": user['author']['members'][0]['handle'],
                "team": None
            }
        json.dump(user_list,f)
    else:
        print("[Debug] using cache user")
        with open("cache/users.json", 'r') as tmp:
            user_list = json.load(tmp)
    return user_list

def get_contest(s, contestId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    data = urlencode({
        'apiKey': key,
        'contestId': contestId,
        'time': int(time())
    })
    methods = 'contest.standings'
    apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
    res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
    api_json = json.loads(res.text)
    #print(api_json)

    contest = api_json['result']['contest']

    returnObj = {}
    returnObj[contest['name']] = {
        "name":contest['name'],
        "begin":contest['startTimeSeconds'],
        "end":contest['startTimeSeconds']+24*60*60,
        "score_precision": 0
    }
    return returnObj

def get_tasks(s, contestId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    data = urlencode({
        'apiKey': key,
        'contestId': contestId,
        'time': int(time())
    })
    methods = 'contest.standings'
    apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
    res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
    api_json = json.loads(res.text)
    tasks = api_json['result']['problems']

    returnObj = {}
    for task in tasks:
        returnObj[task['index']] = {
            "name": task['name'],
            "shortName": task['index'],
            "contest": api_json['result']['contest']['name'],
            "max_score": 100,
            "extra_headers": [
                "Subtask 1 (87)",
                "Subtask 2 (13)"
            ],
            "order": 0,
            "score_mode": "max_subtask",
            "score_precision": 0
        }
    return returnObj

def get_submission_ids(s, contestId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    contestId = 328447
    cache_file = pathlib.Path('cache/submissionIds.json')

    if not cache_file.exists() or int(time()) - int(cache_file.stat().st_mtime) >= 10*60:
        data = urlencode({
            'apiKey': key,
            'contestId': contestId,
            'time': int(time())
        })
        methods = 'contest.status'
        apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
        res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
        api_json = json.loads(res.text)
        json.dump(api_json,open('cache/submissionIds.json','w+'))
    else:
        api_json = json.load(open('cache/submissionIds.json','r'))
        print('using cache submission ids')

    submission_ids = []
    #print(api_json)
    for submission_info in api_json['result']:
        #print(api_json['result'])
        if (submission_info['author']['participantType'] == 'MANAGER'):
            continue
        if (submission_info['relativeTimeSeconds'] == 2147483647):
            continue
        # if (submission_info['points'] == 0.0):
            # continue
        handle = submission_info['author']['members'][0]['handle']
        participant_type = submission_info['author']['participantType']
        problem_index = submission_info['problem']['index']
        submission_time = submission_info['creationTimeSeconds']
        submission_id = submission_info['id']
        submission_ids.append([handle, participant_type, problem_index, submission_time, submission_id])
    return submission_ids

def get_history(s, contestId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    contestId = 328447
    cache_file = pathlib.Path('cache/submissionIds.json')

    if not cache_file.exists() or int(time()) - int(cache_file.stat().st_mtime) >= 10*60:
        data = urlencode({
            'apiKey': key,
            'contestId': contestId,
            'time': int(time())
        })
        methods = 'contest.status'
        apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
        res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
        api_json = json.loads(res.text)
        json.dump(api_json,open('cache/submissionIds.json','w+'))

    else:
        api_json = json.load(open('cache/submissionIds.json','r'))
        print('using cache submission history')

    histories = []
    #creationTimeSeconds
    for sub in api_json['result']:
        histories.append([
            sub['author']['members'][0]['handle'],
            sub['problem']['index'],
            sub['creationTimeSeconds'],
            sub['points']
        ])
    return histories

def get_sublist(s, contestId, userId, key=os.getenv('API_KEY'), secret=os.getenv('SECRET')):
    ids = get_submission_ids(s, contestId)
    userSub = [id for id in ids if id[0] == userId]
    data = [[x[0], x[1], x[2], x[3], process_submission(x[4],get_submission_detail(s, x[4]))] for x in userSub]
    returnArr = []
    for sub in data:
        returnArr.append({
            "user": sub[0],
            "task": sub[2],
            "time": sub[3],
            "key": sub[4][0],
            "score": sum(sub[4][1]),
            "token": False,
            "extra": sub[4][1]
        })

    return returnArr

def process_submission(id,submission):
    print('[Submission Detail]: '+submission)
    start = 0
    place = submission.find('Group')
    subtasks = []
    while (place >= 0):
        start = place+1
        place = submission.find(':', start)
        for i in range(place+2, place+10):
            if (submission[i] == ' '):
                subtasks.append(float(submission[place+2 : i]))
                break
        place = submission.find('Group', start)
    return [id,subtasks]

if __name__ == '__main__':
    # handle = input('enter handle: ')
    handle = 'owo' # CHANGE IT
    password = getpass.getpass('enter password: ')
    contestId = int(input('contestId: '))
    s = Session()
    login(s, handle, password)
    submission_ids = get_submission_ids(s, contestId);
    data = [[x[0], x[1], x[2], x[3], process_submission(get_submission_detail(s, x[4]))] for x in submission_ids]
    file = open(str(contestId) + '.txt', 'w')
    for submission in data:
        file.write(str(submission) + '\n')
    logout(s)
