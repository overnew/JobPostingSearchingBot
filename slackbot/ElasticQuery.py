from elasticsearch import Elasticsearch, helpers
import json
from datetime import datetime, date, timedelta
import QueryMaker
import os


class ElasticCloud:
    #__worknet_index_name = 'worknet_crawle_test2'
    #__programmers_index_name = 'programmers_crawle_test'
    __union_index_name = 'job_post_union_ver1'
    max_size_searched_post = 8

    def __init__(self):
        self.ELASTIC_PASSWORD = os.environ['ELASTIC_CLOUD_PASSWORD']
        self.CLOUD_ID = os.environ['ELASTIC_CLOUD_ID']

        self.client = Elasticsearch(
            cloud_id=self.CLOUD_ID,
            basic_auth=("elastic", self.ELASTIC_PASSWORD)
        )

    def search_query_by_workflow(self, data_dict: dict):
        ret = self.__search_query_by_workflow_index(self.__union_index_name, data_dict)
        return ret

    def __search_query_by_workflow_index(self, index_name, data_dict: dict):
        condition = []

        if data_dict['공고 등록일자'] != '':
            condition.append(QueryMaker.crawl_day_query(data_dict['공고 등록일자']))

        if data_dict['경력'] != '':
            search_word: str = data_dict['경력']
            condition.append(QueryMaker.career_query(search_word))

        if data_dict['근무 위치'] != '':
            condition.append(QueryMaker.location_query(data_dict['근무 위치']))

        ret = self.client.search(index=index_name, size=self.max_size_searched_post, sort=[
            {"_score": {"order": "desc"}}, {"career_start": {"order": "asc"}}
        ], query=self.__make_score_query(data_dict['키워드'], condition))
        return self.__reform_query_result(ret, condition)

    def get_contain_keyword(self, keyword: str):
        ret = self.__search_by_score(self.__union_index_name, keyword)
        return ret

    def __search_by_score(self, index_name: str, keyword_form: str):
        ret = self.client.search(index=index_name, size=self.max_size_searched_post, sort=[
            {"_score": {"order": "desc"}}, {"career_start": {"order": "asc"}}
        ], query=self.__make_score_query(keyword_form))
        return self.__reform_query_result(ret)

    def get_contain_keyword_paging(self, paging_data, keyword_form: str, conditions=[]):
        ret = self.client.search(index=self.__union_index_name, size=self.max_size_searched_post, sort=[{
            "_score": {"order": "desc"}}, {"career_start": {"order": "asc"}}
        ], query=self.__make_score_query(keyword_form, filter_conditions=conditions), search_after=paging_data)
        return self.__reform_query_result(ret, filter_conditions=conditions)

    def __make_score_query(self, keyword_form: str, filter_conditions=[]):
        origin = date.today()
        query = {
            "function_score": {
                "functions": [
                    {"gauss": {
                        "crawle_day": {
                            "origin": origin,
                            "scale": "6d",
                            "offset": "3d",
                            "decay": 0.8
                        }
                    }},
                    {"gauss": {
                        "crawle_day": {
                            "origin": origin,
                            "scale": "14d",
                            "offset": "7d",
                            "decay": 0.4
                        }
                    }},
                    {"gauss": {
                        "crawle_day": {
                            "origin": origin,
                            "scale": "28d",
                            "offset": "14d",
                            "decay": 0.1
                        }
                    }}
                ],
                "query": {
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "title": {
                                        "query": keyword_form,
                                        "boost": 4
                                    }
                                }
                            },
                            {
                                "match": {
                                    "content": {
                                        "query": keyword_form
                                    }
                                }
                            },
                            {
                                "match": {
                                    "content": {
                                        "query": keyword_form,
                                        "operator": "and",
                                        "boost": 2
                                    }
                                }
                            },
                            {
                                "match_phrase": {
                                    "content": {
                                        "query": keyword_form,
                                        "boost": 2
                                    }
                                }
                            }
                        ],
                        "filter": filter_conditions
                    }

                },
                "score_mode": "multiply"

            }

        }
        return query

    def __reform_query_result(self, ret: str, filter_conditions=[]):
        line_cap = "\n\n\n"
        reform = ""
        sort_data = []
        #print("searched : " + str(len(ret['hits']['hits'])))

        for i, row in enumerate(ret['hits']['hits']):
            try:
                data = row['_source']  # 각 공지 데이터

                title = "*<" + data['link'] + "|" + data['title'] + ">*"
                company = "회사: " + data['company']
                location = "근무 위치: " + data['location']
                career = "경력: " + data['career']
                # link = "*<" + data['link'] + "|상세 공고 바로가기>*"
                sort_data = row['sort']

                try:
                    crawling_day = data['crawle_day']
                except:
                    crawling_day = None

                if 'salary' in data:
                    salary = "급여: "
                    if 'salary_type' in data and data['salary_type'] != '회사내규에 따름':
                        salary += data['salary_type'] + " "

                    salary += data['salary']
                else:
                    salary = "급여: 추후 협의"

                reform += title + "\n" + \
                          company + "\n" + \
                          location + "\n" + \
                          career + "\n" + \
                          salary + "\n" + "공고 등록일: " + \
                          crawling_day + line_cap
            except:
                print("error by not enough print => ")
                print(row['_source'])

        return {"hits": len(ret['hits']['hits']), "text": reform, "search_after": sort_data,
                "filter_conditions": filter_conditions}
