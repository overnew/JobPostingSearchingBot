import re


def keyword_query(keyword: str):
    keyword_from = "*" + keyword + "*"
    query = {
        "query_string": {
                "query": keyword_from
        }
    }
    return query


def crawl_day_query(day: str):
    query = {
        "range": {
            "due": {
                "gte": day
            }
        }
    }
    return query


def career_query(data:str):
    if data == '경력 무관':
        return __career_none_query("무관")
    elif data == '신입':
        return __career_none_query("신입")
    else:
        career_num = re.sub(r'[^0-9]', '', data)
        return __career_range_query(int(career_num))


def __career_none_query(key_word: str):
    query = {
        "match": {
            "career": key_word
        }
    }

    return query


def __career_range_query(start: int):
    query = {
        "range": {
            "career_start": {
                "gte": start
            }
        }
    }

    return query


def location_query(location:str):
    query = {
        "match": {
            "location": location
        }
    }
    return query
