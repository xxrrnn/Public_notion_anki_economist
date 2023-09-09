import requests
import re
from bs4 import BeautifulSoup
import random
from datetime import timedelta, date
import datetime
import configparser
import matplotlib.pyplot as plt
import os
from collections import OrderedDict
from datetime import datetime as dt
from datetime import timedelta
import multiprocessing
import time
import os
import signal

# short https://www.notion.so/58951b5a29544562a93fd0c1f5d7112f?v=316bed45c314462c84dca09b30578cea&pvs=4
# query_id = "58951b5a29544562a93fd0c1f5d7112f"
# database_id = "316bed45c314462c84dca09b30578cea"
# https://www.notion.so/4d044f4888104a4c89fbe30487f0198f?v=49f70ebd825a4c85a2a13b9ea10180b8&pvs=4




# query_id = "4d044f4888104a4c89fbe30487f0198f"
# database_id = "49f70ebd825a4c85a2a13b9ea10180b8"
guidURL = 'https://dictionary.cambridge.org/dictionary/english-chinese-simplified/'
guidURL_en = 'https://dictionary.cambridge.org/us/dictionary/english/'
class Update_anki:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('token.ini')
        self.token = config.get('token', 'id')
        self.database_id = config.get('database', 'anki_database')  # 取database前边的
        self.query_id = config.get('database', 'anki_query')  # 取database前边的
        self.headers = headers = {
        "Authorization": "Bearer " + self.token,
        "accept": "application/json",
        "Notion-Version": "2022-06-28"  # Notion版本号
    }
        self.today = {}
        self.knowall_list = []
        self.knowsome_list = []
        self.forgetall_list = []
        self.today_query_id = config.get('database', 'today_query')  # 取database前边的
        self.today_database_id = config.get('database', 'today_database')  # 取database前边的
        self.word_level_dict = {}
        self.word_next_dict = {}
        self.count_know_all = 0
        self.count_know_some = 0
        self.count_forget_all = 0
        self.selection_dict = {"KnowAll": "green","KnowSome":"yellow", "ForgetAll":"red"}
        self.date_dict = {}  # 用于release_tension
        self.tomorrow = True
    def delete_page(self,page_id):
        body = {
            'archived': True
        }
        url = 'https://api.notion.com/v1/pages/' + page_id
        notion = requests.patch(url, headers=self.headers, json=body)
        print(notion)
        return 0
    def DataBase_item_delete(self,response):
        print("start deleting")
        count = 0
        for dict in response:
            count += 1
            id = dict['id']
            print(count / len(response), dict['properties']['words']['title'][0]['plain_text'])
            self.delete_page(id)


    def DataBase_item_query(self,query_database_id):
        # query_database_id = self.query_id
        url_notion_block = 'https://api.notion.com/v1/databases/'+query_database_id+'/query'
        res_notion = requests.post(url_notion_block,headers=self.headers)
        S_0 = res_notion.json()
        res_travel = S_0['results']
        if_continue = len(res_travel)
        # print(len(res_travel))
        if if_continue > 0:
            while if_continue % 100 == 0:
                body = {
                    'start_cursor' : res_travel[-1]['id']
                }
                res_notion_plus = requests.post(url_notion_block,headers=self.headers,json = body)
                S_0plus = res_notion_plus.json()
                res_travel_plus = S_0plus['results']
                for i in res_travel_plus:
                    if i['id'] == res_travel[-1]['id']:
                        continue
                    res_travel.append(i)
                if_continue = len(res_travel_plus)
        return res_travel

    def get_cambridge_soup(self,word_to_search):
        current_guideUrl = guidURL
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.0; WOW64; rv:24.0) Gecko/20100101 Firefox/24.0'}
        url = current_guideUrl + word_to_search
        source_code = requests.get(url, headers=headers).text
        soup = BeautifulSoup(source_code, 'html.parser')
        is_chinese_soup = True
        if len(soup.find_all(class_='def ddef_d db')) != 0:
            return soup,is_chinese_soup
        else:
            is_chinese_soup = False
            current_guideUrl = guidURL_en
            url = current_guideUrl + word_to_search
            source_code = requests.get(url, headers=headers).text
            soup = BeautifulSoup(source_code, 'html.parser')
            if len(soup.find_all(class_='def ddef_d db')) == 0:
                return [],is_chinese_soup
            else:
                return soup,is_chinese_soup

    def get_cambridge_origin_pronoun_voice(self,soup, flag = 1):
        if len(soup) == 0:
            return None,None,None
        # 原词行获取
        #<span class="hw dhw">normalize</span>
        # origin_spans = soup.find_all(class_='hw dhw')
        origin_spans = soup.find_all(class_='tb ttn')
        if len(origin_spans) != 0:
            for origin_span in origin_spans:
                origin_pattern = r'>(.*?)<'
                origin = re.findall(origin_pattern, str(origin_spans))
                if origin != None:
                    break
        else:
            return None,None,None
        # print(origin[0])
        # 音标获取
        # <span class="ipa dipa lpr-2 lpl-1">ˈnaɪ.sə.ti</span>
        pronoun_spans = soup.find_all(class_='ipa dipa lpr-2 lpl-1')
        # print(pronoun_spans)
        # for pronoun_span in pronoun_spans:
        pronoun_pattern = r'>(.*?)<'
        pronoun_gets = re.findall(pronoun_pattern, str(pronoun_spans))
        pronounciation = ""
        for pronoun_get in pronoun_gets:
            if '/' in pronoun_get or pronoun_get[len(pronoun_get)-1] == '/' or len(pronoun_get) == 0:
                continue
            pronounciation = '/' + pronoun_get + '/'
            break
        # print(pronounciation)

        # voice网址获取
        voice_spans = soup.find_all('source', type='audio/mpeg')
        # print("voice_up_spans",voice_up_spans)
        pattern = re.compile(r'src="([^"]+\.mp3)"')
        url_voice = ""
        for voice_span in voice_spans:
            match = pattern.search(str(voice_span))
            if match:
                extracted_voice = match.group(1)
                if "us_pron" in extracted_voice:
                    url_voice = "https://dictionary.cambridge.org" + extracted_voice
                    break
                    pass
        # print(url_voice)
        return origin[0], pronounciation, url_voice


    # def notion_words_patch(page_id,origin, pronoun, url_voice):
    def notion_words_patch(self,page_id,level):
        print(level)
        colors = ["default","gray","brown","orange","yellow","green","blue","purple","pink","red"]
        data = {
            "parent": {"type": "database_id", "database_id": "49f70ebd825a4c85a2a13b9ea10180b8"},
            'properties': {
                "Level": {"select": {"name": level, "color": colors[int(level)]}},
                # "words": {"title": [{"type": "text", "text": {"content": origin}}]},
                # "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                # "voice": {"url": url_voice},
                # "Date Wrong": {"date": {"start": "2023-11-21"}},
                # '移動方式': {'rich_text': [{"text": {"content": move}}]},
            }
        }
        r = requests.patch(
            "https://api.notion.com/v1/pages/{}".format(page_id),
            json=data,
            headers=self.headers,
        )
        print(r.text)

    def patch_all_pronoun_and_voice(self,response):
        all_page_id = []
        all_words = []
        count = 0
        for dict in response:
            all_page_id.append(dict['id'])
        for dict in response:
            try:
                if dict['properties']['passage']['multi_select'][0]['name'] != -1:
                    # print(dict['properties']['words']['title'][0]['plain_text'])
                    all_words.append(dict['properties']['words']['title'][0]['plain_text'])
                    count += 1
            except:
                print(dict)
        for word_num in range(len(all_words)):
            word = all_words[word_num]
            page_id = all_page_id[word_num]
            print(word)
            print(word_num / count, count)
            soup,is_chinese = self.get_cambridge_soup(word)
            origin, pronounciation, url_voice = self.get_cambridge_origin_pronoun_voice(soup)
            if origin == None:
                origin = word
            if pronounciation == None:
                pronounciation = ""
            if url_voice == None:
                url_voice = ""
            self.notion_words_patch(page_id ,origin,pronounciation,url_voice)
        pass
    def patch_all_level(self,response):
        levels = []
        all_page_id = []
        count = 0
        for dict in response:
            all_page_id.append(dict['id'])
        for dict in response:
            con = True
            for num in range(6,0,-1):
                checkbox = 'Checkbox ' + str(num)
                if dict['properties'][checkbox]['checkbox'] == True:
                    levels.append(str(num))
                    count += 1
                    con = False
                    break
            if con:
                levels.append('0')

        print(levels)
        for num in range(len(all_page_id)):
            page_id = all_page_id[num]
            level = levels[num]
            self.notion_words_patch(page_id,level)




    def get_day_of_day(self,n=0):
        '''''
        if n>=0,date is larger than today
        if n<0,date is less than today
        date format = "YYYY-MM-DD"
        '''
        if (n < 0):
            n = abs(n)
            # formatted_date = current_date.strftime('%Y-%m-%d')
            return (date.today() - timedelta(days=n)).strftime('%Y-%m-%d')
        else:
            return (date.today() + timedelta(days=n)).strftime('%Y-%m-%d')

    def patch_all_date(self,response):
        dates = []
        all_page_id = []
        count = 0
        d_day = [0,1,2,3,4,5,6,7]
        for dict in response:
            all_page_id.append(dict['id'])
            count += 1
        for i in range(len(all_page_id)):
            day = random.sample(d_day, len(d_day))[0]
            dates.append(self.get_day_of_day(day))

        print(dates)
        for i in range(len(all_page_id)):
            print(i,i/count)
            date = dates[i]
            page_id = all_page_id[i]
            data = {
                "parent": {"type": "database_id", "database_id": self.database_id},
                'properties': {
                    "Last": {"date": {"start": date}},
                    # "Level": {"select": {"name": level, "color": colors[int(level)]}},
                    # "words": {"title": [{"type": "text", "text": {"content": origin}}]},
                    # "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                    # "voice": {"url": url_voice},
                    # "Date Wrong": {"date": {"start": "2023-11-21"}},
                    # '移動方式': {'rich_text': [{"text": {"content": move}}]},
                }
            }
            r = requests.patch(
                "https://api.notion.com/v1/pages/{}".format(page_id),
                json=data,
                headers=self.headers,
            )
            print(r.text)

    def next_day_on_level(self,level):
        if level == '0':
            n = 1
        elif level == '1':
            n = 2
        elif level == '2':
            n = 4
        elif level == '3':
            # n = 3
            n = int(random.randint(6,8))
        elif level == '4':
            # n = 8
            n = int(random.randint(13,16))
        elif level == '5':
            # n = 15
            n = int(random.randint(28,32))
        elif level == '6':
            # n = 30
            n = int(random.randint(60,68))
        elif level == '7':
            # n = 60
            n = int(random.randint(125,131))
        elif level == '8':
            # n = 90
            n = int(random.randint(252,260))
        elif level == '9':
            n = 365
        else:
            n = 1
            print("wrong level")
        return (date.today() + timedelta(days=n)).strftime('%Y-%m-%d')

    def patch_one_data(self, data, page_id):
        r = requests.patch(
            "https://api.notion.com/v1/pages/{}".format(page_id),
            json=data,
            headers=self.headers,
        )
        print(r.text)

    def patch_update(self):
        # 获取当前日期和时间
        current_datetime = dt.now()
        # 计算当日凌晨4点的时间
        today_4am = current_datetime.replace(hour=4, minute=0, second=0, microsecond=0)
        if current_datetime < today_4am:
            print("现在是"+str(current_datetime)+"还没有到凌晨4点")
            self.tomorrow = False
        else:
            print("现在是"+str(current_datetime)+"已经超过凌晨四点")
            self.tomorrow = True
        print("start get response")
        response = self.DataBase_item_query(self.query_id)
        modified_time = os.path.getmtime("TxtDataFiles/word_today.txt")
        modified_datetime = datetime.datetime.fromtimestamp(modified_time)
        modified_datetime = modified_datetime.date()
        # 获取当前日期
        if modified_datetime != dt.today().date():
            with open("TxtDataFiles/word_today.txt", "w") as file:
                file.truncate()
        # self.word_next_dict = {}

        colors = ["default","gray","brown","orange","yellow","green","blue","purple","pink","red"]
        all_page_id = []
        count = 0
        today = date.today()
        today_str = date.today().strftime('%Y-%m-%d')

        word_date_id = {}
        for dict in response:
            count += 1
            print(count/len(response))
            print(count ,len(response))
            try:
                word = dict['properties']['words']['title'][0]['plain_text']
            except:
                word = "xxxxxxxx"
            page_id = dict['id']
            KnowAll = dict['properties']["KnowAll"]['checkbox']
            KnowSome = dict['properties']["KnowSome"]['checkbox']
            ForgetAll = dict['properties']["ForgetAll"]['checkbox']
            checked_times = dict['properties']["Checked Times"]['number']
            # if word == "jello":
            #     pass
            # 如果选了
            if KnowAll or KnowSome or ForgetAll:
                checked_times += 1
                print(word)
                print(KnowAll, KnowSome, ForgetAll)
                level = dict['properties']["Level"]['select']['name']
                word_selection = ""
                if KnowAll:
                    word_selection = 'KnowAll'
                    with open("TxtDataFiles/word_today.txt", "a", encoding="utf-8") as file:
                        file.write(word + " |KnowAll""\n")
                    self.count_know_all += 1
                    self.knowall_list.append(dict)
                    next_level = str(int(level) + 1)
                    if int(next_level) > 9:
                        next_level = '9'
                    next_str = self.next_day_on_level(next_level)
                elif KnowSome:
                    word_selection = 'KnowSome'
                    with open("TxtDataFiles/word_today.txt", "a", encoding="utf-8") as file:
                        file.write(word + " |KnowSome""\n")
                    self.count_know_some += 1
                    self.knowsome_list.append(dict)
                    if int(level) >= 4:
                        next_level = str(int(int(level) /2))
                        # if int(next_level) < 1:
                        #     next_level = '0'
                    elif int(level) >= 2:
                        next_level = str(int(level) - 1)
                    else:
                        next_level = str(int(level) )
                    next_str = self.next_day_on_level(next_level)
                elif ForgetAll:
                    word_selection = 'ForgetAll'
                    with open("TxtDataFiles/word_today.txt", "a", encoding="utf-8") as file:
                        file.write(word + " |ForgetAll\n")
                    self.count_forget_all += 1
                    self.forgetall_list.append(dict)
                    next_level = '0'
                    next_str = self.next_day_on_level(next_level)
                else:
                    next_level = '0'
                    next_str = self.next_day_on_level(next_level)
                try:
                    self.word_next_dict[next_str] = self.word_next_dict[next_str] + 1
                except:
                    self.word_next_dict[next_str] = 1
                try:
                    self.word_level_dict[next_level] = self.word_level_dict[next_level] + 1
                except:
                    self.word_level_dict[next_level] = 1
                if next_str in self.date_dict.keys():
                    self.date_dict[date].append(dict)
                else:
                    self.date_dict[date] = [dict]
                # self.today["KnowAll"] = self.knowall_list
                # self.today["KnowSome"] = self.knowsome_list
                # self.today["ForgetAll"] = self.forgetall_list

                data = {
                    "parent": {"type": "database_id", "database_id": self.database_id},
                    'properties': {
                        "Last": {"date": {"start": today_str}},
                        "Next": {"date": {"start": next_str}},
                        "Level": {"select": {"name": next_level, "color": colors[int(next_level)]}},
                        "KnowAll": {"checkbox": False},
                        "KnowSome": {"checkbox": False},
                        "ForgetAll": {"checkbox": False},
                        "Checked Times": {"number": checked_times},

                        # "words": {"title": [{"type": "text", "text": {"content": origin}}]},
                        # "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                        # "voice": {"url": url_voice},
                        # "Date Wrong": {"date": {"start": "2023-11-21"}},
                        # '移動方式': {'rich_text': [{"text": {"content": move}}]},
                    }
                }
                # must change
                self.patch_one_data(data,page_id)
                # self.checked_move_to_today(dict,word_selection)
                self.run_upload_with_timeout(dict,word_selection)

            # 如果没选
            else:
                try:
                    next = dict['properties']["Next"]['date']['start']
                    last = dict['properties']["Last"]['date']['start']
                    level = dict['properties']["Level"]['select']['name']
                except:
                    next = None
                    level = 0
                # second_time = datetime.datetime.strptime(next, "%Y-%m-%d %H:%M:%S")

                try:
                    self.word_level_dict[level] = self.word_level_dict[level] + 1
                except:
                    self.word_level_dict[level] = 1

                if next != None:
                    second_time = datetime.datetime.strptime(next, "%Y-%m-%d").date()
                    # second_time_hour = datetime.datetime.strptime(next, "%Y-%m-%d")
                    # last_time = datetime.datetime.strptime(last, "%Y-%m-%d")
                    # 获取当前日期和时间
                    today = dt.now().date()
                    late = False
                    if second_time < today and self.tomorrow:
                        late = True
                    else:
                        try:
                            self.word_next_dict[str(second_time)] = self.word_next_dict[str(second_time)] + 1
                        except:
                            self.word_next_dict[str(second_time)] = 1
                    if late:
                        print(word + "  late")
                        d_day = [1,2]
                        n = random.sample(d_day, len(d_day))[0]
                        next_str = (date.today() + timedelta(days=n)).strftime('%Y-%m-%d')
                        data = {
                            "parent": {"type": "database_id", "database_id": self.database_id},
                            'properties': {
                                "Next": {"date": {"start": next_str}},
                                # "Level": {"select": {"name": level, "color": colors[int(level)]}},
                                # "Today": {"checkbox": False},
                                # "words": {"title": [{"type": "text", "text": {"content": origin}}]},
                                # "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                                # "voice": {"url": url_voice},
                                # "Date Wrong": {"date": {"start": "2023-11-21"}},
                                # '移動方式': {'rich_text': [{"text": {"content": move}}]},
                            }
                        }
                        # r = requests.patch(
                        #     "https://api.notion.com/v1/pages/{}".format(page_id),
                        #     json=data,
                        #     headers=headers,
                        # )
                        self.patch_one_data(data, page_id)
                        try:
                            self.word_next_dict[next_str] = self.word_next_dict[next_str] + 1
                        except:
                            self.word_next_dict[next_str] = 1

                else:
                    try:
                        level = dict['properties']["Level"]['select']['name']
                        next = self.next_day_on_level(level)
                    except:
                        next = "0"
                    data = {
                        "parent": {"type": "database_id", "database_id": self.database_id},
                        'properties': {
                            "Next": {"date": {"start": next}},
                            # "Level": {"select": {"name": level, "color": colors[int(level)]}},
                            # "Today": {"checkbox": False},
                            # "words": {"title": [{"type": "text", "text": {"content": origin}}]},
                            # "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                            # "voice": {"url": url_voice},
                            # "Date Wrong": {"date": {"start": "2023-11-21"}},
                            # '移動方式': {'rich_text': [{"text": {"content": move}}]},
                        }
                    }

                    self.patch_one_data(data, page_id)
                pass
        print(count)

        self.draw_pic()
        self.today_delete_before()
        # 判断是否需要分配压力
        categories_next = list(self.word_next_dict.keys())
        values_next = list(self.word_next_dict.values())
        need_to_release = False
        tension_date = []
        for num in range(len(values_next)):
            if values_next[num] > 300:
                tension_date.append(categories_next[num])
                print("日期：" + categories_next[num] + " , 这天需要背的单词为 "
                      + str(values_next[num]) + " 个，超过300个")
                need_to_release = True
        want_to_release = ""
        # if need_to_release:
        #     want_to_release = input("出现压力过大的日期，是否要分配压力，是打 1 ，不是可以直接 enter")
        # if want_to_release == "1":
        #     self.release_the_tension(tension_date)

    def draw_pic(self):
        # # 显示图形
        # plt.show()
        # plt.figure()
        # plt.figure(figsize=(6, 6))  # 调整图的大小
        categories = list(self.word_level_dict.keys())
        values = list(self.word_level_dict.values())

        # 对标签进行排序并获取排序后的索引
        sorted_indices = sorted(range(len(categories)), key=lambda k: categories[k])
        categories_level = [categories[i] for i in sorted_indices]
        values_level = [values[i] for i in sorted_indices]

        self.word_next_dict = OrderedDict(
            sorted(self.word_next_dict.items(), key=lambda x: dt.strptime(x[0], '%Y-%m-%d')))
        categories_next = list(self.word_next_dict.keys())
        values_next = list(self.word_next_dict.values())

        colors = ['red', 'green', 'blue', 'purple', 'orange']

        # plt.figure(figsize=(6, 6))  # 调整图的大小

        # 开始绘图
        fig, axs = plt.subplots(2, 2, figsize=(10, 6))
        bars1 = axs[0, 0].bar(range(len(categories_level)), values_level, color=colors)
        axs[0, 0].set_title('Level Bar Chart')
        axs[0, 0].set_label('Levels')
        axs[0, 0].set_ylabel('Word Amount')
        axs[0, 0].set_xticks(range(len(categories_level)), categories_level, ha='right')
        axs[0, 0].grid(True, axis='y', linestyle='--', alpha=0.7)

        for bar in bars1:
            axs[0, 0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, str(int(bar.get_height())),
                           ha='center',
                           va='bottom',fontsize=6)

        # 创建下方的子图
        bars2 = axs[1, 0].bar(range(len(categories_next)), values_next, color=colors, alpha=0.7)
        axs[1, 0].set_title('Next Day Chart')
        axs[1, 0].set_xlabel('Next Day')
        axs[1, 0].set_ylabel('Word Amount')
        axs[1, 0].set_xticks(range(len(categories_next)), categories_next, rotation=45, ha='right')
        axs[1, 0].tick_params(axis='x', labelsize=8)  # 设置x轴刻度标签的字体大小为8
        axs[1, 0].grid(True, axis='y', linestyle='--', alpha=0.7)

        for bar in bars2:
            axs[1, 0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1, str(int(bar.get_height())),
                           ha='center',
                           va='bottom',fontsize=6)

        my_dpi = 96
        # plt.figure(figsize=(480/my_dpi,480/my_dpi), dpi=my_dpi)
        if self.count_forget_all == 0 and self.count_know_some == 0 and self.count_forget_all == 0:
            axs[0, 1].axis('off')
        else:
            axs[0, 1].pie(x=[self.count_know_all, self.count_know_some, self.count_forget_all],
                          labels=['know all', 'know some', 'forget all'],
                          autopct='%.2f%%')
            # plt.legend(patches, [f"{label}: {size}" for label, size in zip(labels, sizes)], loc="upper left")
            title = "Know All: {}    Know Some:{}    Forget All:{}".format(self.count_know_all, self.count_know_some,
                                                                           self.count_forget_all)
            axs[0, 1].set_title(title)

        today_word_level_dict = {"KnowAll":0,"KnowSome":0,"ForgetAll":0}
        with open("TxtDataFiles/word_today.txt","r",encoding="utf-8") as file:
            today_word_levels = file.readlines()
        for today_word_level in today_word_levels:
            word_level = today_word_level.strip('\n')
            word_level = word_level.split('|')
            level = word_level[1]
            # try:
            #     today_word_level_dict[level] += 1
            # except:
            #     today_word_level_dict[level] = 0
            today_word_level_dict[level] += 1
        try:
            length = len(today_word_level_dict.keys())
        except:
            axs[1, 1].axis('off')
        if len(today_word_level_dict.keys()) ==0:
            axs[1, 1].axis('off')
        else:
            axs[1, 1].pie(x=[today_word_level_dict["KnowAll"], today_word_level_dict["KnowSome"],
                             today_word_level_dict["ForgetAll"]],
                          labels=['know all', 'know some', 'forget all'],
                          autopct='%.2f%%')
            # plt.legend(patches, [f"{label}: {size}" for label, size in zip(labels, sizes)], loc="upper left")
            title = "Today all:  Know All: {}    Know Some:{}    Forget All:{}".format(today_word_level_dict["KnowAll"], today_word_level_dict["KnowSome"],
                                                                           today_word_level_dict["ForgetAll"])
            axs[1, 1].set_title(title)

        plt.tight_layout(pad=2.0)  # 增加子图间的纵向距离
        today_str = date.today().strftime('%Y-%m-%d')
        file_path = "StatisticsPics/"+ today_str + ".png"
        plt.savefig(file_path)
        plt.show(block=True)



    def checked_move_to_today(self, body, selection):
        # #清空后post今天看到的单词
        # for selection in self.today.keys():
        #     checked_list = self.today[selection]
        #     for body in checked_list:
        word_content = body["properties"]['words']['title'][0]['plain_text']
        print("正在导入 " + word_content+ " 到today单词库中")
        body["parent"]["database_id"] = self.today_database_id
        word_tag = body["properties"]['Tags']['select']['name']
        word_color = body["properties"]['Tags']['select']['color']
        title = body["properties"]['passage']['multi_select'][0]['name']
        pronoun = body["properties"]['phonetic symbol']['rich_text'][0]['text']['content']
        meaning = body["properties"]['meaning']['rich_text'][0]['text']['content']
        today_str = date.today().strftime('%Y-%m-%d')
        # next_str = body["properties"]['Next']['date']['start']
        voice_url = body["properties"]['voice']['url']
        passage_id = body["properties"]['🌏 Economist Reading']['relation'][0]['id']
        # today_str = body["properties"]['words']['title'][0]['plain_text']

        p = {
            "parent": {"database_id": self.today_query_id},
            # "properties":body["properties"]
             "properties": {
                 "Tags": {"select": {"name": word_tag, "color": word_color}},
                 "words": {"title": [{"type": "text", "text": {"content": word_content}}]},
                 "passage": {"multi_select": [{"name": title}]},
                 "phonetic symbol": {"rich_text": [{"type": "text", "text": {"content": pronoun}}]},
                 "meaning": {
                     "rich_text": [{"type": "text", "text": {"content": meaning}}]},
                 "Checked Date": {"date": {"start": today_str}},
                 # "Next": {"date": {"start": next_str}},
                 "voice": {"url": voice_url},
                 "Level": {"select": {"name": "0", "color": "default"}},
                 # "KnowAll": {"checkbox": False},
                 # "KnowSome": {"checkbox": False},
                 # "ForgetAll": {"checkbox": False},
                 # "Checked Times": {"number": 0},
                 "🌏 Economist Reading": {
                     "relation": [
                         {
                             "id": passage_id
                         }
                     ]
                 },
                 "Selection":{
                     "select":{"name":selection,"color":self.selection_dict[selection]}
                 }
             },
         }

        url = "https://api.notion.com/v1/pages"
        headers = {
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json",
            "Authorization": "Bearer " + self.token
        }
        r = requests.post(url, json=p, headers=self.headers)
        print(r.text)
        print("导入" + word_content + " 到today，完成")

    def run_upload_with_timeout(self,dict,word_selection):
        while True:
            upload_process = multiprocessing.Process(target=self.checked_move_to_today(dict,word_selection))
            upload_process.start()
            upload_process.join(timeout=15)  # 主进程等待上传进程最多10秒

            if not upload_process.is_alive():
                break  # 如果上传进程已完成，退出循环
            else:
                print("函数执行时间超过10秒，停止当前进程并重新执行程序")
                os.kill(upload_process.pid, signal.SIGTERM)  # 终止上传进程

    def today_delete_before(self):
        response = self.DataBase_item_query(self.today_query_id)
        # 判断是否有之前的内容，如果有就清空
        # just_add = False
        if len(response) == 0:
            pass
        else:
            if self.tomorrow:
                print("晚于凌晨4点，清空前日单词")
                for dict in response:
                    checked_date = dt.strptime(dict['properties']["Checked Date"]['date']['start'], '%Y-%m-%d')
                    today = date.today()
                    checked_date = checked_date.date()
                    if checked_date != today:
                        self.delete_page(dict["id"])
            else:
                print("早于凌晨4点，不清空前日单词")

    def release_the_tension(self,tension_date):
        print("先不做了，如果之后背单词真背不下去再写")
        # for date in tension_date:
        #     this_day_response = self.date_dict[date]
        #     print(len(this_day_response))
        #     count = -1
        #     for dict in this_day_response:
        #         count += 1
        #         word_content = dict["properties"]['words']['title'][0]['plain_text']
        #         print(word_content)
        #         print(count,count/len(this_day_response))
        #         level = dict["properties"]['Level']['select']["name"]







if __name__ == "__main__":
    # print(next_day_on_level("8"))

    # print
    # https://www.notion.so/56b03c71d936493ab95a789cee835112?v=08662e1ef850458bb90b333d1f56fa60&pvs=4
    # https://www.notion.so/35907aea3e044dc29996ff4b070b6836?v=d041ee4b1708414a90bbd4f508c8026d&pvs=4
    a = Update_anki()
    response = a.DataBase_item_query("35907aea3e044dc29996ff4b070b6836")
    a.DataBase_item_delete(response)

    # response = None
    print("start updating")
    # a.patch_update()



