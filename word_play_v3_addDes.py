### 로컬 한글 출력용 ###
import sys
import io
import random
sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')
########################

## slacker import #####
# from slacker import Slacker
#
# slack = Slacker('slack_token')
#######################
import json
import os
import re
import urllib.request
import time

import multiprocessing as mp
from threading import Thread

from urllib import parse #인코딩용 임포트

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "slack_token"
slack_client_id = "slack_id"
slack_client_secret = "slack_secret"
slack_verification = "slack_verif"
sc = SlackClient(slack_token)


def processing_event(queue):
  while True:
      # 큐가 비어있지 않은 경우 로직 실행
      if not queue.empty():
          slack_event = queue.get()

          # Your Processing Code Block gose to here
          channel = slack_event["event"]["channel"]
          text = slack_event["event"]["text"]
          # 챗봇 크롤링 프로세스 로직 함수
          keywords = _crawl_word_keywords(text)

          # 아래에 슬랙 클라이언트 api를 호출하세요
          sc.api_call(
              "chat.postMessage",
              channel=channel,
              text=keywords
          )


def _crawl_word_keywords(text):
    # URL 데이터를 가져올 사이트 url 입력
    #slack.chat.post_message('#general', 'testing sorry')
    #en_lan = '가'.encode('utf-8')
    #print(en_lan) #\xea\xb0\x80 ->%ea%b0%80
    #url = "https://www.wordrow.kr/%EC%8B%9C%EC%9E%91%ED%95%98%EB%8A%94-%EB%A7%90/%EA%B0%80/%EC%84%B8%20%EA%B8%80%EC%9E%90"
    ##임시변수##

    ###########
    keywords = []

    data_list = []


    count = 0
    s_text = text.split() #들어온 채팅을 분할
    a_word = [o_word for o_word in s_text[1]] #첫 단어를 글자로 나눔
    if len(s_text) > 2 and "뭐야" in s_text[2]:
        e_word = parse.quote(s_text[1])
        url = "https://www.wordrow.kr/%EC%8B%9C%EC%9E%91%ED%95%98%EB%8A%94-%EB%A7%90/" + e_word
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")
        w_table = soup.find("h3", class_="card-caption")
        for words in w_table.find_all("small"):
            data_list.append(words.get_text().strip())

        for des in data_list:
            keywords.append(des)

        return u'\n'.join(keywords)

    if len(a_word) != 3:
        keywords.append("저는 세글자 끝말잇기만 지원해요.\nㅇㅇㅇ 쿵쿵따 라고 써주세요\n단어의 뜻이 궁금하면\nㅇㅇㅇ 뭐야 라고 해주세요:)")
        return u'\n'.join(keywords)
    e_word = parse.quote(a_word[2]) #마지막 글자 e_word
    #i_word = text[0]
    #keywords.append(i_word)
    #keywords.append("hi")
    #keywords.append("{}".format(e_word))



    #글자로 시작하는 단어 모두 저장
    for i in range(1, 5):
        if count != 0 and count < 100 :
            break #마지막장이면 아웃

        count = 0 #카운트 초기화
        #백과사전 가서 마지막글자 e_world로 시작하는거 검색
        url = "https://www.wordrow.kr/%EC%8B%9C%EC%9E%91%ED%95%98%EB%8A%94-%EB%A7%90/" + e_word +"/%EC%84%B8%20%EA%B8%80%EC%9E%90?%EC%AA%BD="+str(i)
        soup = BeautifulSoup(urllib.request.urlopen(url).read(), "html.parser")

        w_table = soup.find("div", class_="table")
        if w_table.find("span", class_="h4 text-warning"):#지면
            keywords.append("제가 졌어요ㅠㅠ")
            return u'\n'.join(keywords)

        for datas in w_table.find_all("h3", class_="card-caption"):
            for word_des in datas.find_all("a"):
                data_list.append(word_des.get_text().strip())
                count += 1


    ran_num = random.randrange(1,len(data_list)) #랜덤숫자 정함
    keywords.append("{} 쿵쿵따!".format(data_list[ran_num])) #랜덤단어 출력

    return u'\n'.join(keywords)


# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]
        # 아래에 슬랙 클라이언트 api를 호출하세요
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text="기다려주세요"
        )
        event_queue.put(slack_event)
        return make_response("App mention message has been sent", 200, )
        # channel = slack_event["event"]["channel"]
        # text = slack_event["event"]["text"]

        # keywords = _crawl_word_keywords(text)
        # sc.api_call(
        #     "chat.postMessage",
        #     channel=channel,
        #     text=keywords
        # )

        #return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})

    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    event_queue = mp.Queue()

    p = Thread(target=processing_event, args=(event_queue,))
    p.start()
    print("subprocess started")
    app.run('127.0.0.1', port=5000)
    p.join()
