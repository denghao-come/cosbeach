import multiprocessing
from gevent import monkey;monkey.patch_all(thread=False);  # monkey.patch_socket();
import gevent
import gevent.queue

import os
import sys
import requests
import boto3
import botocore
import random
import argparse
import time
import psutil
import queue
from io import BytesIO
import logging
from urllib.request import urlopen
from json import load

logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] - %(process)d - %(levelname)s: %(message)s"))
my_ip = load(urlopen('https://api.ipify.org/?format=json'))['ip']
logger.addHandler(handler)

def create_s3_client(args):
    config_dict = {'signature_version': 's3', 'connect_timeout': 30000, 'read_timeout': 30000, 'max_pool_connections': 300}
    configuration = boto3.session.Config(**config_dict)

    client = boto3.client('sts',
        aws_access_key_id=args.access_key,
        aws_secret_access_key=args.secret_key,
        endpoint_url=args.endpoint_url,
        region_name=args.region_name,
        use_ssl=args.use_ssl,
        config=configuration,
    )

    return client

def create_session_client(client, args):
    response = client.get_session_token(DurationSeconds=args.duration_seconds)
    ak = response['Credentials']['AccessKeyId']
    sk = response['Credentials']['SecretAccessKey']
    token = response['Credentials']['SessionToken']

    s3_session = boto3.Session(
          aws_access_key_id=ak,
          aws_secret_access_key=sk,
          aws_session_token=token
    )

    #在liunx中可以使用下面这行，带超时重连参数的
    #config = boto3.session.Config(connect_timeout=3000000, read_timeout=3000000, retries={'max_attempts': 0}, signature_version="s3")
    #在Windows中使用这个不带参数的代码，上面那个带参数的会报错
    config = boto3.session.Config(signature_version="s3")
    session_client = s3_session.client('s3', endpoint_url=args.endpoint_url, config=config)

    return session_client

class CostThread(gevent.Greenlet):
    def __init__(self, task_queue, args):
        gevent.Greenlet.__init__(self)

        self.task_queue = task_queue
        self.total_num = args.thread_num * args.file_num
        self.result_queue = args.result_queue
        self.internal_time = args.internal_time
        self.argss = args

        self.cost_time = 0
        self.err_num = 0
        self.num_loop = 0
        self.pid = os.getpid()
    def statistic_info(self, ct, net):
        if ct < 0.00001:
            logger.info('再等一会儿。。。')
            return

        cnet = psutil.net_io_counters()

        throughtput = (cnet.bytes_sent - net.bytes_sent) + (cnet.bytes_recv - net.bytes_recv)

        throughtput /= ct

        if throughtput > 2**30:
            throughtput = '{0:.2f}GB'.format(throughtput/2**30)
        elif throughtput > 2**20:
            throughtput = '{0:.2f}MB'.format(throughtput/2**20)
        elif throughtput > 2**10:
            throughtput = '{0:.2f}KB'.format(throughtput/2**10)
        else:
            throughtput = '{0:.2f}B'.format(throughtput)
        file_size = self.argss.file_size
        method = self.argss.method
        if method == 'download':
            method = '下载'
        elif method == 'upload':
            method = '上传'
        else:
            method = '删除'
        if self.argss.sts_token:
            method = 'STS '
            file_size = ''

        success_num = self.num_loop - self.err_num
        if not success_num:
            logger.info('请求数量：%s，失败数量：%s', self.num_loop, self.err_num)
            logger.info('请求全部失败:<')
            return
        output_format = '\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+\n' +\
                        '|  请求数   | 请求耗时 | 失败请求数 | 请求平均耗时 | 请求成功率 | 运行耗时 |   QPS  |   带宽   | 类型 | 文件  |\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+\n' +\
                        '| {0:^9} | {1:^8} | {2:^10} | {3:^12} | {4:^10} | {5:^8} | {6:^6.1f} | {7:^8} | {8:^2} | {9:^5} |\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+'
        logger.info(output_format.format(self.num_loop, '%.0fs'%self.cost_time, self.err_num, '%.0fms'%(self.cost_time*1000/success_num),
                                        '%.0f%%'%(success_num*100/self.num_loop), '%.0fs'%ct, self.num_loop/ct, throughtput, method, file_size))

    def _run(self):
        st = time.time()
        st2 = st

        net = psutil.net_io_counters()

        while self.num_loop < self.total_num:
            try:
                t, err = self.task_queue.get_nowait()
            except gevent.queue.Empty:
                gevent.sleep(0)
                continue

            self.cost_time += t
            self.err_num += err
            self.num_loop += 1

            st3 = time.time()
            if (st3 - st2) >= self.internal_time:
                # self.statistic_info(st3 - st, net)
                st2 = time.time()
                try:
                    self.result_queue.put_nowait((self.cost_time, self.err_num, self.pid, self.num_loop))
                except queue.Full:
                    logger.exception('queue Full')
            # gevent.sleep(0)
        else:
            # self.statistic_info(st3 - st, net)

            try:
                self.result_queue.put_nowait((self.cost_time, self.err_num, self.pid, self.num_loop))
                self.result_queue.put_nowait(('EOF', 0, self.pid, self.num_loop))
            except queue.Full:
                logger.exception('queue Full')

class FileThread(gevent.Greenlet):
    def __init__(self, id, q, args):
        gevent.Greenlet.__init__(self)
        self.thread_id = id
        self.queue = q
        self.argss = args
        self.count = args.file_num
        self.size = args.filesize
        self.prefix_name = args.prefix_name
        self.presign = args.presign
        self.method = args.method

        self.s3_client = args.client

        self.session_client = None

        self.session_recreate_time = args.duration_seconds * 0.8

        self.ascii_chr = [chr(x).encode() for x in range(27, 127)] if self.method == 'upload' else ''

    def _run(self):
        start_time = time.time()

        self.session_client = create_session_client(self.s3_client, self.argss)

        num = 1
        while num <= self.count:
            e_time = 0
            bad_request = 0
            current_time = time.time()

            if (current_time - start_time) >= self.session_recreate_time:
                self.session_client = create_session_client(self.s3_client, self.argss)

            if self.method == 'upload':
                random.shuffle(self.ascii_chr)
                body = BytesIO(b''.join(self.ascii_chr)*(self.size//100))

            name = '%s_%d'%(self.prefix_name, self.thread_id * self.count * self.argss.group_num + num)

            try:
                if self.presign:
                    presign_param = {
                        'download': dict(ClientMethod='get_object', HttpMethod='GET'),
                        'upload': dict(ClientMethod='put_object', HttpMethod='PUT'),
                        'delete': dict(ClientMethod='delete_object', HttpMethod='DELETE'),
                    }

                    url = self.session_client.generate_presigned_url(
                        **presign_param[self.method],
                        Params={'Bucket': self.argss.bucket, 'Key': name},
                        ExpiresIn=3600,
                    )

                    s_time = time.time()
                    if self.method == 'download':
                        res = requests.get(url)
                    elif self.method == 'upload':
                        res = requests.put(url, data=body)
                    else:
                        res = requests.delete(url)

                    e_time = time.time() - s_time

                    if res.status_code >= 300:
                        bad_request = 1
                else:
                    s_time = time.time()
                    if self.method == 'download':
                        resp = self.session_client.get_object(Bucket=self.argss.bucket, Key=name)
                        resp['Body'].read()
                    elif self.method == 'upload':
                        self.session_client.put_object(Bucket=self.argss.bucket, Key=name, Body=body)
                    else:
                        self.session_client.delete_object(Bucket=self.argss.bucket, Key=name)
                    e_time = time.time() - s_time
            except Exception as e:
                logger.exception(e)
                e_time = 0
                bad_request = 1

            num += 1
            try:
                self.queue.put_nowait((e_time, bad_request))
            except gevent.queue.Full:
                logger.exception('gevent queue full')
                gevent.sleep(0.1)
                self.queue.put_nowait((e_time, bad_request))

            gevent.sleep(0)

class STSThread(gevent.Greenlet):
    def __init__(self, id, q, args):
        gevent.Greenlet.__init__(self)
        self.thread_id = id
        self.queue = q
        self.argss = args
        self.count = args.file_num
        self.s3_client = args.client

    def _run(self):
        num = 1
        while num <= self.count:
            e_time = 0
            bad_request = 0

            try:
                s_time = time.time()
                self.s3_client.get_session_token(DurationSeconds=self.argss.duration_seconds)    
                e_time = time.time() - s_time
            except:
                bad_request = 1
            num += 1
            try:
                self.queue.put_nowait((e_time, bad_request))
            except gevent.queue.Full:
                gevent.sleep(0.1)
                self.queue.put_nowait((e_time, bad_request))

            gevent.sleep(0)

class RunnerInfo():
    def __init__(self, args):
        self.result_queue = args.result_queue
        self.internal_time = args.internal_time
        self.argss = args

        self.cost_time = 0
        self.err_num = 0
        self.num_loop = 0
        self.group_loop = 0
        self.group = {}
    def statistic_info(self, ct, net):
        if ct < 0.00001:
            logger.info('再等一会儿。。。')
            return

        cnet = psutil.net_io_counters()

        throughtput = (cnet.bytes_sent - net.bytes_sent) + (cnet.bytes_recv - net.bytes_recv)
        throughtput /= ct

        if throughtput > 2**30:
            throughtput = '{0:.2f}GB'.format(throughtput/2**30)
        elif throughtput > 2**20:
            throughtput = '{0:.2f}MB'.format(throughtput/2**20)
        elif throughtput > 2**10:
            throughtput = '{0:.2f}KB'.format(throughtput/2**10)
        else:
            throughtput = '{0:.2f}B'.format(throughtput)
        file_size = self.argss.file_size
        method = self.argss.method
        if method == 'download':
            method = '下载'
        elif method == 'upload':
            method = '上传'
        else:
            method = '删除'
        if self.argss.sts_token:
            method = 'STS '
            file_size = ''

        success_num = self.num_loop - self.err_num
        if not success_num:
            logger.info('当前请求数量：%s，失败数量：%s', self.num_loop, self.err_num)
            logger.info('请求全部失败:<')
            return
        output_format = '\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+\n' +\
                        '|  请求数   | 请求耗时 | 失败请求数 | 请求平均耗时 | 请求成功率 | 运行耗时 |   QPS  |   带宽   | 类型 | 文件  |\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+\n' +\
                        '| {0:^9} | {1:^8} | {2:^10} | {3:^12} | {4:^10} | {5:^8} | {6:^6.1f} | {7:^8} | {8:^2} | {9:^5} |\n' +\
                        '+-----------+----------+------------+--------------+------------+----------+--------+----------+------+-------+'
        logger.info(output_format.format(self.num_loop, '%.0fs'%self.cost_time, self.err_num, '%.0fms'%(self.cost_time*1000/success_num),
                                        '%.0f%%'%(success_num*100/self.num_loop), '%.0fs'%ct, self.num_loop/ct, throughtput, method, file_size))

    def run(self):
        st = time.time()
        st2 = st

        net = psutil.net_io_counters()

        while True:
            try:
                t, err, pid, num = self.result_queue.get(timeout=30)
            except queue.Empty:
                logger.exception('result queue empty')
                break
            else:
                if t == 'EOF':
                    self.group_loop += 1
                    if self.group_loop == self.argss.group_num:
                        break
                    continue

                if pid not in self.group.keys():
                    self.group[pid] = {}

                self.group[pid]['cost_time'] = t
                self.group[pid]['err_num'] = err
                self.group[pid]['cur_num'] = num

            # logger.info(self.group)

            self.cost_time = 0
            self.err_num = 0
            self.num_loop = 0

            for _pid in self.group.keys():
                self.cost_time += self.group[_pid]['cost_time']
                self.err_num += self.group[_pid]['err_num']
                self.num_loop += self.group[_pid]['cur_num']
            st3 = time.time()
            if (st3 - st2) >= self.internal_time:
                self.statistic_info(st3 - st, net)
                st2 = time.time()
        self.statistic_info(time.time() - st, net)

def runner_info(args):
    logger = logging.getLogger()

    #time_str = time.strftime('%Y%m%d%H%M%S', time.localtime())
    file_handler = logging.FileHandler('s3.log.%s'%my_ip, 'a', 'utf8')
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] - %(levelname)s: %(message)s"))
    logger.addHandler(file_handler)

    logger.info('命令：%s', ' '.join(sys.argv))

    if not args.sts_token:
        logger.info('文件名前缀：{0}，文件总数量{1}个'.format(args.prefix_name, args.total_put))
    else:
        logger.info('请求总数量{0}个'.format(args.total_put))

    RunnerInfo(args).run()

def runner(args):
    try:
        args.client = create_s3_client(args)
    except Exception as e:
        logger.exception('创建S3 Client 失败，%s', e)
        sys.exit(1)
    task_queue = gevent.queue.Queue()

    threads = [CostThread(task_queue, args)]

    for index in range(0, args.thread_num):
        if args.sts_token:
            t = STSThread(index, task_queue, args)
        else:
            t = FileThread(index, task_queue, args)
        threads.append(t)
    for t in threads:
        t.start()

    gevent.joinall(threads)

def main(args):
    args.total_put =  args.group_num * args.thread_num * args.file_num

    if not args.sts_token:
        if args.method in ('upload', 'download', 'delete'):
            if args.method in ('download', 'delete') and not args.prefix_name:
                logger.info('下载或删除文件时必须指定名称前缀 prefix_name')
                return
        else:
            logger.info('不支持的类型：{}'.format(args.method))
            return

        filesize = args.file_size.upper()
        if (len(filesize) < 3) or (filesize[-2:] not in ('KB', 'MB')):
            logger.info('文件大小参数 {} 写法错误'.format(args.file_size))
            return
        try:
            filesize_num = float(filesize[:-2])
        except ValueError:
            logger.info('文件大小参数 {} 写法错误'.format(args.file_size))
            return

        if filesize[-2:]  == 'KB':
            args.filesize = int(filesize_num * 2**10)
        else:
            args.filesize = int(filesize_num * 2**20)
        args.prefix_name = args.prefix_name if args.prefix_name else 'name_{0}'.format(random.randint(100, 9000))

    if not args.total_put or not args.group_num:
        return
    args.result_queue = multiprocessing.Queue()
    process_info_out = multiprocessing.Process(target=runner_info, args=(args,))
    process_info_out.start()

    # pool = multiprocessing.Pool(processes=args.group_num)
    # for i in range(args.group_num):
    #     pool.apply_async(func=runner, args=(args,))
    # pool.close()
    # pool.join()

    process_list = []
    for _ in range(args.group_num):
        process = multiprocessing.Process(target=runner, args=(args,))
        process_list.append(process)

    for proc in process_list:
        proc.start()
    for proc in process_list:
        proc.join()

    process_info_out.join()

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=(
            '向S3服务发送或下载文件。\n' +
            '示例：\n' +
            's3_upload_file.py -n 1000 -t 10\n' +
            '表示模拟 10 个用户，每个用户发送 1000 个请求，那么一共发送 10*1000 个请求' +
            '检查的类型有 upload、download、delete，默认是 upload'
        ))

        parser.add_argument(
            '-g', '--group',
            dest='group_num',
            type=int,
            help='用户组数量，默认为1',
            default=1,
        )
        parser.add_argument(
            '-t', '--thread',
            dest='thread_num',
            type=int,
            help='用户数量，默认10',
            default=10,
        )
        parser.add_argument(
            '-n', '--num',
            dest='file_num',
            type=int,
            help='每个用户发送的请求数量，默认10000',
            default=10000,
        )
        parser.add_argument(
            '-s', '--size',
            dest='file_size',
            type=str,
            help='每次发动的文件大小，默认4MB',
            default='4MB',
        )
        parser.add_argument(
            '-m', '--method',
            dest='method',
            type=str,
            help='检查类型',
            default='upload', # 'download', 'delete'
        )
        parser.add_argument(
            '-p', '--prefix',
            dest='prefix_name',
            type=str,
            help='名称前缀',
            default='',
        )
        parser.add_argument(
            '--presign',
            dest='presign',
            action='store_true',
            help='使用私有链接',
        )
        parser.add_argument(
            '-i', '--internal_time',
            dest='internal_time',
            type=int,
            help='日志打印时长间隔',
            default=2,
        )
        parser.add_argument(
            '-S', '--sts_token',
            dest='sts_token',
            action='store_true',
            help='检查获取 STS token接口',
        )
        parser.add_argument(
            '--access_key',
            dest='access_key',
            type=str,
            help='access key',
            default='',
        )
        parser.add_argument(
            '--secret_key',
            dest='secret_key',
            type=str,
            help='secret key',
            default='',
        )
        parser.add_argument(
            '--endpoint_url',
            dest='endpoint_url',
            type=str,
            help='endpoint url',
            default='',
        )
        parser.add_argument(
            '--region_name',
            dest='region_name',
            type=str,
            help='region_name',
            default='',
        )
        parser.add_argument(
            '--use_ssl',
            dest='use_ssl',
            action='store_true',
            help='use_ssl',
        )
        parser.add_argument(
            '--bucket',
            dest='bucket',
            type=str,
            help='bucket',
            default='',
        )
        parser.add_argument(
            '-d', '--duration_seconds',
            dest='duration_seconds',
            type=int,
            help='STS 客户端持续时间',
            default=3600,
        )

        args = parser.parse_args()

        main(args)

    except Exception as e:
        raise