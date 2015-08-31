# coding=utf-8
import re
import os
import subprocess
import argparse
import collections

usage = '''%(prog)s <logdir>

Утилита для анализа логов. Для запуска укажите путь к папке с логами. Пример:
%(prog)s  C:\\azk\\logs
Результаты будут записаны в файл results.txt и разбиты по категориям:
ORA - оракловские ошибки
OTHERS - все остальные ошибки
Все подробности по ключу -h
'''
parser = argparse.ArgumentParser(description='Список команд',
                                 usage=usage,
                                 epilog='Вопросы и пожелания направлять на p.alekseev@bftcom.com')
parser.add_argument("logdir", help="Путь к папке с логами")
parser.add_argument("-f", "--files", action='store_true', help="Разбить результаты лога на отдельные файлы")
args = parser.parse_args()

print('Старт работы!')
folder = os.path.realpath(args.logdir)

# folder = r'E:\work\logs\2860\logsb312'
os.chdir(folder)
result = 'results.txt'
if os.path.isfile(result):
    os.remove(result)
files = [file for file in os.listdir(folder) if '.log' in file and '.zip' not in file and '.7z' not in file]

re_errors = re.compile(
    r'(\d\d\b.\d\d.\d\d \d\d\b:\d\d\b:\d\d\b.\d\d\d,.*,ERROR.*)([\s\S]*?)\d\d\b.\d\d.\d\d \d\d\b:\d\d\b:\d\d\b.\d\d\d')
re_ora = re.compile(r'ORA')

re_maxquery = re.compile(
    r'(\d\d\b.\d\d.\d\d \d\d\b:\d\d\b:\d\d\b.\d\d\d,.*Max query time .*)([\s\S]*?)\d\d\b.\d\d.\d\d \d\d\b:\d\d\b:\d\d\b.\d\d\d')
re_maxquery_time = re.compile(r'(?<=(exceeding \())(.*)(?=\s)')


def create_log():
    for log in files:
        print('Читаем файл {}'.format(log))

        with open(log, 'r') as loger:
            data = loger.read()

        errors = re.findall(re_errors, data)

        print('Количество найденных ошибок: {0}'.format(len(errors)))
        print('Записываем ошибки в лог.....')

        with open(result, 'a+') as fi:
            fi.write('\n')
            fi.write('=' * 50 + log + '=' * 50 + '\n')
            fi.write('\n')
        for error in errors:
            with open(result, 'a+') as fi:
                # Запишем сначала все ORA ошибки
                if re.search(re_ora, error[0] + error[1]):
                    fi.write('-' * 50 + 'ORA' + '-' * 50 + '\n')
                    fi.write(error[0])
                    fi.write(error[1])
            with open(result, 'a+') as fi:
                # Запишем  все остальные ошибки
                if not re.search(re_ora, error[0] + error[1]):
                    fi.write('-' * 50 + 'OTHERS' + '-' * 50 + '\n')
                    fi.write(error[0])
                    fi.write(error[1])

        print('Ищем долгие запросы....')
        maxquery = re.findall(re_maxquery, data)
        maxquery_time_result = {}
        print('Количество найденных долгих запросов: {0}'.format(len(maxquery)))
        print('Записываем долгие заросы в лог.....')
        for query_error in maxquery:
            time_result = re.search(re_maxquery_time, query_error[0]).group()
            maxquery_time_result[int(time_result)] = query_error
        od = collections.OrderedDict(sorted(maxquery_time_result.items()))
        for i in sorted(od.keys(), reverse=True):
            with open(result, 'a+') as fi:
                fi.write('-' * 50 + '>> Max query time ' + '-' * 50 + '\n')
                fi.write(od[i][0] + od[i][1])


def create_log_files():
    for log in files:
        print('Читаем файл {}'.format(log))

        with open(log, 'r') as loger:
            data = loger.read()

        errors = re.findall(re_errors, data)
        print('Количество найденных ошибок: {0}'.format(len(errors)))

        ora_errors = []
        others_errors = []
        if errors:
            ora_errors.append('=' * 50 + log + '=' * 50 + '\n')
            others_errors.append('=' * 50 + log + '=' * 50 + '\n')
            for error in errors:
                if re.search(re_ora, error[0] + error[1]):
                    ora_errors.append('-' * 50 + '\n')
                    ora_errors.append(error[0] + error[1])
                if not re.search(re_ora, error[0] + error[1]):
                    others_errors.append('-' * 50 + '\n')
                    others_errors.append(error[0] + error[1])

        print('Ищем долгие запросы....')
        maxquery = re.findall(re_maxquery, data)
        maxquery_time_result = {}
        print('Количество найденных долгих запросов: {0}'.format(len(maxquery)))

        maxquery_errors = []
        if maxquery:
            maxquery_errors.append('=' * 50 + log + '=' * 50 + '\n')
            print('Записываем долгие запросы в лог.....')
            for query_error in maxquery:
                time_result = re.search(re_maxquery_time, query_error[0]).group()
                maxquery_time_result[int(time_result)] = query_error
            od = collections.OrderedDict(sorted(maxquery_time_result.items()))
            for i in sorted(od.keys(), reverse=True):
                maxquery_errors.append('-' * 50 + '\n')
                maxquery_errors.append(od[i][0] + od[i][1])

        with open('result_ORA.txt', 'a+') as fi:
            for text in ora_errors:
                fi.write(text)

        with open('result_OTHERS.txt', 'a+') as fi:
            for text in others_errors:
                fi.write(text)

        with open('result_MAXQUERY.txt', 'a+') as fi:
            for text in maxquery_errors:
                fi.write(text)

if args.files:
    create_log_files()
else:
    create_log()

print('Работа парсера завершена!')
subprocess.Popen('explorer "{0}"'.format(folder))