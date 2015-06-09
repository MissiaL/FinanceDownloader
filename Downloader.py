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
import ftputil



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
-ftp    : Путь к FTP директории c архивами
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
-------
downloader.exe -s -o AZ_VOLGOBL_20150420 AZ_VOLGOBL_20150420 -ftp /root/dir/azk/
Выкачивает server.zip c FTP. Основной адрес FTP задается
в conf.ini. Следует указать путь только до директории,
относительного основного адреса. Распаковывает, настраивает
Azk2Server.properties под под запуск с БД Oracle
        '''

parser = argparse.ArgumentParser(description='List of commands:', usage=usage)
parser.add_argument('-s', '--server', action='store_const', const=['server.zip'], help='Только server.zip')
parser.add_argument('-c', '--client', action='store_const', const=['client.zip'], help='Только client.zip')
parser.add_argument('-sc', '--sc', action='store_const', const=['server.zip', 'client.zip'],
                    help='Только client.zip и server.zip')
parser.add_argument('-f', '--INTERBASE', nargs='*', help='Путь к БД. Необязательные параметры: логин, пароль')
parser.add_argument('-o', '--ORACLE', nargs=2, help='Логин и пароль от БД')
parser.add_argument('-ftp', '--FTP', nargs=1, help='Путь к директории на FTP')
args = parser.parse_args()
opt = vars(args)

files = ['server.zip']
db = []
ftp_path = None
for command, arguments in opt.items():
    if command in ['server', 'sc', 'client'] and arguments is not None:
        files = arguments
    if command in ['INTERBASE', 'ORACLE'] and arguments is not None:
        db.append(command)
        db = db + arguments
    if command in ['FTP'] and arguments is not None:
        ftp_path = arguments[0]

config = configparser.ConfigParser()
config.read(os.path.join(sys.argv[0][:-14], 'conf.ini'))
try:
    dest = config['PATH']['dir']
    try:
        need_files = config['FILES']['need']
    except:
        need_files = []
    try:
        vcl = config['PATH']['vcl']
    except:
        vcl = False
    try:
        lic = config['PATH']['lic']
    except:
        lic = False
    try:
        host = config['FTP']['host']
    except:
        host = False
    try:
        user = config['FTP']['user']
    except:
        user = False
    try:
        password = config['FTP']['password']
    except:
        password = False
    try:
        azkdburl_orcl = config['Server.properties']['azkdburl_orcl']
    except:
        azkdburl_orcl = False
    try:
        azkdburl_fb = config['Server.properties']['azkdburl_fb']
    except:
        azkdburl_fb = False

except KeyError:
    print('ФАИЛ КОНФИГУРАЦИИ conf.ini НЕ НАЙДЕН!')
    raise

if ftp_path and not host:
    raise Exception('В ФАИЛЕ КОНФИГУРАЦИИ conf.ini НЕ НАЙДЕН параметр host!')
elif ftp_path and not user:
    raise Exception('В ФАИЛЕ КОНФИГУРАЦИИ conf.ini НЕ НАЙДЕН параметр user!')
elif ftp_path and not password:
    raise Exception('В ФАИЛЕ КОНФИГУРАЦИИ conf.ini НЕ НАЙДЕН параметр password!')


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


def ftp_bar(src, dest):
    ftp_host = ftputil.FTPHost(host, user, password)
    ftp_host.chdir(ftp_path)
    print('\nCopying: {0} to {1}'.format(src, dest))
    size = ftp_host.path.getsize(src)
    os.chdir(dest)
    t = threading.Thread(target=ftp_host.download, args=(src, src,))
    t.start()
    tm = 0
    while True:
        if os.path.isfile(os.path.join(dest, src)):
            break
        tm += 1
        time.sleep(0.2)
        if tm == 10:
            break
    widgets = [src + ' ', Percentage(), ' ', Bar(marker=RotatingMarker()),
               ' ', ETA(), ' ', FileTransferSpeed()]
    pbar = ProgressBar(widgets=widgets, maxval=size).start()
    w = 0
    while True:
        try:
            cur_size = os.path.getsize(os.path.join(dest, src))
        except FileNotFoundError:
            w+=1
            time.sleep(0.2)
            if w == 10:
                break
            continue
        pbar.update(cur_size)
        if cur_size == size:
            break
    pbar.finish()


def edit_config(config_db):
    # def replacer(search, replace):
    # print('Replace {0} to {1}'.format(search, replace))
    # for line in fileinput.input(cfg, inplace=True):
    # print(line.replace(search, replace), end='')
    cfg_file = 'Azk2Server.properties'

    def replacer(re_search, replace):
        cfg = open(cfg_file, "r")
        regex = re.compile(re_search)
        for line in cfg:
            if regex.search(line):
                print(line)
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
        try:
            replacer('\A#azk.db.accessmode=INTERBASE', 'azk.db.accessmode=INTERBASE')
        except:
            #planing
            replacer('\Aazk.db.accessmode=INTERBASE', 'azk.db.accessmode=INTERBASE')
        if path:
            if azkdburl_fb:
                replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                         azkdburl_fb + ':' + path)
            else:
                replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                         'azk.db.url=jdbc:firebirdsql:127.0.0.1/3050' + ':' + path)
        if login:
            replacer('\Aazk.db.user=SYSDBA', 'azk.db.user=' + login)
        if pwd:
            replacer('\Aazk.db.password=masterkey', 'azk.db.password=' + pwd)

    if db_name == 'ORACLE':
        try:
            replacer('\A#azk.db.accessmode=ORACLE', 'azk.db.accessmode=ORACLE')
        except:
            #planing
            replacer('\Aazk.db.accessmode=INTERBASE', 'azk.db.accessmode=ORACLE')
        replacer('\Aazk.db.user=SYSDBA', 'azk.db.user=' + config_db[1])
        replacer('\Aazk.db.password=masterkey', 'azk.db.password=' + config_db[2])
        if azkdburl_orcl:
            replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                     azkdburl_orcl)
        else:
            replacer('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1',
                     'azk.db.url=jdbc:oracle:thin:@172.21.10.56:1521:support11')
    try:
        replacer('\Aazk.license.name=X:/azk2/bft.lic', 'azk.license.name=bft.lic')
    except:
        #planing
        replacer('\Aazk.license.name=X:/azk2/for_build/bft.lic', 'azk.license.name=bft.lic')


def copy_vcl(client=None):
    path = os.path.join(os.getcwd(), 'client')
    if client:
        path = os.getcwd()
    vcl_source = os.listdir(vcl)
    for vcl_files in vcl_source:
        vcl_full_name = os.path.join(vcl, vcl_files)
        print('Copy {0} to {1}'.format(vcl_full_name, path))
        copy(vcl_full_name, path)


def main(files):
    if not ftp_path:
        assert os.getcwd() != dest, 'Недопустимый путь'

    if ftp_path:
        dest_folder = os.path.join(dest, os.path.basename(os.path.normpath(ftp_path)))
    else:
        dest_folder = os.path.join(dest, os.path.basename(os.getcwd()))

    if os.path.isdir(dest_folder):
        print('Delete: ', dest_folder)
        rmtree(dest_folder)
    print('Create: ', dest_folder)
    os.makedirs(dest_folder)

    # Копирование
    for file in files:
        if ftp_path:
            ftp_bar(file, dest_folder)
        else:
            copy_bar(file, dest_folder)

    os.chdir(dest_folder)
    local_files = os.listdir(os.getcwd())

    client = False
    print(os.getcwd())
    if 'server.zip' in local_files and 'client.zip' in local_files:
        zip_barr('server.zip')
        zip_barr('client.zip', 'client')
        if vcl:
            copy_vcl()
    elif 'server.zip' in local_files:
        zip_barr('server.zip')
    elif 'client.zip' in local_files:
        client = True
        zip_barr('client.zip')
        os.remove('client.zip')
        if vcl:
            copy_vcl(client=True)

    files = os.listdir(os.getcwd())
    if lic:
        lic_name = os.path.basename(lic)
        if lic_name not in files:
            print('Copy bft.lic to {0}'.format(os.getcwd()))
            copy(lic, os.getcwd())

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
