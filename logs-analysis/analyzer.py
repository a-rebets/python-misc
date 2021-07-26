from datetime import datetime
import re
import sys

log_line_pattern = re.compile(
    r'((?:\d+\.){3}\d+).*\[(\S+.+)\]\s+\"([A-Z]+)\s*(\S+).*\"\s+(\d{3})\s+(\d{3})')
accepted_methods = ['GET', 'HEAD', 'POST', 'PUT',
                    'DELETE', 'TRACE', 'OPTIONS', 'CONNECT', 'PATCH']


class MalformedHTTPRequest(Exception):
    pass


class Request:
    def __init__(self, method, path, status_code, size):
        self.method = method
        self.path = path
        self.status_code = status_code
        self.size = size

    def get_method(self):
        return self.method

    def get_path(self):
        return self.path

    def __str__(self):
        return 'Request[method - %s, path - %s, status - %s, size - %s]' % (self.method, self.path, self.status_code, self.size)


class LogEntry:
    def __init__(self, ip, timestamp, request_args):
        self.ip = ip
        self.timestamp = timestamp
        if request_args[0] in accepted_methods:
            self.request = Request(*request_args)
        else:
            raise MalformedHTTPRequest(
                'The request is not of an appropriate form')

    def __str__(self):
        return 'Log: %s %s %s' % (self.ip, str(self.timestamp), str(self.request))


def convert_line(line):
    match = log_line_pattern.match(line)
    if match != None:
        ip = match.group(1)
        timestamp = get_datetime_obj(match.group(2))
        method = match.group(3)
        path = match.group(4)
        status_code = match.group(5)
        size = int(match.group(6))
        log = LogEntry(ip, timestamp, (method, path, status_code, size))
        return log
    else:
        return None


def convert_file(file):
    res = []
    wrong_requests = 0
    for line in file:
        try:
            obj = convert_line(line)
            if obj is None:
                wrong_requests += 1
            else:
                res.append(obj)
        except MalformedHTTPRequest:
            wrong_requests += 1
    print(f'Found {wrong_requests} request(s) of an inappropirate form!')
    return res


def get_datetime_obj(arg):
    return datetime.strptime(arg, '%d/%b/%Y:%H:%M:%S %z')


def print_logs(arr, start_time, finish_time):
    print('Logs between dates:')
    if finish_time < start_time:
        sys.stderr.print("Finish date cannot be earlier than the start!")
    else:
        for log in arr:
            if log is not None:
                tmp = log.timestamp
                if start_time <= tmp <= finish_time:
                    print(log)


def run():
    try:
        source = open("./access_log.txt", "r", encoding='utf-8')
        start_time = get_datetime_obj('18/Oct/2020:10:59:54 +0200')
        end_time = get_datetime_obj('18/Oct/2020:15:02:29 +0200')
        print_logs(convert_file(source), start_time, end_time)
    except EnvironmentError:
        sys.stderr.write(
            'File with the specified name cannot be opened / found !')


if __name__ == '__main__':
    run()
