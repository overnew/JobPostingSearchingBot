from elasticsearch import Elasticsearch, helpers
import json
from datetime import datetime, date, timedelta
import QueryMaker
import os


class ElasticCloud:
    __worknet_index_name = 'worknet_final'
    __programmers_index_name = 'programmers_final'

    def __init__(self):
        self.ELASTIC_PASSWORD = os.environ['ELASTIC_CLOUD_PASSWORD']
        self.CLOUD_ID = os.environ['ELASTIC_CLOUD_ID']

        self.client = Elasticsearch(
            cloud_id=self.CLOUD_ID,
            basic_auth=("elastic", self.ELASTIC_PASSWORD)
        )

    def search_query_by_workflow(self, data_dict: dict) -> str:
        resource = data_dict['출처']
        ret = ''

        if '프로그래머스' in resource:
            ret += self.__search_query_by_workflow_index(self.__programmers_index_name, data_dict)

        if '워크넷' in resource:
            ret += self.__search_query_by_workflow_index(self.__worknet_index_name, data_dict)

        return ret

    def __search_query_by_workflow_index(self, index_name, data_dict: dict) -> str:
        condition = [QueryMaker.due_day_unable_query()]

        if data_dict['키워드'] != '':
            condition.append(QueryMaker.keyword_query(data_dict['키워드']))

        if data_dict['공고 등록일자'] != '':
            condition.append(QueryMaker.crawl_day_query(data_dict['공고 등록일자']))

        if data_dict['경력'] != '':
            condition.append(QueryMaker.career_query(data_dict['경력']))

        if data_dict['근무 위치'] != '':
            condition.append(QueryMaker.location_query(data_dict['근무 위치']))

        ret = self.client.search(index=index_name, query={
            "bool": {
                "filter": condition
            }
        })

        return self.__reform_query_result(ret)

    def get_contain_keyword(self, keyword: str) -> str:
        keyword_from = "*" + keyword + "*"
        ret = self.__get_contain_keyword_by_index_name(self.__programmers_index_name, keyword_from)
        ret += self.__get_contain_keyword_by_index_name(self.__worknet_index_name, keyword_from)

        return ret

    def __get_contain_keyword_by_index_name(self, index_name: str, keyword_form: str):
        ret = self.client.search(index=index_name, query={
            "bool": {
                "filter": [
                    QueryMaker.due_day_unable_query(),
                    {
                        "query_string": {
                            "query": keyword_form
                        }
                    }
                ]
            }
        })
        return self.__reform_query_result(ret)

    def get_recent_posting(self) -> str:
        ret = self.__get_recent_posting_by_index_name(self.__programmers_index_name)
        # ret += self.__get_recent_posting_by_index_name(self.__worknet_index_name)

        return ret

    def __get_recent_posting_by_index_name(self, index_name: str) -> str:
        ret = self.client.search(index=index_name, query={
            "bool": {
                "filter": [
                    QueryMaker.due_day_unable_query(),
                    {
                        "range": {
                            "due": {
                                "gte": date.today() - timedelta(days=1)
                            }
                        }
                    }
                ]
            }
        })

        return self.__reform_query_result(ret)

    def __reform_query_result(self, ret: str) -> str:
        line_cap = "\n\n\n"
        reform = ""

        for i, row in enumerate(ret['hits']['hits']):
            data = row['_source']
            title = "*" + data['title'] + "*"
            company = "회사: " + data['company']
            location = "근무 위치: " + data['location']
            career = "경력: " + data['career']
            link = data['link']

            if 'salary' in data:
                salary = "급여: "
                if 'salary_type' in data and data['salary_type'] != '회사내규에 따름':
                    salary += data['salary_type'] + " "

                salary += data['salary']
            else:
                salary = "급여: 추후 협의"
            reform += title + "\n" + company + "\n" + location + "\n" + career + "\n" + salary + "\n" + link + line_cap

        return reform
