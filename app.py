###########################################
from flask import Flask, request, send_from_directory, jsonify, Response, redirect, url_for
from cf import *
from judgeProtocol import *
from requests import Session
#import codeforces_api
import os
from dotenv import load_dotenv
###########################################

app = Flask(__name__,static_url_path='')
load_dotenv()
#cf_api = codeforces_api.CodeforcesApi (os.getenv('API_KEY'), os.getenv('SECRET'))
s = Session()

@app.route('/')
def index():
    return redirect(url_for('send_ranking'))

@app.route('/dev/')
def dev():
    #s = Session()
    login(s, os.getenv('handle'), os.getenv('password'))
    #submission_ids = get_submission_ids(s, 328447, os.getenv('API_KEY'), os.getenv('SECRET'));
    #print(submission_ids)
    #return get_submission_detail(s, 118062611)

    return jsonify(get_users(s, 328447, os.getenv('API_KEY'), os.getenv('SECRET')))


@app.route('/rank/')
@app.route('/rank/<path:x>')
def send_ranking(x='Ranking.html'):
    print(x)
    root_dir = os.path.dirname(__file__)
    return send_from_directory(root_dir, x)

@app.route('/rank/contests/')
def contests():
    return jsonify(get_contest(s,328447))

@app.route('/rank/teams/')
def teams():
    return jsonify({})

@app.route('/rank/tasks/')
def tasks():
    return jsonify(get_tasks(s,328447))

@app.route('/rank/users/')
def users():
    return jsonify(get_users(s,328447))

@app.route('/rank/scores/')
def scores():
    login(s, os.getenv('handle'), os.getenv('password'))
    submission_ids = get_submission_ids(s, 328447)
    print(submission_ids)
    data = [[x[0], x[1], x[2], x[3], process_submission(x[4],get_submission_detail(s, x[4]))] for x in submission_ids]
    returnObj = {}
    for submission in data:
        if submission[0] in returnObj:
            if submission[2] in returnObj[submission[0]]:
                returnObj[submission[0]] = {
                    submission[2]: max(sum(submission[4][1]),(returnObj[submission[0]][submission[2]]))
                }

        returnObj[submission[0]] = {
            submission[2]: sum(submission[4][1])
        }
    return jsonify(returnObj)

@app.route('/rank/history/')
def history():
    return jsonify(
[
    ["test1909_5fbwu5230", "Pinata", 1568107457, 100.0]
]
    )

@app.route('/rank/sublist/<id>/')
def sublist(id):
    return jsonify(
[
    {
        "user": "test1909_5fbwu5230",
        "task": "Pinata",
        "time": 1568637337,
        "key": "5230",
        "score": 100.0,
        "token": False,
        "extra": ["0", "0", "0", "0"]
    }
]
    )


@app.route('/rank/events/')
def events():
    return Response('',
                          mimetype="text/event-stream")

@app.route('/rank/logo/')
def logo():
    root_dir = os.path.dirname(__file__)
    return send_from_directory(os.path.join(root_dir,'img'), 'logo-resize.jpg')

@app.route('/rank/faces/<id>/')
def faces(id):
    root_dir = os.path.dirname(__file__)
    return send_from_directory(os.path.join(root_dir,'img'), 'face.png')



if __name__ == "__main__":
    app.run(debug=True,threaded=True)
