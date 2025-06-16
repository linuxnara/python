import jaydebeapi
import jpype
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.dates as mdates
from datetime import datetime
import threading
import time
import collections
import sys

from matplotlib import font_manager, rc
plt.rcParams['axes.unicode_minus'] = False

#차트 폰트 설정
path = "c:/Windows/Fonts/malgun.ttf"
font_name = font_manager.FontProperties(fname=path).get_name()
rc('font', family=font_name)

# 1. Tibero 데이터베이스 접속 정보
# Tibero JDBC 드라이버(.jar 파일)의 전체 경로(jdbc지원하는 파일은 뭐든 될듯)
JDBC_DRIVER_PATH = "C:/Temp/pydbmon/tibero7-jdbc.jar"

# Tibero JDBC 드라이버의 자바 클래스 이름
JDBC_DRIVER_CLASS = "com.tmax.tibero.jdbc.TbDriver"

# Tibero JDBC 연결 URL
JDBC_URL = "jdbc:tibero:thin:@127.0.0.1:0000:BIZB2C" # @서버IP:포트:SID

# 데이터베이스 접속 정보
DB_USER = "aaaa"
DB_PASSWORD = "bbbb"


# SITEID 목록 정의
SITE_IDS = [f'S{i:03d}' for i in range(1, 9)] # S001부터 S008까지

# QUERY 변경: SITEID를 파라미터로 받을 수 있도록 수정
QUERY_ALL_SITES_TEMPLATE = """
SELECT
    SITEID,
    SUM(CASE WHEN ORDSTEP = '000' THEN 1 ELSE 0 END) AS ERROR_COUNT,
    SUM(CASE WHEN ORDSTEP <> '000' THEN 1 ELSE 0 END) AS ORDER_COUNT
FROM
    TEST
WHERE
    SITEID IN ({site_ids_placeholder})
    AND REGDATE >= TO_DATE('{start_date}', 'YYYYMMDDHH24MISS')
    AND REGDATE <= TO_DATE('{end_date}', 'YYYYMMDDHH24MISS')
GROUP BY
    SITEID
ORDER BY
    SITEID
"""
# --- 설정 영역 끝 ---

# 데이터 저장을 위한 설정
MAX_DATA_POINTS = 20
timestamps = collections.deque(maxlen=MAX_DATA_POINTS)
# 각 SITEID별 데이터를 저장할 딕셔너리
site_data = {
    site_id: {
        'error': collections.deque(maxlen=MAX_DATA_POINTS),
        'order': collections.deque(maxlen=MAX_DATA_POINTS)
    } for site_id in SITE_IDS
}
data_lock = threading.Lock()

# 프로그램 종료 플래그
program_running = True

def data_fetcher():
    print("데이터 수집 스레드를 시작합니다.")
    while True:
        conn = None
        try:
            conn = jaydebeapi.connect(
                JDBC_DRIVER_CLASS,
                JDBC_URL,
                [DB_USER, DB_PASSWORD],
                JDBC_DRIVER_PATH
            )
            current_time = datetime.now()
            start_date_str = current_time.strftime('%Y%m%d000000')
            end_date_str = current_time.strftime('%Y%m%d235959')

            with data_lock:
                timestamps.append(current_time)

            # SITE_IDS 리스트를 SQL IN 절에 사용할 문자열로 변환
            # 예: "'S001', 'S002', ..., 'S008'"
            site_ids_str = ", ".join(f"'{s}'" for s in SITE_IDS)

            # 쿼리 포맷팅
            query = QUERY_ALL_SITES_TEMPLATE.format(
                site_ids_placeholder=site_ids_str,
                start_date=start_date_str,
                end_date=end_date_str
            )

            with conn.cursor() as cursor:
                cursor.execute(query)
                results = cursor.fetchall()

                # 모든 SITEID에 대해 초기 값을 0으로 설정 (데이터가 없는 경우를 대비)
                fetched_site_data = {site_id: {'error': 0, 'order': 0} for site_id in SITE_IDS}

                # 쿼리 결과 파싱 및 fetched_site_data에 저장
                for row in results:
                    site_id_from_db, error_count, order_count = row
                    fetched_site_data[site_id_from_db]['error'] = error_count
                    fetched_site_data[site_id_from_db]['order'] = order_count

                # 수집된 데이터를 site_data deque에 추가
                with data_lock:
                    for site_id in SITE_IDS:
                        site_data[site_id]['error'].append(fetched_site_data[site_id]['error'])
                        site_data[site_id]['order'].append(fetched_site_data[site_id]['order'])
                        print(f"[{current_time.strftime('%H:%M:%S')}] SITEID: {site_id}, ERROR={fetched_site_data[site_id]['error']}, ORDER={fetched_site_data[site_id]['order']}")

        except jpype.JException as e:
            print(f"Java/JDBC 오류 발생: {e}")
        except Exception as e:
            print(f"알 수 없는 오류 발생: {e}")
        finally:
            if conn:
                # 중요: DB 연결은 try 블록이 끝나자마자 닫는 것이 안전합니다.
                # 다음 루프 시작 전에 완전히 해제되도록 합니다.
                try:
                    conn.close()
                    print("DEBUG: DB 연결 성공적으로 닫음.")
                except Exception as e:
                    print(f"DEBUG: DB 연결 닫는 중 오류 발생: {e}")

        # --- 종료 신호 감지 로직 강화 ---
        if not program_running: # 쿼리 실행 후 바로 확인
            print("DEBUG: data_fetcher 스레드, 쿼리 후 종료 신호 감지.")
            break

        # 다음 쿼리까지 대기. 대기 중에도 종료 신호를 계속 확인
        wait_time = 60 # 초
        start_wait = time.time()
        while time.time() - start_wait < wait_time:
            if not program_running:
                print(f"DEBUG: data_fetcher 스레드, 대기 중 종료 신호 감지. 남은 대기 시간: {wait_time - (time.time() - start_wait):.2f}초")
                break
            time.sleep(1) # 1초마다 확인

        if not program_running: # 대기 루프 종료 후 다시 확인
            print("DEBUG: data_fetcher 스레드, 대기 종료 후 최종 종료.")
            break

    print("데이터 수집 스레드가 종료됩니다.")

def animate(i, axes):
    """
    주기적으로 그래프를 업데이트
    """
    with data_lock:
        # 전체 타임스탬프가 비어있으면 그리지 않고 종료
        if not timestamps:
            return

        for idx, site_id in enumerate(SITE_IDS):
            ax = axes.flatten()[idx] # 2D axes 배열을 1D로 평탄화하여 인덱싱
            ax.clear()

            # 해당 SITEID의 error/order 데이터 덱 가져오기
            current_errors = site_data[site_id]['error']
            current_orders = site_data[site_id]['order']

            # 데이터의 길이가 타임스탬프의 길이와 일치하고, 데이터가 비어있지 않은 경우에
            if len(timestamps) > 0 and len(current_errors) == len(timestamps) and len(current_orders) == len(timestamps):
                ax.plot(timestamps, current_errors, 'r-o', label='Error Count')
                ax.plot(timestamps, current_orders, 'b-s', label='Order Count')
            elif len(timestamps) > 0 and len(current_errors) < len(timestamps):
                # 여기서는 그냥 그리지 않고 넘어감
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Warning: Data length mismatch for {site_id}. "
                      f"timestamps={len(timestamps)}, errors={len(current_errors)}, orders={len(current_orders)}")
                # 필요하다면 빈 그래프라도 표시하도록 처리할 수 있음
                # ax.text(0.5, 0.5, "데이터 로딩 중...", horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
                
            else:
                # 데이터가 전혀 없는 경우
                print(f"[{datetime.now().strftime('%H:%M:%S')}] No data yet for SITEID: {site_id}")


            siteTitle = ""
            if site_id == "S001" : 
                siteTitle = "테스트1"
            elif site_id == "S002":
                siteTitle = "테스트2"
            elif site_id == "S003":
                siteTitle = "테스트3"

            ax.set_title(f'{siteTitle}({site_id})', fontsize=12)
            ax.set_ylabel('건수', fontsize=10)
            ax.legend(loc='upper left', fontsize=8)
            ax.grid(True)

            time_format = mdates.DateFormatter('%H:%M')
            ax.xaxis.set_major_formatter(time_format)
            plt.setp(ax.get_xticklabels(), rotation=30, ha="right", fontsize=8)
            ax.tick_params(axis='y', labelsize=8)

    plt.tight_layout(pad=3.0)

# 종료
def on_close(event):
    global program_running
    print("DEBUG: on_close 함수 진입 - Matplotlib 창이 닫혔습니다.")
    program_running = False # 데이터 수집 스레드 종료 플래그 설정
    print("DEBUG: program_running 플래그 설정 완료.")

    # 데이터 수집 스레드가 종료될 때까지 잠시 대기
    print("DEBUG: data_fetcher 스레드 종료 대기 중...")
    fetch_thread.join(timeout=5) # 최대 5초 대기
    if fetch_thread.is_alive():
        print("DEBUG: 경고: data_fetcher 스레드가 5초 내에 종료되지 않았습니다.")
    else:
        print("DEBUG: data_fetcher 스레드 성공적으로 종료.")

    if jpype.isJVMStarted():
        print("DEBUG: JVM을 종료합니다...")
        try:
            jpype.shutdownJVM() # 정상적으로 종료되지 않음.. 왜 그러지?
            print("DEBUG: JVM이 성공적으로 종료되었습니다.")
        except Exception as e:
            print(f"DEBUG: JVM 종료 중 오류 발생: {e}")
    else:
        print("DEBUG: JVM이 시작되지 않았거나 이미 종료되었습니다.")

    print("DEBUG: sys.exit(0) 호출 직전.")
    sys.exit(0) # 프로그램 강제 종료

if __name__ == "__main__":
    global fetch_thread

    jpype.startJVM(jpype.getDefaultJVMPath(), "-Djava.class.path=" + JDBC_DRIVER_PATH, "-Xrs", "-XX:MaxJavaStackTraceDepth=1000")
    fetch_thread = threading.Thread(target=data_fetcher, daemon=True)
    fetch_thread.start()

    # 데이터 수집 스레드가 최소한 한 번 데이터를 가져올 때까지 대기
    print("초기 데이터 수집을 기다리는 중...")
    while True:
        with data_lock:
            if timestamps: # timestamps에 데이터가 하나라도 있으면
                all_site_data_ready = True
                for site_id in SITE_IDS:
                    # 모든 site_id에 대해 error, order 데이터가 timestamps와 길이가 같은지 확인
                    if not site_data[site_id]['error'] or \
                       len(site_data[site_id]['error']) != len(timestamps) or \
                       not site_data[site_id]['order'] or \
                       len(site_data[site_id]['order']) != len(timestamps):
                        all_site_data_ready = False
                        break
                if all_site_data_ready:
                    print("초기 데이터 수집 완료. 그래프를 시작합니다.")
                    break
        time.sleep(1) # 1초마다 확인

    fig, axes = plt.subplots(nrows=2, ncols=4, figsize=(18, 10), sharex=True)
    fig.suptitle('실시간 주문/에러 모니터링 (SITE별)', fontsize=18)

    fig.canvas.mpl_connect('close_event', on_close)

    ani = animation.FuncAnimation(fig, animate, fargs=(axes,), interval=1000, cache_frame_data=False)

    plt.show()

    # jpype.shutdownJVM()
    # print("프로그램을 종료합니다.")
