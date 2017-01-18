#!/usr/bin/env python
#-*- coding:utf-8 -*-

import requests
from bs4 import BeautifulSoup
import urllib
import re
import random
from time import sleep
# module
from zhihu_auth import ZhihuAuth
from zhihu_auth import Logging

# Setting Logging
Logging.flag = True

class Zhihu:
    def __init__(self):
        self.auth = ZhihuAuth()
        self.requests = self.auth.get_requests()

    def login(self):
    	self.auth.login()
		if self.auth.islogin() != True:
		    Logging.error(u"你的身份信息已经失效，请重新生成身份信息( `python auth.py` )。")
		    raise Exception("无权限(403)")
    
    def get_requests(self):
    	return self.requests

    def get_auth(self):
    	return self.auth

class Collections:
	soup = None

	def __init__(self, url, requests, name=None, creator=None):
        self.zhihu = Zhihu()
        self.requests = requests

        if not re.compile(r"(http|https)://www.zhihu.com/collection/\d{8}").match(url):
            raise ValueError("\"" + url + "\"" + " : it isn't a collection url.")
        else:
            self.url = url
            # print 'collection url',url
            if name != None:
                self.name = name
            if creator != None:
                self.creator = creator

    soup = None
        
    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/"
        }
        r = requests.get(self.url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_name(self):
        if hasattr(self, 'name'):
            if platform.system() == 'Windows':
                return self.name.decode('utf-8').encode('gbk')
            else:
                return self.name
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            self.name = soup.find("h2", id="zh-fav-head-title").string.encode("utf-8").strip()
            if platform.system() == 'Windows':
                return self.name.decode('utf-8').encode('gbk')
            return self.name

    def get_creator(self):
        if hasattr(self, 'creator'):
            return self.creator
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            creator_id = soup.find("h2", class_="zm-list-content-title").a.string.encode("utf-8")
            creator_url = "http://www.zhihu.com" + soup.find("h2", class_="zm-list-content-title").a["href"]
            creator = User(creator_url, creator_id)
            self.creator = creator
            return creator

    def get_all_answers(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        answer_list = soup.find_all("div", class_="zm-item")
        if len(answer_list) == 0:
            print "the collection is empty."
            return
            yield
        else:
            question_url = None
            question_title = None
            for answer in answer_list:
                if not answer.find("p", class_="note"):
                    question_link = answer.find("h2")
                    if question_link != None:
                        question_url = "http://www.zhihu.com" + question_link.a["href"]
                        question_title = question_link.a.string.encode("utf-8")
                    question = Question(question_url, question_title)
                    answer_url = "http://www.zhihu.com" + answer.find("span", class_="answer-date-link-wrap").a["href"]
                    author = None

                    if answer.find("div", class_="zm-item-answer-author-info").get_text(strip='\n') == u"匿名用户":
                        author_url = None
                        author = User(author_url)
                    else:
                        author_tag = answer.find("div", class_="zm-item-answer-author-info").find_all("a")[0]
                        author_id = author_tag.string.encode("utf-8")
                        author_url = "http://www.zhihu.com" + author_tag["href"]
                        author = User(author_url, author_id)
                    yield Answer(answer_url, question, author)
            i = 2
            while True:
                headers = {
                    'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
                    'Host': "www.zhihu.com",
                    'Origin': "http://www.zhihu.com",
                    'Pragma': "no-cache",
                    'Referer': "http://www.zhihu.com/"
                }
                r = requests.get(self.url + "?page=" + str(i), headers=headers, verify=False)
                answer_soup = BeautifulSoup(r.content, "lxml")
                answer_list = answer_soup.find_all("div", class_="zm-item")
                if len(answer_list) == 0:
                    break
                else:
                    for answer in answer_list:
                        if not answer.find("p", class_="note"):
                            question_link = answer.find("h2")
                            if question_link != None:
                                question_url = "http://www.zhihu.com" + question_link.a["href"]
                                question_title = question_link.a.string.encode("utf-8")
                            question = Question(question_url, question_title)
                            answer_url = "http://www.zhihu.com" + answer.find("span", class_="answer-date-link-wrap").a[
                                "href"]
                            author = None
                            if answer.find("div", class_="zm-item-answer-author-info").get_text(strip='\n') == u"匿名用户":
                                # author_id = "匿名用户"
                                author_url = None
                                author = User(author_url)
                            else:
                                author_tag = answer.find("div", class_="zm-item-answer-author-info").find_all("a")[0]
                                author_id = author_tag.string.encode("utf-8")
                                author_url = "http://www.zhihu.com" + author_tag["href"]
                                author = User(author_url, author_id)
                            yield Answer(answer_url, question, author)
                i = i + 1

    def get_top_i_answers(self, n):
        j = 0
        answers = self.get_all_answers()
        for answer in answers:
            j = j + 1
            if j > n:
                break
            yield answer

class Answer:
    soup = None

    def __init__(self, answer_url, requests, question=None, author=None, upvote=None, content=None):

        self.answer_url = answer_url
        self.requests = requests

        if question != None:
            self.question = question
        if author != None:
            self.author = author
        if upvote != None:
            self.upvote = upvote
        if content != None:
            self.content = content

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/"
        }
        r = requests.get(self.answer_url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_question(self):
        if hasattr(self, "question"):
            return self.question
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            question_link = soup.find("h2", class_="zm-item-title zm-editable-content").a
            url = "http://www.zhihu.com" + question_link["href"]
            title = question_link.string.encode("utf-8")
            question = Question(url, title)
            return question

    def get_author(self):
        if hasattr(self, "author"):
            return self.author
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            if soup.find("div", class_="zm-item-answer-author-info").get_text(strip='\n') == u"匿名用户":
                author_url = None
                author = User(author_url)
            else:
                author_tag = soup.find("div", class_="zm-item-answer-author-info").find_all("a")[1]
                author_id = author_tag.string.encode("utf-8")
                author_url = "http://www.zhihu.com" + author_tag["href"]
                author = User(author_url, author_id)
            return author

    def get_upvote(self):
        if hasattr(self, "upvote"):
            return self.upvote
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            count = soup.find("span", class_="count").string
            if count[-1] == "K":
                upvote = int(count[0:(len(count) - 1)]) * 1000
            elif count[-1] == "W":
                upvote = int(count[0:(len(count) - 1)]) * 10000
            else:
                upvote = int(count)
            return upvote

    def get_content(self):
        if hasattr(self, "content"):
            return self.content
        else:
            if self.soup == None:
                self.parser()
            soup = BeautifulSoup(self.soup.encode("utf-8"), "lxml")
            answer = soup.find("div", class_="zm-editable-content clearfix")
            soup.body.extract()
            soup.head.insert_after(soup.new_tag("body", **{'class': 'zhi'}))
            soup.body.append(answer)
            img_list = soup.find_all("img", class_="content_image lazy")
            for img in img_list:
                img["src"] = img["data-actualsrc"]
            img_list = soup.find_all("img", class_="origin_image zh-lightbox-thumb lazy")
            for img in img_list:
                img["src"] = img["data-actualsrc"]
            noscript_list = soup.find_all("noscript")
            for noscript in noscript_list:
                noscript.extract()
            content = soup
            self.content = content
            return content

    def to_txt(self):

        content = self.get_content()
        body = content.find("body")
        br_list = body.find_all("br")
        for br in br_list:
            br.insert_after(content.new_string("\n"))
        li_list = body.find_all("li")
        for li in li_list:
            li.insert_before(content.new_string("\n"))

        if platform.system() == 'Windows':
            anon_user_id = "匿名用户".decode('utf-8').encode('gbk')
        else:
            anon_user_id = "匿名用户"
        if self.get_author().get_user_id() == anon_user_id:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "text"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "text")))
            if platform.system() == 'Windows':
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt".decode(
                    'utf-8').encode('gbk')
            else:
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt"
            print file_name
            # if platform.system() == 'Windows':
            # file_name = file_name.decode('utf-8').encode('gbk')
            # print file_name
            # else:
            # print file_name
            file_name = file_name.replace("/", "'SLASH'")
            if os.path.exists(os.path.join(os.path.join(os.getcwd(), "text"), file_name)):
                f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "a")
                f.write("\n\n")
            else:
                f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "a")
                f.write(self.get_question().get_title() + "\n\n")
        else:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "text"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "text")))
            if platform.system() == 'Windows':
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt".decode(
                    'utf-8').encode('gbk')
            else:
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.txt"
            print file_name
            # if platform.system() == 'Windows':
            # file_name = file_name.decode('utf-8').encode('gbk')
            # print file_name
            # else:
            # print file_name
            file_name = file_name.replace("/", "'SLASH'")
            f = open(os.path.join(os.path.join(os.getcwd(), "text"), file_name), "wt")
            f.write(self.get_question().get_title() + "\n\n")
        if platform.system() == 'Windows':
            f.write("作者: ".decode('utf-8').encode('gbk') + self.get_author().get_user_id() + "  赞同: ".decode(
                'utf-8').encode('gbk') + str(self.get_upvote()) + "\n\n")
            f.write(body.get_text().encode("gbk"))
            link_str = "原链接: ".decode('utf-8').encode('gbk')
            f.write("\n" + link_str + self.answer_url.decode('utf-8').encode('gbk'))
        else:
            f.write("作者: " + self.get_author().get_user_id() + "  赞同: " + str(self.get_upvote()) + "\n\n")
            f.write(body.get_text().encode("utf-8"))
            f.write("\n" + "原链接: " + self.answer_url)
        f.close()

    # def to_html(self):
    # content = self.get_content()
    # if self.get_author().get_user_id() == "匿名用户":
    # file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.html"
    # f = open(file_name, "wt")
    # print file_name
    # else:
    # file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.html"
    # f = open(file_name, "wt")
    # print file_name
    # f.write(str(content))
    # f.close()

    def to_md(self):
        content = self.get_content()
        if platform.system() == 'Windows':
            anon_user_id = "匿名用户".decode('utf-8').encode('gbk')
        else:
            anon_user_id = "匿名用户"
        if self.get_author().get_user_id() == anon_user_id:
            if platform.system() == 'Windows':
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md".decode(
                    'utf-8').encode('gbk')
            else:
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md"
            print file_name
            # if platform.system() == 'Windows':
            # file_name = file_name.decode('utf-8').encode('gbk')
            # print file_name
            # else:
            # print file_name
            file_name = file_name.replace("/", "'SLASH'")
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "markdown"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "markdown")))
            if os.path.exists(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name)):
                f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "a")
                f.write("\n")
            else:
                f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "a")
                f.write("# " + self.get_question().get_title() + "\n")
        else:
            if not os.path.isdir(os.path.join(os.path.join(os.getcwd(), "markdown"))):
                os.makedirs(os.path.join(os.path.join(os.getcwd(), "markdown")))
            if platform.system() == 'Windows':
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md".decode(
                    'utf-8').encode('gbk')
            else:
                file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md"
            print file_name
            # file_name = self.get_question().get_title() + "--" + self.get_author().get_user_id() + "的回答.md"
            # if platform.system() == 'Windows':
            # file_name = file_name.decode('utf-8').encode('gbk')
            # print file_name
            # else:
            # print file_name
            file_name = file_name.replace("/", "'SLASH'")
            f = open(os.path.join(os.path.join(os.getcwd(), "markdown"), file_name), "wt")
            f.write("# " + self.get_question().get_title() + "\n")
        if platform.system() == 'Windows':
            f.write("### 作者: ".decode('utf-8').encode('gbk') + self.get_author().get_user_id() + "  赞同: ".decode(
                'utf-8').encode('gbk') + str(self.get_upvote()) + "\n")
        else:
            f.write("### 作者: " + self.get_author().get_user_id() + "  赞同: " + str(self.get_upvote()) + "\n")
        text = html2text.html2text(content.decode('utf-8')).encode("utf-8")

        r = re.findall(r'\*\*(.*?)\*\*', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'_(.*)_', text)
        for i in r:
            if i != " ":
                text = text.replace(i, i.strip())

        r = re.findall(r'!\[\]\((?:.*?)\)', text)
        for i in r:
            text = text.replace(i, i + "\n\n")

        if platform.system() == 'Windows':
            f.write(text.decode('utf-8').encode('gbk'))
            link_str = "\n---\n#### 原链接: ".decode('utf-8').encode('gbk')
            f.write(link_str + self.answer_url.decode('utf-8').encode('gbk'))
        else:
            f.write(text)
            f.write("\n---\n#### 原链接: " + self.answer_url)
        f.close()

    def get_visit_times(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        for tag_p in soup.find_all("p"):
            if "所属问题被浏览" in tag_p.contents[0].encode('utf-8'):
                return int(tag_p.contents[1].contents[0])

    def get_voters(self):
        if self.soup == None:
            self.parser()
        soup = self.soup
        data_aid = soup.find("div", class_="zm-item-answer  zm-item-expanded")["data-aid"]
        request_url = 'http://www.zhihu.com/node/AnswerFullVoteInfoV2'
        # if session == None:
        #     create_session()
        # s = session
        # r = s.get(request_url, params={"params": "{\"answer_id\":\"%d\"}" % int(data_aid)})
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/"
        }
        r = requests.get(request_url, params={"params": "{\"answer_id\":\"%d\"}" % int(data_aid)}, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        voters_info = soup.find_all("span")[1:-1]
        if len(voters_info) == 0:
            return
            yield
        else:
            for voter_info in voters_info:
                if voter_info.string == u"匿名用户、" or voter_info.string == u"匿名用户":
                    voter_url = None
                    yield User(voter_url)
                else:
                    voter_url = "http://www.zhihu.com" + str(voter_info.a["href"])
                    voter_id = voter_info.a["title"].encode("utf-8")
                    yield User(voter_url, voter_id)


class User:
    user_url = None
    # session = None
    soup = None

    def __init__(self, user_url, user_id=None):
        if user_url == None:
            self.user_id = "匿名用户"
        elif user_url.startswith('www.zhihu.com/people', user_url.index('//') + 2) == False:
            raise ValueError("\"" + user_url + "\"" + " : it isn't a user url.")
        else:
            self.user_url = user_url
            if user_id != None:
                self.user_id = user_id

    def parser(self):
        headers = {
            'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
            'Host': "www.zhihu.com",
            'Origin': "http://www.zhihu.com",
            'Pragma': "no-cache",
            'Referer': "http://www.zhihu.com/"
        }
        r = requests.get(self.user_url, headers=headers, verify=False)
        soup = BeautifulSoup(r.content, "lxml")
        self.soup = soup

    def get_user_id(self):
        if self.user_url == None:
            # print "I'm anonymous user."
            if platform.system() == 'Windows':
                return "匿名用户".decode('utf-8').encode('gbk')
            else:
                return "匿名用户"
        else:
            if hasattr(self, "user_id"):
                if platform.system() == 'Windows':
                    return self.user_id.decode('utf-8').encode('gbk')
                else:
                    return self.user_id
            else:
                if self.soup == None:
                    self.parser()
                soup = self.soup
                user_id = soup.find("div", class_="title-section ellipsis") \
                    .find("span", class_="name").string.encode("utf-8")
                self.user_id = user_id
                if platform.system() == 'Windows':
                    return user_id.decode('utf-8').encode('gbk')
                else:
                    return user_id

    def get_head_img_url(self, scale=4):
        """
            By liuwons (https://github.com/liuwons)
            增加获取知乎识用户的头像url
            scale对应的头像尺寸:
                1 - 25×25
                3 - 75×75
                4 - 100×100
                6 - 150×150
                10 - 250×250
        """
        scale_list = [1, 3, 4, 6, 10]
        scale_name = '0s0ml0t000b'
        if self.user_url == None:
            print "I'm anonymous user."
            return None
        else:
            if scale not in scale_list:
                print 'Illegal scale.'
                return None
            if self.soup == None:
                self.parser()
            soup = self.soup
            url = soup.find("img", class_="Avatar Avatar--l")["src"]
            return url[:-5] + scale_name[scale] + url[-4:]

    def get_data_id(self):
        """
            By yannisxu (https://github.com/yannisxu)
            增加获取知乎 data-id 的方法来确定标识用户的唯一性 #24
            (https://github.com/egrcc/zhihu-python/pull/24)
        """
        if self.user_url == None:
            print "I'm anonymous user."
            return 0
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            data_id = soup.find("button", class_="zg-btn zg-btn-follow zm-rich-follow-btn")['data-id']
            return data_id

    def get_gender(self):
        """
            By Mukosame (https://github.com/mukosame)
            增加获取知乎识用户的性别
        """
        if self.user_url == None:
            print "I'm anonymous user."
            return 'unknown'
        else:
            if self.soup == None:
                self.parser()
            soup = self.soup
            try:
                gender = str(soup.find("span",class_="item gender").i)
                if (gender == '<i class="icon icon-profile-female"></i>'):
                    return 'female'
                else:
                    return 'male'
            except:
                return 'unknown'
	def get_collections(self):
        if self.user_url == None:
            print "I'm anonymous user."
            return
            yield
        else:
            collections_num = self.get_collections_num()
            if collections_num == 0:
                return
                yield
            else:
                for i in xrange((collections_num - 1) / 20 + 1):
                    collection_url = self.user_url + "/collections?page=" + str(i + 1)
                    headers = {
                        'User-Agent': "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/42.0.2311.135 Safari/537.36",
                        'Host': "www.zhihu.com",
                        'Origin': "http://www.zhihu.com",
                        'Pragma': "no-cache",
                        'Referer': "http://www.zhihu.com/"
                    }
                    r = requests.get(collection_url, headers=headers, verify=False)

                    soup = BeautifulSoup(r.content, "lxml")
                    for collection in soup.find_all("div", class_="zm-profile-section-item zg-clear"):
                        url = "http://www.zhihu.com" + \
                              collection.find("a", class_="zm-profile-fav-item-title")["href"]
                        name = collection.find("a", class_="zm-profile-fav-item-title").string.encode("utf-8")
                        yield Collection(url, name, self)


def main():
    zhihu=Zhihu()
    zhihu.login()

if __name__=='__main__':
    main()
