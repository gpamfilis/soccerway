import requests
import time
from bs4 import BeautifulSoup

def get_data_(date):
    date_url = date.replace('-','/')+'/'

    res = requests.get("http://int.soccerway.com/matches/"+date_url)
    soup = BeautifulSoup(res.text,"html5lib")

    table_cont = soup.findAll("div", { "class" : "table-container" })[0]

    main_table = table_cont.find('table').find('tbody')
    rows = main_table.find_all('tr')
    if len(rows)==0:
        print('no data')
        return None
    else:
        champ_name_id = []

        for i in range(len(rows)):
            try:
                champ_name_id.append([i,rows[i].find('h3').text])
            except AttributeError as e:
                pass

        ### Get parameters for api call

        champs, cids = api_get_champs_and_cid(main_table)

#         print(champs)
        
        raw_data_from_api_call = get_games(date=date,cids=cids)
#         print("raw_api_data: ",raw_data_from_api_call)
        api_data = dict(zip(champs,raw_data_from_api_call))

        # champ_name_id

        actual = get_index_for_shown_matches(champ_name_id)
        if actual is None:
            raw_page_data = {}
            if api_data is None:
                print('no data')
            else:
                raw_page_data.update(api_data)
        else:
            champ_total_indexes = get_match_indexes_for_shown_matches(actual)
#             print(champ_total_indexes)
            raw_page_data = return_raw_page_matches(rows, actual, champ_name_id,champ_total_indexes)
    
            if raw_page_data is None:
                print('no raw page data')
            else:
                raw_page_data.update(api_data)
        # print("get data")
        return raw_page_data


def get_match(date="2000-11-11",cid=74):
	# print("get match: {0}".format(cid))
    param1 = 'block_id=page_matches_1_block_date_matches_1'
    params = 'params={"competition_id":'+'{}'.format(cid)+'}'
    a = 'http://int.soccerway.com/a/block_date_matches?'+param1+'&'+ \
    'callback_params={"bookmaker_urls":{"13":[{"link":"http://www.bet365.com/home/?affiliate=365_179024","name":"Bet 365"}]},"block_service_id":"matches_index_block_datematches","date":"%s","stage-value":"5"}'%(date)+\
    '&action=showMatches&'+params
    res = requests.get(a)
    # print("get match:")
    if res.status_code!=200:
        print(res.status_code)
        return None
    else:
        js = res.json()
        if len(js['commands'][0]['parameters']['content']) <5:
            return None
        else:
            return js['commands'][0]['parameters']['content']

def insert_date(data,date="ge"):
    new = []
    for d in data:
        d.insert(0, date)
        new.append(d)
        del d
    return new

def insert_champ(data,champ="ge"):
    new = []
    for d in data:
        d.insert(0, champ)
        new.append(d)
        del d
    return new


def parse_matches_v2(body):
    if type(body) is list:
        body = body[0]
    atags = body.find_all('a')
    games = []
    n=0
    game = []

    for i in range(len(atags)):
        atag = atags[i]
        if "teams" in atag.attrs['href']:
            ga = atag['title']
            game.append(ga)
            n+=1
        elif "matches"  in atag.attrs['href']:
            text = atag.text
            if "More info" in text:
                pass
            elif "View events" in text:
                pass
            else:
                score=text
                game.append(score.strip()) # always? strip?
                n+=1
        if n%3==0:
            if len(game) ==0:
                pass
            else:
                games.append(game)
                game = []
    return games

def get_games(date="2000-11-11", cids=[74], parse=False):
    raw = []
    for i in cids:
        data = get_match(date=date,cid=i)
        time.sleep(1)
        raw.append(data)
    matches = []
    for data in raw:
        if data is None:
            continue
        else:
            soup = BeautifulSoup(data, "html5lib")
            body = soup.find('body')
            if parse:
                parsed = parse_matches(body)
            else:
                parsed = body
        matches.append(parsed)
    return matches


def api_get_champs_and_cid(main_table):
    date_matches = main_table.findAll("tr", {"id" : lambda L: L and L.startswith('date_matches'),"class":"group-head clickable "})
    champs = []
    cids = []
    for d in range(len(date_matches)):
        row = date_matches[d]
        champ = row.find('h3').text
        id_str = int(row.attrs['id'].split('-')[1])
        champs.append(champ)
        cids.append(id_str)
    return champs, cids


def get_index_for_shown_matches(champ_name_id):
    skips = [id_[0] for i, id_ in enumerate(champ_name_id)]
    actual = []
    last = 0
    n=0
    for i in range(len(skips)-1):
        
        if skips[i+1]-skips[i]>=2:
            actual.append(skips[i])
            last+=1
        else:
            n+=1
    actual.append(skips[last])
    if len(actual)==1:
        return None
    else:
        return actual

def get_match_indexes_for_shown_matches(actual):
    n=1
    champ_total_indexes = []
    for j in range(len(actual)-1):
        start = actual[n-1]+1
        end = actual[n]
        champ_index=[]
        for i in range(start,end):
            champ_index.append(i)
        n+=1
        champ_total_indexes.append(champ_index)
    return champ_total_indexes

def return_raw_page_matches(rows, actual, champ_name_id,champ_total_indexes):
    page_champs = champ_name_id[:len(actual)-1]
    total = []
    for champs in champ_total_indexes:
        raw = [rows[i] for i in champs]
    #     print(raw)
        total.append(raw)
    shown_matches = dict(zip([c[1] for c in page_champs],total))
    return shown_matches