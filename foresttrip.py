#!/usr/bin/python
#-*- coding:utf-8 -*-
import os
import datetime
import time
from xml.etree.ElementTree import parse
from datetime import datetime, timedelta
from urllib import parse
from bs4 import BeautifulSoup

# 
# 자연휴양림 자리 찾기
# rudolph
# mofette@naver.com
# 20230309 - 리눅스 클론 서비스 돌리던걸 github  업로드

# csrf 세션 정보 얻기
def getSession():

    curl = "curl -D /home/rudolph/Python/camping/foresttrip_jsession.txt 'https://www.foresttrip.go.kr/main.do?hmpgId=FRIP' -s -o /home/rudolph/Python/camping/foresttrip_csrf.txt"
    os.system(curl)
    time.sleep(1)
    
    f = open('/home/rudolph/Python/camping/foresttrip_jsession.txt', 'r', encoding='utf-8')
    jsession = f.read()
    f.close()

    f = open('/home/rudolph/Python/camping/foresttrip_csrf.txt', 'r', encoding='utf-8')
    _csrfdata = f.read()
    f.close()
    
    soup = BeautifulSoup(_csrfdata, 'html.parser');
    _csrf = soup.find('input', {'name':'_csrf'}).get('value')

    findsession = ""
    for i in jsession.split('\n'):        
        if(len(i) > 23 and i[0:23] == 'Set-Cookie: JSESSIONID='):
            findsession = (i.split('=')[1].replace("; path", ""))

    return [findsession, _csrf]
    

# 자연휴양림 html 페이지 파싱
def getHtml(startDate, endDate, _csrf, jsession):
    stDate = startDate.replace('-', '')
    edDate = endDate.replace('-', '')
    #22/05/14(토)+-+22/05/15(일)
    tmp = startDate.replace('-', '/')[2:] + '(토)' + '+-+' + endDate.replace('-', '/')[2:] + '(일)'
    queryString = {'test': tmp}
    paramDate = parse.urlencode(queryString, encoding='utf-8', safe='+-+').split('=')[1]

    #csrf = 'f1810f67-346f-43ea-b1e2-cc4bea13b103'
    #jsessionid = 'U4CPf7MS_Un_evCSLczOsRrJIuI0aqEYuzCh5PQ5.node22'
    csrf = _csrf
    jsessionid = jsession

    curl = "curl 'https://www.foresttrip.go.kr/rep/or/innerFcfsRcrfrDtlDetls.do'"
    curl += " -H 'Accept: text/html, */*; q=0.01'"
    curl += " -H 'Accept-Language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'"
    curl += " -H 'Cache-Control: no-cache'"
    curl += " -H 'Connection: keep-alive'"
    curl += " -H 'Content-Type: application/json; charset=UTF-8'"
    curl += " -H 'Cookie: SCOUTER=x3t7t5r271rm29; PCID=16545823983566241345822; JSESSIONID=" + jsessionid + "; _gid=GA1.3.1686304193.1655773083; _gat_gtag_UA_210230422_1=1; enterPopup4715=close; enterPopup4714=close; _ga_E22WFNBEF7=GS1.1.1655773082.5.1.1655773102.40; _ga=GA1.3.1976978157.1654582398; NetFunnel_ID='"
    curl += " -H 'Host: www.foresttrip.go.kr'"
    curl += " -H 'Origin: https://www.foresttrip.go.kr'"
    curl += " -H 'Referer: https://www.foresttrip.go.kr/rep/or/fcfsRsrvtRcrfrDtlDetls.do?_csrf=" + csrf + "&srchInsttArcd=1&srchInsttId=&srchRsrvtBgDt={0}&srchRsrvtEdDt={1}&srchStngNofpr=2&srchSthngCnt=1&srchWord=&srchUseDt=22%2F05%2F14%28%ED%86%A0%29+-+22%2F05%2F15%28%EC%9D%BC%29&houseCampSctin=01&rsrvtPssblYn=N&srchHouseCharg=&srchCampCharg=&goodsClsscHouseCdArr=&goodsClsscCampCdArr=&srchInsttTpcd=&srchMyLtd=&srchMyLng=&srchDstnc=&hmpgId=FRIP&keyword=&calPicker={2}'"
    curl += " -H 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36'"
    curl += " -H 'Sec-Fetch-Dest: empty'"
    curl += " -H 'Sec-Fetch-Mode: cors'"
    curl += " -H 'Sec-Fetch-Site: same-origin'"
    curl += " -H 'User-Agent: Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.64 Mobile Safari/537.36'"
    curl += " -H 'X-Ajax-call: true'"
    curl += " -H 'X-CSRF-TOKEN: " + csrf + "'"
    curl += " -H 'X-Requested-With: XMLHttpRequest'"
    curl += " -H 'sec-ch-ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"101\", \"Google Chrome\";v=\"101\"'"
    curl += " -H 'sec-ch-ua-mobile: ?1'"
    curl += " -H 'sec-ch-ua-platform: \"Android\"'"
    curl += " --data-raw '{\"srchInsttArcd\":\"1\",\"srchInsttId\":\"\",\"srchRsrvtBgDt\":\"{0}\",\"srchRsrvtEdDt\":\"{1}\",\"srchStngNofpr\":\"2\",\"srchSthngCnt\":\"1\",\"houseCampSctin\":\"02\",\"rsrvtPssblYn\":\"N\",\"srchHouseCharg\":\"\",\"srchHouseOver\":\"\",\"srchCampCharg\":\"\",\"srchCampOver\":\"\",\"srchMyLtd\":\"\",\"srchMyLng\":\"\",\"srchDstnc\":\"\",\"srchDstncOver\":\"\",\"srtngOrdr\":\"rsrvtPssbl\",\"goodsClsscHouseCdArr\":[],\"goodsClsscCampCdArr\":[],\"srchInsttTpcd\":[],\"cmdogYn\":\"N\",\"bbqYn\":\"N\",\"dsprsYn\":\"N\",\"otsdWeterYn\":\"N\",\"wifiYn\":\"N\",\"snowPlaceYn\":\"N\"}'"
    curl += " -s -o /home/rudolph/Python/camping/foresttrip.html"

    curl = curl.replace('{0}', stDate)
    curl = curl.replace('{1}', edDate)
    curl = curl.replace('{2}', paramDate)

    os.system(curl)
    time.sleep(0.1)

    f = open('/home/rudolph/Python/camping/foresttrip.html', 'r', encoding='utf-8')
    data = f.read()
    f.close()
    
    #print(data)
    return data


#특정 정보 찾기
def parsingHtml(htmlData):
    
    soup = BeautifulSoup(htmlData, 'html.parser')    
    list = soup.select('#searchResultMap > div', attr={'class':'rc_item'})

    rtnData = []
    for item in list:
        rcti = item.select('div', attr={'class':'rc_ti'})
        if int(rcti[12].text.split(':')[1]) > 0:
            rtnData.append([rcti[0].find('b').text, rcti[12].text, rcti[9].find_all('a')[1].text])
    
    return rtnData

# 토요일만 구하기
def weekSaturday():
    startdate = datetime.now();
    enddate = datetime.now() + timedelta(days = 60);

    rtnDate = []
    for i in range((enddate - startdate).days):    
        curdate = startdate + timedelta(days = i+1)
        week = ['월', '화', '수', '목', '금', '토', '일']
        if(week[curdate.weekday()] == '토'):
            #print(curdate.strftime('%Y-%m-%d'))
            rtnDate.append(curdate.strftime('%Y-%m-%d'))
    
    return rtnDate
    

# 일요일만 구하기
def weekSunday():
    startdate = datetime.now();
    enddate = datetime.now() + timedelta(days = 60);

    rtnDate = []
    for i in range((enddate - startdate).days):    
        curdate = startdate + timedelta(days = i+1)
        week = ['월', '화', '수', '목', '금', '토', '일']
        if(week[curdate.weekday()] == '일'):
            #print(curdate.strftime('%Y-%m-%d'))    
            rtnDate.append(curdate.strftime('%Y-%m-%d'))

    return rtnDate

#예약가능한 자연 휴양림 정보 슬랙으로 메시지 전송
def sendslack(msg):
    #your hook token
    hooktoken = ''

    cmd = 'curl -X POST --data-urlencode "payload={\'channel\': \'#python_slackbot\', \'username\': \'webhookbot\', \'text\': \'' + msg + '\', \'icon_emoji\': \':ghost:\'}" https://hooks.slack.com/services/' + hooktoken + ' -s'
    os.system(cmd)
    time.sleep(0.1)


#메인 시작
if __name__ == '__main__':

    print('START : ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') )

    startdate = weekSaturday()
    enddate   = weekSunday()

    result = getSession()
    findsession = result[0]
    _csrf = result[1]

    print(findsession, _csrf)
    
    if len(startdate) != len(enddate): #길이가 다르면 시작일자 마지막을 삭제
        startdate.remove(startdate[len(startdate) - 1])
  
    for st in startdate:
        print(st, enddate[startdate.index(st)])
        htmlData = getHtml(st, enddate[startdate.index(st)], _csrf, findsession)

        #csrf 토큰을 얻기 전에 오류.. 현재는 자동으로 얻어오기 때문에 따로 필요없으나 예외처리이므로 남겨둠
        if(htmlData == '{"result_code":"-1", "ErrorCode" : "-5", "ErrorMsg" : "로그인 세션이 만료되었거나 접근방식이 올바르지 않습니다."}'):
            print("휴양림 X-CSRF-TOKEN 업데이트 필요!")
            sendslack("휴양림 X-CSRF-TOKEN 업데이트 필요!")
            break
            
        rtnData = parsingHtml(htmlData)
        if len(rtnData) > 0:
            msg = ""
            for ft in rtnData:
                if ft[0] != '[사립](양평군)양평설매재자연휴양림':
                    print(ft[0], ft[1])
                    msg += '[' + st + '~' + enddate[startdate.index(st)] + ']' + ft[0] + ' ' + ft[1] + ' ' + 'https://www.foresttrip.go.kr/' + '\n'
                else:
                    continue

            if msg != "":
                sendslack(msg)



    print('END : ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
