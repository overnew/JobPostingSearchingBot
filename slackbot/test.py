import config
import re
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from elasticConnect import getQueryToCloud
import json

bot_token = os.environ['bot_token']
app = App(token=os.environ['app_token'])


@app.event("app_mention")  # 앱을 언급했을 때
def who_am_i(event, client, message, say):
  print('event:', event)
  print('client:', client)
  print('message:', message)
  say(f'저는 당신의 길을 넓혀주는 봇입니다. 안녕하세요! <@{event["user"]}>')

@app.message(re.compile("lunch"))
def regex(event, client, message, say):
    say('eat burger')


@app.message("최신 공고")
def queryStart(event, client, message, say):
    say(getQueryToCloud())
    

@app.event("workflow_published")
def workflow(event, client, message, say):
    print("됐드")
    say("let's go")


@app.message(re.compile("질의"))
def regex2(event, client, message, say):
#   print('event:', event)
#   print('client:', client)
#   print('message:', message)
#   print(type(event))
    print('message:', event['text'])
    print(event['blocks'][0]['elements'])
    say('찾았다 임마')
  

if __name__ == '__main__':
    handler = SocketModeHandler(app_token=os.environ['app_token'],app=app)
    handler.start()
    