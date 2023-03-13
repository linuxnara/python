#!/usr/bin/python
#-*- coding:utf-8 -*-

import os
import datetime
import time
from bs4 import BeautifulSoup
from PIL import Image
import glob
import shutil

#네이버 웹툰 페이지 로딩
def getPage(titleId, page):
    #769209
    curl = 'curl "https://comic.naver.com/webtoon/detail?titleId={0}&no={1}&weekday=wed" -s -k -o /home/rudolph/Python/naverwebtoon.html'
    curl = curl.replace('{0}', str(titleId))
    curl = curl.replace('{1}', str(page))

    os.system(curl)
    time.sleep(0.1)

    f = open('/home/rudolph/Python/naverwebtoon.html', 'r', encoding='utf-8')
    data = f.read()
    f.close()

    return data

#HTML 필요 내용 파싱
def parsingHtml(pageData):
    soup = BeautifulSoup(pageData, 'html.parser')

    title = soup.find(attrs={'property':'og:title'}).attrs['content']
    images = soup.select('div.view_area')[0].find_all(attrs={'alt':'comic content'})
    maintitle = soup.select('div.detail')[0].find_all(attrs={'class':'title'})[0].text

    return [title, images, maintitle]

# 이미지 다운로드
def imgDownload(title, page, images, basePath):

    createDirectory(basePath)

    for x in images:
        #print(x.src.text)
        #print(x.attrs['src'], x.attrs['id'])
        filename = x.attrs['src'].split('/')[len(x.attrs['src'].split('/')) -1]

        curl = "curl '" + x.attrs['src'] + "'"
        curl += " -H 'authority: image-comic.pstatic.net'"
        curl += " -H 'accept: image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'"
        curl += " -H 'accept-language: ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'"
        curl += " -H 'cache-control: no-cache'"
        curl += " -H 'pragma: no-cache'"
        curl += " -H 'referer: https://comic.naver.com/webtoon/detail?titleId=769209&no=1&weekday=wed'"
        curl += " -H 'sec-ch-ua: \" Not A;Brand\";v=\"99\", \"Chromium\";v=\"100\", \"Google Chrome\";v=\"100\"'"
        curl += " -H 'sec-ch-ua-mobile: ?0' "
        curl += " -H 'sec-ch-ua-platform: \"Windows\"' "
        curl += " -H 'sec-fetch-dest: image' "
        curl += " -H 'sec-fetch-mode: no-cors' "
        curl += " -H 'sec-fetch-site: cross-site' "
        curl += " -H 'user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36' "
        curl += ' --compressed -k -s -o ' + basePath + filename
        os.system(curl)
        time.sleep(0.1)


#목록 이미지 합치기
def combineImage(basePath, full_width,full_height,image_key,image_list,index):
    canvas = Image.new('RGB', (full_width, full_height), 'white')
    output_height = 0

    for im in image_list:
        width, height = im.size
        canvas.paste(im, (0, output_height))
        output_height += height

    canvas.save(basePath + image_key+'_merged_'+str(index)+'.jpg')

#디렉터리 이미지 목록
def listImage(basePath, downPath, image_key, image_value):
    full_width, full_height,index = 0, 0, 1
    image_list = []

    for i in image_value:
        im = Image.open(downPath + image_key+"_"+str(i)+".jpg")
        #print('Get '+image_key+"_"+str(i)+".jpg")
        width, height = im.size

    image_list = []

    for i in image_value:
        im = Image.open(downPath + image_key+"_"+str(i)+".jpg")
        #print('Get '+image_key+"_"+str(i)+".jpg")
        width, height = im.size

        if full_height+height > 65000:
            combineImage(basePath, full_width,full_height,image_key,image_list,index)
            index = index + 1
            image_list = []
            full_width, full_height = 0, 0

        image_list.append(im)
        full_width = max(full_width, width)
        full_height += height

    combineImage(basePath, full_width,full_height,image_key,image_list,index)

#이미지 합치기 메인
def concatimg(basePath, downPath):
    target_dir = downPath
    files = glob.glob(target_dir + "*.jpg")

    name_list = {}

    for f in files:
        name = f.split('/')[len(f.split('/')) - 1]
        key =  name.split('_')[0] + '_' + name.split('_')[1] + '_' + name.split('_')[2]
        value = name.split('_')[3].split('.')[0]

        if key in name_list.keys():
            name_list[key].append(int(value))
        else:
            name_list[key] = [int(value)]

        name_list[key].sort()

    for key,value in name_list.items():
        listImage(basePath, downPath, key,value)

#디렉토리 생성
def createDirectory(path):
    try:
        if not os.path.exists(path):
            os.makedirs(path)
    except OSError:
        print('디렉터리 생성 실패 : ' + path)


#텔레그램 전송
def sendtelegram(filePath):
    api_key = 'api_key'
    chat_id = 'chat_id'
    BASE_URL = 'https:///api.telegram.org/bot' + api_key + '/sendDocument'
    cmd = 'curl -k -F chat_id=' + chat_id + ' ' + ' -F document=@"' + filePath + '" ' + BASE_URL + ' -s'
    os.system(cmd)
    time.sleep(0.1)

#시작
if __name__ == '__main__':

    #769209
    titleId = input('title_id : ')

    #마지막 회차 조회
    totalPage = getPage(titleId, 1);
    soup = BeautifulSoup(totalPage, 'html.parser')
    total = soup.select('div.pg_area')[0].find(attrs={'class':'total'}).text
    maintitle = ''

    #다운로드 & 머지 & 압축 & 텔레그램 전송
    for i in range(1, int(total) + 1):
        page = i

        #기본경로
        homePath = '/home/rudolph/Python/naverwebtoon/'
        downPath = '/home/rudolph/Python/naverwebtoon/' + str(page) + '/files/'
        basePath = '/home/rudolph/Python/naverwebtoon/' + str(page) + "/"

        #HTML 페이지 내용 다운로드
        pageData = getPage(titleId, page);

        #HTML 페이지 파싱
        resultData = parsingHtml(pageData)
        print(resultData[0])
        maintitle = resultData[2]

        #이미지다운로드
        print('\t이미지 다운로드 중... ')
        imgDownload(resultData[0], page, resultData[1], downPath)
        print('\t이미지 다운로드 완료!')

        #이미지 합치기
        print('\t이미지 합치기')
        concatimg(basePath, downPath)
        print('\t이미지 합치기 완료!')

        #다운로드 디렉터리 삭제
        print('\t다운로드 디렉터리 삭제중... ')
        shutil.rmtree(downPath)
        print('\t다운로드 디렉터리 삭제 완료!')


        #압축
        #print('\t디렉터리 압축중... ')
        #print('zip -j "' + zipPath + resultData[0] + '.zip" ' + basePath + ' -r ')
        #os.system('zip -j "' + zipPath + resultData[0] + '.zip" ' + basePath + ' -r')
        #time.sleep(0.1)
        #print('\t디렉터리 압축 완료... ')

        #소스 디렉터리 삭제
        #print('\t다운로드 디렉터리 삭제중... ')
        #shutil.rmtree(basePath)
        #print('\t다운로드 디렉터리 삭제 완료!')

        #텔레그램 전송
        #sendtelegram(zipPath + resultData[0] + '.zip')

        #다운로드 받을 페이지 마지막 번호 지정
        if page == 5:
            break


    zipPath = '/home/rudolph/Python/naverwebtoon_zip/'
    targetPath = '/home/rudolph/Python/naverwebtoon/'

    createDirectory(zipPath)

    print('\t디렉터리 압축중...')
    os.system('zip -j "' + zipPath + maintitle + '.zip" ' + targetPath + ' -r')
    print('\t디렉터리 압축 완료!')

    #소스디렉터리 삭제
    shutil.rmtree(targetPath)

    print('텔레그램 전송')
    print(zipPath + maintitle + '.zip')
    sendtelegram(zipPath + maintitle + '.zip')
    print('텔레그램 전송완료')
