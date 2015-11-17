# coding=utf-8
import argparse
import logging
import os
import shutil
import sys
import threading
import time
import zipfile
from configparser import ConfigParser
from shutil import copy
import win32api
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, RotatingMarker

import replacer

parser = argparse.ArgumentParser()
parser.add_argument('-az', '--azkversion', nargs=1, help='Версия АЦК')
parser.add_argument('-gz', '--gzversion', nargs=1, help='Версия АЦК')
parser.add_argument('-name', '--azkdbname', nargs=1, help='Имя схемы')
parser.add_argument('-port', '--azkport', nargs=1, help='Порт сервера АЦК Финансы')
args = parser.parse_args()


def copy_bar(src, home):
    logging.info('Копирование %s в %s', src, home)
    size = os.path.getsize(src)
    t = threading.Thread(target=copy, args=(src, home,))
    t.setDaemon(True)
    t.start()
    tm = 0
    while True:
        if os.path.isfile(os.path.join(home, src)):
            break
        tm += 1
        time.sleep(0.2)
        if tm == 10:
            break
    name = os.path.basename(src)
    widgets = [name + ' ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=size).start()
    while True:
        cur_size = os.path.getsize(os.path.join(home, name))
        pbar.update(cur_size)
        if cur_size == size:
            break
    pbar.finish()


def zip_bar(file, folder=None):
    logging.info('Извлечение: %s', file)
    zf = zipfile.ZipFile(file)
    uncompress_size = sum((file.file_size for file in zf.infolist()))
    extracted_size = 0
    widgets = [file + ' ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=uncompress_size).start()
    for zip_file in zf.infolist():
        extracted_size += zip_file.file_size
        pbar.update(extracted_size)
        zf.extract(zip_file, path=folder)
    zf.close()
    pbar.finish()


def yno():
    reply = str(input('Удалить папку ? (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return 'Тебе сложно было ввести нормальный ответ? Самый умный, да?'


curDir = os.getcwd()


dos_path = os.path.dirname(os.path.realpath(sys.executable))
appDir = win32api.GetLongPathName(dos_path)
#appDir = os.path.dirname(os.path.realpath(__file__))



whiteFileList = ['apache-tomcat-6.0.29_BFT-1.0.zip', 'azk.war', 'client.zip', 'server.zip']
#whiteFileList = ['client.zip']
config = ConfigParser()
config.read(os.path.join(appDir, 'config.ini'))
mount = config.get('DISK', 'mount')
if config.has_option('VCL', 'path'):
    vcl = config.get('VCL', 'path')
else:
    vcl = False

# ver = '2.37.0.115'
if args.azkversion is not None:
    ver = args.azkversion[0].strip()
else:
    ver = input('Введите версию: ')

buildPath = '.'.join(ver.split('.')[:2])

try:
    os.chdir(r'{0}:/builds/azk2/{1}/{2}'.format(mount, buildPath, ver))
except FileNotFoundError:
    print('Версия {} не найдена'.format(ver))
    raise

azkFiles = os.listdir('.')
filesForCopy = [file for file in azkFiles if file in whiteFileList]

azkDir = os.path.join(curDir, ver)

if os.path.exists(azkDir):
    print('Папка с версией {0} уже есть в текущей директории {1}'.format(ver, curDir))
    if yno():
        print('Удаляем...')
        shutil.rmtree(azkDir)
        time.sleep(0.1)
        os.makedirs(azkDir)
    else:
        print('Поменяйте директорию или удалите папку')
        sys.exit(0)
else:
    os.makedirs(azkDir)

print('Начинаем копирование в {}'.format(azkDir))

for file in filesForCopy:
    copy_bar(file, azkDir)
os.chdir(azkDir)
azkExtractFiles = ['client.zip', 'server.zip']
azkDirFiles = [file for file in os.listdir('.') if file in azkExtractFiles]
print('Начинаем извлекать архивы...')
for file in azkDirFiles:
    if file == 'client.zip':
        zip_bar(file, folder='client')
    else:
        zip_bar(file)

if args.azkdbname is not None:
    dbname = args.azkdbname[0]
    print('Настраиваем Azk2Server.properties')
    replacer.replaceAzkConfig(dbname)

if args.azkport is not None:
    serverport = args.azkport[0]
    print('Меняем порт в StartServer.bat')
    replacer.replaceServerPort(serverport)

if vcl:
    print('Копируем библиотеки VCL')
    os.chdir(vcl)
    files = [f for f in os.listdir('.') if f.endswith('.bpl')]
    for file in files:
        shutil.copy(file, os.path.join(azkDir,'client'))

print('Конец работы!')