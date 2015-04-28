__author__ = 'MissiaL'

import os
from shutil import copy, rmtree
import threading
import time
import zipfile
import fileinput
import argparse
import sys
import configparser
import re
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, RotatingMarker

usage = '''downloader.exe [option] ... [-s | -c | -sc ] ... [-f | -o ] ... [arg]
Скрипт выкачивает с текущей папки архивы, создает необходимые директории
и распаковывает в папку, указанную в конфигурационном файле.
Оставляет все папки и файлы, указанные в конфигурационном файле

Основные параметры:
-sc     : Выкачивание сервера и клиента
-s      : Выкачивание сервера
-c      : Выкачивание клиента
Дополнительные параметры:
-f      : Тип БД Firebird. Необходимо указать путь к БД.
          Если не указать логин и пароль, то используется
          стандартный логин и пароль(sysdba, masterkey)
-o      : Тип БД Oracle. Так же необходимо указать
          логин и пароль к БД
Примеры использования:
downloader.exe -s
Выкачивает server.zip, распаковывает, удаляет файлы
-------
downloader.exe -sс -o AZ_VOLGOBL_20150420 AZ_VOLGOBL_20150420
Выкачивает server.zip, client.zip, распаковывает, настраивает
Azk2Server.properties под под запуск с БД Oracle
-------
downloader.exe -s -f C:\\base\\FIREBIRD.FDB
Выкачивает server.zip, распаковывает, настраивает
Azk2Server.properties под под запуск с БД FireBird
        '''

parser = argparse.ArgumentParser(description='List of commands:', usage=usage)
parser.add_argument('-s', '--server', action='store_const', const=['server.zip'], help='Только server.zip')
parser.add_argument('-c', '--client', action='store_const', const=['client.zip'], help='Только client.zip')
parser.add_argument('-sc', '--sc', action='store_const', const=['server.zip', 'client.zip'],
                    help='Только client.zip и server.zip')
parser.add_argument('-f', '--INTERBASE', nargs='*', help='Путь к БД. Необязательные параметры: логин, пароль')
parser.add_argument('-o', '--ORACLE', nargs=2, help='Логин и пароль от БД')
args = parser.parse_args()
opt = vars(args)

files = ['server.zip']
db = []
for i, d in opt.items():
    if i in ['server', 'sc', 'client'] and d is not None:
        files = d
    if i in ['INTERBASE', 'ORACLE'] and d is not None:
        db.append(i)
        db = db + d

config = configparser.ConfigParser()
config.read(os.path.join(sys.argv[0][:-14], 'conf.ini'))
try:
    dest = config['PATH']['dir']
    need_files = config['FILES']['need']
except KeyError:
    print('File conf.ini not found!!!!!!')
    raise


def zip_barr(file, folder=None):
    print('\nExtracting: {0}'.format(file))
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


def copy_bar(src, dest):
    print('\nCopying: {0} to {1}'.format(src, dest))
    size = os.path.getsize(src)
    t = threading.Thread(target=copy, args=(src, dest,))
    t.start()
    tm = 0
    while True:
        if os.path.isfile(os.path.join(dest, src)):
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
        cur_size = os.path.getsize(os.path.join(dest, name))
        pbar.update(cur_size)
        if cur_size == size:
            break
    pbar.finish()




def edit_config(config_db):

    # def replacer(search, replace):
    #     print('Replace {0} to {1}'.format(search, replace))
    #     for line in fileinput.input(cfg, inplace=True):
    #         print(line.replace(search, replace), end='')
    cfg_file = 'Azk2Server.properties'

    def replacer(re_search, replace):
        cfg = open(cfg_file, "r")
        regex = re.compile(re_search)
        for line in cfg:
            if regex.search(line):
                line_for_replace = line.strip()
        cfg.close()
        print('Replace {0} to {1}'.format(line_for_replace, replace))
        for line in fileinput.input(cfg_file, inplace=True):
            print(line.replace(line_for_replace, replace), end='')



    print('\nEdit {0}'.format(cfg_file))
    # config_db = ['ORACLE', 'AZ_ROSTOVOBL_20150203', 'AZ_ROSTOVOBL_20150203']
    db_name = None
    path = None
    login = None
    pwd = None

    if config_db:
        db_name = config_db[0]
        if len(config_db) >= 2:
            path = config_db[1].replace('\\', '/')
        if len(config_db) >= 3:
            login = config_db[2]
        if len(config_db) >= 4:
            pwd = config_db[3]

    if db_name == 'INTERBASE':
        replacer('\A#azk.db.accessmode=INTERBASE', 'azk.db.accessmode=INTERBASE')
        if path:
            replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                     'azk.db.url=jdbc:firebirdsql:127.0.0.1/3050:' + path)
        if login:
            replacer('\Aazk.db.user=SYSDBA', 'azk.db.user=' + login)
        if pwd:
            replacer('\Aazk.db.password=masterkey', 'azk.db.password=' + pwd)

    if db_name == 'ORACLE':
        replacer('\A#azk.db.accessmode=ORACLE', 'azk.db.accessmode=ORACLE')
        replacer('\Aazk.db.user=SYSDBA', 'azk.db.user=' + config_db[1])
        replacer('\Aazk.db.password=masterkey', 'azk.db.password=' + config_db[2])
        replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                 'azk.db.url=jdbc:oracle:thin:@172.21.10.56:1521:support11')

    replacer('\Aazk.license.name=X:/azk2/bft.lic', 'azk.license.name=bft.lic')


def main(files):
    assert os.getcwd() != dest, 'Wrong path'

    dest_folder = os.path.join(dest, os.path.basename(os.getcwd()))

    if os.path.isdir(dest_folder):
        print('Delete: ', dest_folder)
        rmtree(dest_folder)
    print('Create: ', dest_folder)
    os.makedirs(dest_folder)

    for file in files:
        copy_bar(file, dest_folder)

    os.chdir(dest_folder)
    local_files = os.listdir(os.getcwd())

    client = False
    print(os.getcwd())
    if 'server.zip' in local_files and 'client.zip' in local_files:
        zip_barr('server.zip')
        zip_barr('client.zip', 'client')
    elif 'server.zip' in local_files:
        zip_barr('server.zip')
    elif 'client.zip' in local_files:
        client = True
        zip_barr('client.zip')
        os.remove('client.zip')

    files = os.listdir(os.getcwd())

    if not client:
        print('')
        for file in files:
            if os.path.isdir(file):
                pass
            elif file in need_files:
                pass
            else:
                print('Deleting: ', file)
                os.remove(file)
        edit_config(db)


if __name__ == '__main__':
    try:
        main(files)
    except KeyboardInterrupt:
        raise
