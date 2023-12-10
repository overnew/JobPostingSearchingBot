import re
import os
import datetime
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from ElasticQuery import ElasticCloud
from Subscribe import SubscribeDataSaver

bot_token = os.environ['bot_token']
app = App(token=bot_token)
cloud = ElasticCloud()
sub = SubscribeDataSaver()
__paging_max = 4


@app.event("app_mention")  # 앱을 언급했을 때
def app_mention(event, client, message, say):
    __introduce_app(event, client, message, say)


@app.event("bot_added")  # 봇 추가 되었을 때
def bot_added(event, client, message, say):
    __introduce_app(event, client, message, say)


def __introduce_app(event, client, message, say):
    say(f'저는 여러 사이트의 채용 공고를 한번에 검색해 주는 봇 TATTOO입니다. 안녕하세요!\n'
        f'사용 설명을 확인 하려면 \'help\'를 입력해주세요! <@{event["user"]}>')


@app.message(re.compile("lunch"))
def regex(event, client, message, say):
    say('eat burger')


@app.message(re.compile("(help|도움|도움말)"))
def send_help_message(message,say):
    if ":mag:" in message["text"]:
        return

    info = "*채용 공고 구독 기능과 다양한 Command를 확인하려면 캔버스를 참조해주세요!*\n" \
           "*<https://start-aws.slack.com/docs/T04VBKA4L4Q/F063ABZCF0C|구독 및 Command 사용 방법>*\n\n " \
           "*주요 공고*\n 대기업의 취업 공고 홈페이지 리스트를 보여드려요!\n\n" \
           "*개발 정보*\n 서비스의 소스코드 링크를 보여드려요!\n\n" \
           "*help*\n 도움말을 다시 보여드려요! 🔍"

    say(rap_block(info))


def rap_block(info: str):
    return {
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": info
                }
            }
        ]}


@app.message(re.compile("개발 정보"))
def show_dev_info(event, client, message, say):
    info = "*<https://github.com/overnew/JobPostingCrawler| 크롤링 코드 Github>* \n\n" \
           "*<https://github.com/overnew/JobPostingSearchingBot| slack bot 코드 Github>* \n\n"

    say(rap_block(info))


@app.message(re.compile("주요 공고"))
def show_main_page_list(event, client, message, say):
    info = "*<https://career.woowahan.com/?jobCodes=&employmentTypeCodes=&serviceSectionCodes=&careerPeriod=&keyword=&category=jobGroupCodes%3ABA005007#recruit-list|배달의 민족 이달의 채용 공고>*\n\n" \
           "*<https://about.daangn.com/jobs/|당근 마켓 채용 공고>* \n\n" \
           "*<https://recruit.navercorp.com/rcrt/list.do?srchClassCd=1000000|네이버 채용 공고>*\n\n" \
           "*<https://careers.kakao.com/jobs?part=TECHNOLOGY|카카오 채용 공고>* \n\n" \
           "*<https://www.amazon.jobs/en/search?offset=0&result_limit=10&sort=relevant&country%5B%5D=KOR&business_category%5B%5D=amazon-web-services&distanceType=Mi&radius=24km&latitude=37.55886&longitude=126.99989&loc_group_id=&loc_query=South%20Korea&base_query=&city=&country=KOR&region=&county=&query_options=&&cmpid=SMOTAW401927B|AWS 한국 채용 공고>* \n\n" \
           "*<https://careers.linecorp.com/ko/jobs?ca=Engineering|라인 채용 공고>*\n\n" \
           "*<https://www.coupang.jobs/kr/jobs/?department=Ecommerce+Engineering&department=Play+Engineering&department=Product+UX&department=Search+and+Discovery&department=Search+and+Discovery+Core+Infrastructure&department=Cloud+Platform&department=Corporate+IT&department=eCommerce+Product&department=FTS+(Fulfillment+and+Transportation+System)&department=Marketplace%2c+Catalog+%26+Pricing+Systems&department=Program+Management+Office&department=Customer+Experience+Product|쿠팡 채용 공고>* \n\n"

    say(rap_block(info))


@app.message(re.compile("검색:"))
def query_start(event, client, message, say):
    keyword = event['text'].replace("검색:", "").lstrip()

    if len(keyword) <= 1:
        say("두글자 이상으로 검색해 주세요!")
        return

    ret = cloud.get_contain_keyword(keyword)
    result = ret["text"]
    hits = ret['hits']

    if hits == 0:
        result = "검색된 데이터가 없습니다..."
    elif hits == cloud.max_size_searched_post:
        say(make_paging_button(0, ret["text"], ret['search_after'], keyword))
        return

    say(result)

def query_by_paging(paging_data):
    paging_data_arr = paging_data.split('/')
    paging_cnt = int(paging_data_arr[0]) + 1
    keyword = paging_data_arr[3]
    search_after = [float(paging_data_arr[1]), int(paging_data_arr[2])]
    conditions = json.loads(paging_data_arr[4].replace("'", '"'))


    ret = cloud.get_contain_keyword_paging(search_after, keyword, conditions)

    result = ret["text"]
    hits = ret['hits']
    conditions = ret['filter_conditions']
    if hits == 0:
        result = "검색된 데이터가 없습니다..."
    elif hits == cloud.max_size_searched_post:
        result = make_paging_button(paging_cnt, ret["text"], ret['search_after'], keyword, conditions)

    return result



@app.command("/검색")
def handle_search_command(ack, body, logger, say):
    keyword = body['text'].replace("검색:", "").lstrip()

    if len(keyword) <= 1:
        say("두글자 이상으로 검색해 주세요!")
        return

    ret = cloud.get_contain_keyword(keyword)
    result = ret["text"]
    hits = ret['hits']

    if hits == 0:
        result = "검색된 데이터가 없습니다..."
    elif hits == cloud.max_size_searched_post:
        say(make_paging_button(0, ret["text"], ret['search_after'], keyword))
        return

    ack()
    say(result)

@app.message(re.compile("질의 시작"))
def exe_workflow(event, client, message, say):
    workflow_body: list = event['text'].split("\n*-조건-*\n")[1].split("\n")

    data_dict = dict()

    for i, row in enumerate(workflow_body):
        # print(row)
        try:
            query_data = row.split(": ")
            query_key = query_data[0]
            query_value = query_data[1]
            data_dict[query_key] = query_value
        except:
            print("except occur from ")
            print(row)

    #print(data_dict)

    if len(data_dict['키워드']) <= 1:
        say("키워드는 두글자 이상부터 가능합니다!")
        return

    if data_dict['공고 등록일자'] != '':
        try:
            check_date = data_dict['공고 등록일자'].replace(" ", "")
            check_date = "20" + check_date
            check_date = datetime.datetime.strptime(check_date, '%Y-%m-%d').strftime('%Y-%m-%d')
            data_dict['공고 등록일자'] = check_date
        except:
            say("공고 등록일자 형식이 올바르지 않습니다.")
            return

    # print(event['blocks'][0]['elements'])
    ret = cloud.search_query_by_workflow(data_dict)

    result = ret["text"]
    hits = ret['hits']
    conditions = ret['filter_conditions']

    if hits == 0:
        result = "검색된 데이터가 없습니다..."
    elif hits == cloud.max_size_searched_post:
        say(make_paging_button(0, result, ret['search_after'], data_dict['키워드'], conditions))
        return

    say(result)


@app.command("/구독")
def handle_subscribe_command(ack, body, logger, say):
    #print(body)
    logger.info(body)

    conversations_response = app.client.conversations_open(users=body['user_id'])
    channel_id = conversations_response['channel']['id']

    #dynamo에 저장
    sub.save_subscribe_data(user_id=body['user_id'] ,keyword=body['text'] ,channel_id=channel_id)

    ack()

    response_message = "구독 완료! \n이제 매일 *" + body['text'] + "* 에 대한 채용 공고를 알려드립니다!"

    result = app.client.chat_postMessage(
        channel=channel_id,
        text= response_message
    )

    response_message = "<@" +body['user_id']+"> 님이 키워드 " + response_message
    say(response_message)


# 페이징 용도의 버튼
def make_paging_button(cnt, text, search_after, keyword, conditions = []):
    if cnt >= __paging_max:
        return text

    paging_data = str(cnt) + '/' + str(search_after[0]) + '/' + str(search_after[1]) \
                  + '/' + keyword + '/' + str(conditions)
    paging_button = {
        "text": text + '\n\n',
        "attachments": [
            {
                "text": "좀더 확인 하실래요?",
                "fallback": "unable to see more",
                "callback_id": "paging",
                "color": "#E25372",
                "attachment_type": "default",
                "actions": [
                    {
                        "name": paging_data,
                        "text": "더보기",
                        "type": "button",
                        "value": "더보기"
                    }
                ]
            }
        ]
    }
    return paging_button


@app.action("paging")
def handle_some_action(ack, body, logger, say):
    response = body['actions'][0]['value']
    paging_data = body['actions'][0]['name']

    if response == "더보기":
        ret = query_by_paging(paging_data)
        say(ret)

    ack()
    #logger.info(body)

@app.command("/구독취소")
def handle_unsubscribe_command(ack, body, logger, say):
    #print(body)
    logger.info(body)

    conversations_response = app.client.conversations_open(users=body['user_id'])
    channel_id = conversations_response['channel']['id']

    #dynamo에서 삭제
    sub.delete_subscribe_data(user_id=body['user_id'], channel_id=channel_id)
    ack()

    response_message = "구독 취소 완료! \n이제 DM이 전송 되지 않습니다."

    result = app.client.chat_postMessage(
        channel=channel_id,
        text= response_message
    )

    response_message = "<@" +body['user_id']+"> 님이 키워드 " + response_message
    say(response_message)

if __name__ == '__main__':
    handler = SocketModeHandler(app_token=os.environ['app_token'], app=app)
    handler.start()
