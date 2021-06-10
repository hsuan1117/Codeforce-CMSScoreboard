import getpass, re, json
from requests import Session
from hashlib import sha512
from urllib.parse import urlencode
from time import time
import os
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
    res = s.get('https://codeforces.com')
    csrf_token = re.findall('<meta name="X-Csrf-Token" content="(.{32})"/>', res.text)[0]
    data = {
        'csrf_token': csrf_token,
        'submissionId': ID,
    }
    res = s.post('https://codeforces.com/group/HELkcZPVHX/data/judgeProtocol', data = data) # CHANGE IT
    return res.text

def logout(s):
    res = s.get('https://codeforces.com')
    link = re.findall('<a href="(/.{32}/logout)">Logout</a>', res.text)[0]
    res = s.get('https://codeforces.com' + link)
    assert 'Logout' not in res.text

def get_users(s, contestId, key, secret):
    data = urlencode({
        'apiKey': key,
        'contestId': contestId,
        # 'count': 100,
        # 'from': 1,
        'time': int(time())
    })
    methods = 'contest.standings'
    apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
    res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
    api_json = json.loads(res.text)

    print(api_json['result'])
    return api_json['result']

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

def get_submission_ids(s, contestId, key, secret):
    contestId = 328447
    data = urlencode({
        'apiKey': key,
        'contestId': contestId,
        # 'count': 100,
        # 'from': 1,
        'time': int(time())
    })
    methods = 'contest.status'
    apiSig = sha512(f'123456/{methods}?{data}#{secret}'.encode()).hexdigest()
    res = s.get(f'https://codeforces.com/api/{methods}?{data}', params = {'apiSig': '123456' + apiSig})
    api_json = json.loads(res.text)
    submission_ids = []
    print(api_json)
    for submission_info in api_json['result']:
        print(api_json['result'])
        if (submission_info['author']['participantType'] == 'MANAGER'):
            continue
        if (submission_info['relativeTimeSeconds'] == 2147483647):
            continue
        # if (submission_info['points'] == 0.0):
            # continue
        handle = submission_info['author']['members'][0]['handle']
        participant_type = submission_info['author']['participantType']
        problem_index = submission_info['problem']['index']
        submission_time = submission_info['relativeTimeSeconds']
        submission_id = submission_info['id']
        submission_ids.append([handle, participant_type, problem_index, submission_time, submission_id])
    return submission_ids

def process_submission(submission):
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
    return subtasks

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
