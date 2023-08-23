import re
import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from ElasticQuery import ElasticCloud


bot_token = os.environ['bot_token']
app = App(token=bot_token)
cloud = ElasticCloud()


@app.event("app_mention")  # 앱을 언급했을 때
def app_mention(event, client, message, say):
    __introduce_app(event, client, message, say)


@app.event("bot_added")  # 봇 추가 되었을 때
def bot_added(event, client, message, say):
    __introduce_app(event, client, message, say)


def __introduce_app(event, client, message, say):
    print('event:', event)
    print('client:', client)
    print('message:', message)
    say(f'저는 당신의 길을 넓혀주는 봇입니다. 안녕하세요!\n'
        f'사용 설명을 확인 하려면 \'help\'를 입력해주세요! <@{event["user"]}>')


@app.message(re.compile("lunch"))
def regex(event, client, message, say):
    say('eat burger')


@app.message(re.compile("help"))
def send_help_message(say):
    info = "*다양한 조건 검색 하려면 워크플로우로 제출해 주세요!*\n " \
           "<https://slack.com/shortcuts/Ft05M43RB4CX/26d05c5af0233fbaf71d6522a1f37584|워크플로우 바로가기> \n\n" \
           "*키워드:<검색할 키워드>*\n해당 키워드가 들어있는 모든 채용공고를 검색해 드려요!\n\n" \
           "*최신 공고*\n 어제부터 오늘까지 수집된 채용 공고를 보여 드려요!"

    block = {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": info
                }
            }
        ]}

    say(block)


@app.message(re.compile("최신 공고"))
def queryStart(event, client, message, say):
    say(cloud.get_recent_posting())
    # say("흥칫뿡")


@app.message(re.compile("탐색:"))
def queryStart(event, client, message, say):
    keyword = event['text'].replace("탐색:", "").lstrip()
    ret = cloud.get_contain_keyword(keyword)

    if ret == "":
        ret = "검색된 데이터가 없습니다..."

    say(ret)


@app.message(re.compile("질의 시작"))
def exe_workflow(event, client, message, say):
    #   print('event:', event)
    #   print('client:', client)
    #   print('message:', message)
    #   print(type(event))
    #print('message:', event['text'])
    workflow_body: list = event['text'].split("\n*-조건-*\n")[1].split("\n")

    data_dict = dict()

    for i, row in enumerate(workflow_body):
        #print(row)
        try:
            query_data = row.split(": ")
            query_key = query_data[0]
            query_value = query_data[1]
            data_dict[query_key] = query_value
        except:
            print("except occur from ")
            print(row)

    print(data_dict)

    # print(event['blocks'][0]['elements'])
    ret = cloud.search_query_by_workflow(data_dict)

    if ret == "":
        ret = "검색된 데이터가 없습니다..."

    say(ret)

# @app.event("message")
# def handle_message_events(body, logger):
#     logger.info(body)


if __name__ == '__main__':
    handler = SocketModeHandler(app_token=os.environ['app_token'], app=app)
    handler.start()
