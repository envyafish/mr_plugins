import multiprocessing
import random
import threading
import time

from plugins.xx.logger import Logger
from plugins.xx.models import Course

queue = multiprocessing.Queue(20)
lock = threading.Lock()


def get_course():
    if queue.empty():
        return None
    lock.acquire()
    course = queue.get()
    Logger.info(f"{course.code}开始搜索学习资料")
    Logger.info("下一节课将在50-80S之后开始搜索可下载的资料")
    time.sleep(random.randint(50, 80))
    lock.release()
    return course


def put_course(course: Course):
    Logger.info(f"添加课程{course.code}到队列中,等待资源搜索")
    queue.put(course)
