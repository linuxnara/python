#-*- coding:utf-8 -*-
import os
import glob
import xml.etree.ElementTree as ET
from datetime import datetime
from collections import defaultdict
import re

# Jenkins job 폴더 경로
jenkins_job_path = '/jenkins_project/builds'

# 결과를 저장할 HTML 파일 경로
output_html_path = '/home/jenkins/jenkins_changelog.html'

# changelog 데이터 저장
changelogs_by_date = defaultdict(list)

#changelog.xml 파싱
def parseLogContents(log_data):
    # Split log data by commits
    commits = log_data.strip().split("commit ")[1:]

    commit_data = []

    for commit in commits:
        # Extract commit hash
        commit_hash = commit.split("\n")[0].strip()
        
        # Extract committer info
        committer_match = re.search(r"committer (.*?) <(.*?)>", commit)
        if committer_match:
            committer_id = committer_match.group(1)
            committer_email = committer_match.group(2)
        
        # Extract commit message
        message_match = re.search(r"\n\n\s*(.*?)\n\n", commit, re.DOTALL)
        if message_match:
            commit_message = message_match.group(1).strip()
        else:
            commit_message = ''
        
        # Extract file changes
        file_changes = re.findall(r"\n:.*?\s+([A-Z])\s+(.*?)$", commit, re.MULTILINE)
        files = [file for status, file in file_changes]

        # Append extracted data to list
        commit_data.append({
            'commit_hash': commit_hash,
            'committer_id': committer_id,
            'committer_email': committer_email,
            'commit_message': commit_message,
            'files': files
        })

    # # Print the parsed commit data
    # for data in commit_data:
    #     print(f"Commit Hash: {data['commit_hash']}")
    #     print(f"Committer ID: {data['committer_id']}")
    #     print(f"Committer Email: {data['committer_email']}")
    #     print(f"Commit Message: {data['commit_message']}")
    #     print(f"Files: {data['files']}")
    #     print("\n")

    return commit_data

# 폴더를 순회하며 changelog.xml과 log 파일을 읽기
for root, dirs, files in os.walk(jenkins_job_path):
    if 'changelog.xml' in files:
        changelog_path = os.path.join(root, 'changelog.xml')
        log_path = os.path.join(root, 'log')

        # changelog.xml 파일의 생성일 확인
        changelog_creation_time = datetime.fromtimestamp(os.path.getctime(changelog_path))
        changelog_date = changelog_creation_time.strftime('%Y/%m/%d %H:%M:%S')

        # changelog.xml 파일 내용 읽기
        #tree = ET.parse(changelog_path)
        #root_elem = tree.getroot()
        #changelog_content = ET.tostring(root_elem, encoding='unicode')
        if os.path.exists(changelog_path):
            with open(changelog_path, 'r') as changelog:
                changelog_content = changelog.read()
        else:
            changelog_content = 'Change log file not found'

        # log 파일 내용 읽기
        if os.path.exists(log_path):
            with open(log_path, 'r') as log_file:
                log_content = log_file.read()
        else:
            log_content = 'Log file not found.'

        # 날짜별로 changelog와 log 내용을 저장
        changelogs_by_date[changelog_date].append({
            'changelog': changelog_content,
            'log': log_content
        })

# HTML 파일 생성
with open(output_html_path, 'w') as html_file:
    html_file.write('<html><head><title>Jenkins Changelog</title></head><body>\n')
    html_file.write('<h1>젠킨스 빌드 히스토리</h1>\n')

    for date, entries in sorted(changelogs_by_date.items()):
        html_file.write(f'<hr><h2>일자 : {date}</h2>\n')
        for entry in entries:            
            if entry['changelog'] != '':                
                #print(entry['changelog'])
                result = parseLogContents(entry['changelog'])
                
                html_file.write('<div class="changelog-entry" style="margin-top:10px;">\n')
                html_file.write('<table border=1>\n')
                html_file.write('<tr><th>commiter_id</th><th>commiter_email</th><th>commit_message</th><th>files</th></tr>')
                                
                #내용 저장
                for item in result:
                    html_file.write('<tr>\n')
                    html_file.write(f'<td>{item["committer_id"]}</td>\n')
                    html_file.write(f'<td>{item["committer_email"]}</td>\n')
                    html_file.write(f'<td>{item["commit_message"]}</td>\n')
                    html_file.write(f'<td>\n')
                    for file in item['files']:
                        html_file.write(f'{file}<br>\n')
                    html_file.write('</td>\n')
                    html_file.write('</tr>\n')

                html_file.write('</table>\n')
                html_file.write('</div>\n')
        
    html_file.write('</body></html>\n')

print(f"HTML file generated at {output_html_path}")

