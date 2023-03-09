#!/usr/bin/python
# -*- coding: utf8 -*-

import os
import sys
import urllib2
import json
import time
#from bs4 import BeautifulSoup

# 
# 텀블러 동영상 크롤링(python 3.8)
# rudolph
# mofette@naver.com
# 20230309 - 리눅스 클론 서비스 돌리던걸 github  업로드
#

max_offset = 200

#html 내용 호출
def getJson(url):
    response = urllib2.urlopen(url)
    return response.read()

#포스트 읽기
def readPost(offset):
    #your api key
    api_key = ''
    
    srchName = "http://api.tumblr.com/v2/blog/" + sys.argv[1] + "/posts/video?offset=" + str(offset) + "&limit=50&api_key=" + api_key
    jdata = json.loads(getJson(srchName))  #json call
    return jdata["response"]["posts"]

#다운로드
def down(url):
    spData = url.split('/')
    fileNm = spData[len(spData) - 1]

    #check the file
    ret = os.path.isfile(sys.argv[1] + "/" + fileNm)
    if ret == True:
            return 0

    #check the directory
    ret = os.path.isdir(sys.argv[1])
    if ret == False:
            os.mkdir(sys.argv[1])

    #downloads
    os.system('curl ' + url + ' -# -o ./' + sys.argv[1] + '/' + fileNm)


def main():
    for offset in range(1, max_offset, 50):
        print(offset)
        retJsonData = readPost(offset)

        for post in range(0, len(retJsonData)):
                print(str(offset) + '/' + str(post))
                time.sleep(1)
                url = retJsonData[post]["video_url"]
                down(url)

    return 0

#main call                      
if __name__ == "__main__":
        sys.exit(main())
