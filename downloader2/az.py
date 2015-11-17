import os
from configparser import ConfigParser
import argparse

def azkload():

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



