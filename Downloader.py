__author__ = 'MissiaL'

import os
from shutil import copy, rmtree
import threading
import time
import zipfile
import argparse
import sys
import configparser
from progressbar import Bar, ETA, FileTransferSpeed, Percentage, ProgressBar, RotatingMarker
import ftputil
import etalon
import logging
import replacer

root = logging.getLogger()
root.setLevel(logging.DEBUG)
hdlr = logging.FileHandler(os.path.join(sys.argv[0][:-14], 'downloader.log'))
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
hdlr.setFormatter(formatter)
ch.setFormatter(formatter)
root.addHandler(ch)
root.addHandler(hdlr)

usage = '''downloader.exe [option] ... [-s | -c | -sc ] ... [-f | -o ] ... [-et] ... [-p] ... [arg]
Скрипт выкачивает с текущей папки архивы, создает необходимые директории
и распаковывает в папку, указанную в конфигурационном файле.
Оставляет все папки и файлы, указанные в конфигурационном файле.
Все действия пишутся в downloader.log в корневую папку.

Основные параметры:
-sc     : Выкачивание сервера и клиента
-s      : Выкачивание сервера
-c      : Выкачивание клиента
Дополнительные параметры:
-f      : Тип БД Firebird. Необходимо указать путь к БД
-o      : Тип БД Oracle. Так же необходимо указать
          логин и пароль к БД
-ftp    : Путь к FTP директории c архивами
-et     : Создать эталон БД
-p      : Путь, куда нужно выкачивать сборку
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
-------
downloader.exe -et
Создать эталон БД. Имя эталона берется из имени папки.
Пароль аналогичен. Аргумент создает скрипт grant_user.sql
в папке SQL для выдачи гранта.
        '''

if len(sys.argv) < 2:
    print(usage)
    sys.exit(0)

parser = argparse.ArgumentParser(description='List of commands:', usage=usage)
parser.add_argument('-s', '--server', action='store_const', const=['server.zip'], help='Только server.zip')
parser.add_argument('-c', '--client', action='store_const', const=['client.zip'], help='Только client.zip')
parser.add_argument('-sc', '--sc', action='store_const', const=['server.zip', 'client.zip'],
                    help='Только client.zip и server.zip')
parser.add_argument('-f', '--INTERBASE', nargs=1, help='Путь к БД. Логин и пароль: SYSDBA, MASTERKEY')
parser.add_argument('-o', '--ORACLE', nargs=2, help='Логин и пароль от БД')
parser.add_argument('-ftp', '--FTP', nargs=1, help='Путь к директории на FTP')
parser.add_argument('-et', '--ET', action='store_true', help='Создать эталон БД')
parser.add_argument('-p', '--P', nargs=1, help='Путь, куда нужно выкачивать сборку')
args = parser.parse_args()
opt = vars(args)

files = None
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

if not os.path.isfile(os.path.join(sys.argv[0][:-14], 'conf.ini')):
    logging.error('Файл конфигурации не найден')
    sys.exit(1)

config = configparser.ConfigParser()
config.read(os.path.join(sys.argv[0][:-14], 'conf.ini'))

if config.has_option('PATH', 'home'):
    home = config['PATH']['home']
else:
    home = args.P[0]
if config.has_option('PATH', 'vcl'):
    vcl = config['PATH']['vcl']
else:
    vcl = False
if config.has_option('PATH', 'lic'):
    lic = config['PATH']['lic']
else:
    lic = False
if config.has_option('FILES', 'need'):
    need = config['FILES']['need']
else:
    need = []

if config.has_option('FTP', 'host'):
    host = config['FTP']['host']
else:
    host = False
if config.has_option('FTP', 'user'):
    user = config['FTP']['user']
else:
    user = False
if config.has_option('FTP', 'password'):
    password = config['FTP']['password']
else:
    password = False


if ftp_path and not host:
    logging.error('Указан аргумент -ftp, но файле конфигурации отсутствует параметр host')
    sys.exit(1)
elif ftp_path and not user:
    logging.error('Указан аргумент -ftp, но файле конфигурации отсутствует параметр user')
    sys.exit(1)
elif ftp_path and not password:
    logging.error('Указан аргумент -ftp, но файле конфигурации отсутствует параметр password')
    sys.exit(1)


def zip_barr(file, folder=None):
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


def copy_bar(src, home):
    logging.info('Копирование %s в %s', src, home)
    size = os.path.getsize(src)
    t = threading.Thread(target=copy, args=(src, home,))
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


def ftp_bar(src, home):
    ftp_host = ftputil.FTPHost(host, user, password)
    ftp_host.chdir(ftp_path)
    logging.info('Копирование %s to %s', src, home)
    size = ftp_host.path.getsize(src)
    os.chdir(home)
    t = threading.Thread(target=ftp_host.download, args=(src, src,))
    t.start()
    tm = 0
    while True:
        if os.path.isfile(os.path.join(home, src)):
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
            cur_size = os.path.getsize(os.path.join(home, src))
        except FileNotFoundError:
            w += 1
            time.sleep(0.2)
            if w == 10:
                break
            continue
        pbar.update(cur_size)
        if cur_size == size:
            break
    pbar.finish()


def edit_config(config_db):
    replacer.edit_cfg(config_db)

def copy_vcl(client=None):
    path = os.path.join(os.getcwd(), 'client')
    if client:
        path = os.getcwd()
    vcl_source = os.listdir(vcl)
    for vcl_files in vcl_source:
        vcl_full_name = os.path.join(vcl, vcl_files)
        logging.info('Копирование %s в %s', vcl_full_name, path)
        copy(vcl_full_name, path)


def main(files):
    if files is not None:
        logging.info('-' * 60)
        logging.info('Старт работы')
        if not ftp_path:
            assert os.getcwd() != home, 'Недопустимый путь. Возможно необходимо проверить путь запуска утилиты!'

        if ftp_path:
            dest_folder = os.path.join(home, os.path.basename(os.path.normpath(ftp_path)))
        else:
            dest_folder = os.path.join(home, os.path.basename(os.getcwd()))

        if os.path.isdir(dest_folder):
            logging.info('Удаление: %s', dest_folder)
            rmtree(dest_folder)
        logging.info('Создание: %s', dest_folder)
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
        logging.info(os.getcwd())
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
                logging.info('Копирование bft.lic в %s', os.getcwd())
                copy(lic, os.getcwd())

        if not client:
            for file in files:
                if os.path.isdir(file):
                    pass
                elif file in need:
                    pass
                else:
                    logging.info('Удаление %s', file)
                    os.remove(file)
            edit_config(db)

        if args.ET:
            etalon.create()

    if args.ET:
        etalon.create()


if __name__ == '__main__':
    try:
        main(files)
    except KeyboardInterrupt:
        raise
