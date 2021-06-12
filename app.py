###########################################
import queue

from flask import Flask, request, send_from_directory, jsonify, Response, redirect, url_for, render_template
from judgeProtocol import *
from requests import Session
import os
import numpy as np
from dotenv import load_dotenv

###########################################

app = Flask(__name__, static_url_path='', template_folder='')
load_dotenv()
s = Session()


@app.route('/')
def index():
    root_dir = os.path.dirname(__file__)
    return render_template('home.html', Group=os.getenv('GROUP_ID'), ContestId=os.getenv('CONTEST_ID'))
    return send_from_directory(root_dir, 'home.html')
    # return redirect(url_for('send_ranking'))


@app.route('/dev/')
def dev():
    login(s, os.getenv('HANDLE'), os.getenv('PASSWORD'))
    return jsonify(get_users(s, int(os.getenv('CONTEST_ID')), os.getenv('API_KEY'), os.getenv('SECRET')))


@app.route('/rank/')
@app.route('/rank/<path:x>')
def send_ranking(x='Ranking.html'):
    print(x)
    with open('.gitignore') as f:
        if x in f.read():
            x = 'Ranking.html'
    root_dir = os.path.dirname(__file__)
    return send_from_directory(root_dir, x)


@app.route('/rank/contests/')
def contests():
    return jsonify(get_contest(s, int(os.getenv('CONTEST_ID'))))


@app.route('/rank/teams/')
def teams():
    return jsonify({})


@app.route('/rank/tasks/')
def tasks():
    return jsonify(get_tasks(s, int(os.getenv('CONTEST_ID'))))


@app.route('/rank/users/')
def users():
    return jsonify(get_users(s, int(os.getenv('CONTEST_ID'))))


@app.route('/rank/scores/')
def scores():
    login(s, os.getenv('HANDLE'), os.getenv('PASSWORD'))
    submission_ids = get_submission_ids(s, int(os.getenv('CONTEST_ID')))

    # print(submission_ids)
    # Handle Type ProbIndex SubmitTime [id,subtask]
    data = [[x[0], x[1], x[2], x[3], process_submission(x[4], get_submission_detail(s, x[4]))] for x in submission_ids]
    return_obj = {}

    for submission in data:  # iter data
        if submission[0] in return_obj:  # Check if handle exists
            if submission[2] in return_obj[submission[0]]:  # Check if prob exists
                if submission[4][1] == 0:
                    # Patch Compile Error
                    continue
                #print(1)
                #print("! "+str(submission[4][0]))
                #size = max(np.array(submission[4][1]).shape , np.array(return_obj[submission[0]][submission[2]]).shape)
                #zeros = np.zeros(size)
                #print(np.array(submission[4][1]).resize((20,0)), end=' one\n')
                #print(np.array(return_obj[submission[0]][submission[2]]).resize((20,0)), end=' two\n')
                try:
                    return_obj[submission[0]] = {
                        # 先存 Subtask
                        submission[2]: np.maximum(submission[4][1], return_obj[submission[0]][submission[2]])
                    }
                except:
                    print(submission[4][1])
                    print(return_obj[submission[0]][submission[2]])
                    print('error')
                # print(return_obj)

        return_obj[submission[0]] = {
            submission[2]: submission[4][1]
        }
    # return return_obj
    # returnObj 轉換為總分
    for user in return_obj:
        for task in return_obj[user]:
            return_obj[user][task] = sum(return_obj[user][task])
    return jsonify(return_obj)


@app.route('/rank/history/')
def history():
    return jsonify(get_history(s, int(os.getenv('CONTEST_ID'))))


@app.route('/rank/sublist/<id>/')
def sublist(id):
    return jsonify(get_sublist(s, int(os.getenv('CONTEST_ID')), id))


msgs = queue.Queue(maxsize=5)


@app.route('/rank/events/')
def events():
    msgs.put("only test")

    def stream():
        while True:
            message = msgs.get(True)  # returns a queue.Queue
            print("Sending {}".format(message))
            yield "data: {}\n\n".format(message)

    return Response(stream(),
                    mimetype="text/event-stream")


@app.route('/api/test', methods=['GET'])
def api_parse_sentence():
    msgs.put(request.args.get('sentence'))
    return "OK"


@app.route('/rank/logo/')
def logo():
    root_dir = os.path.dirname(__file__)
    return send_from_directory(os.path.join(root_dir, 'img'), 'logo-resize.jpg')


@app.route('/rank/faces/<id>/')
def faces(id):
    root_dir = os.path.dirname(__file__)
    return send_from_directory(os.path.join(root_dir, 'img'), 'face.png')


@app.after_request
def apply_caching(response):
    response.headers["Timestamp"] = float(time())
    return response


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
