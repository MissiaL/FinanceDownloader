import subprocess
import re
import sys
import os
import logging

def create():
    #os.chdir('E:\\AZK\\1578\\2.36.0.101')
    logging.info('Запускаем операцию создания эталона БД')
    config_folder = os.getcwd()
    # Название папки - это имя пользователя azk.db.user
    folder_path = os.getcwd().split('\\')
    folder_name = folder_path[len(folder_path) - 1]

    azk_db_user = 'azk.db.user=ET_' + folder_name.replace('.', '_') + '\n'
    azk_db_password = 'azk.db.password=ET_' + folder_name.replace('.', '_') + '\n'
    azk_db_sysuser = 'azk.db.sysuser=SYS\n'
    azk_db_syspassword = 'azk.db.syspassword=.........\n'

    db_name = None
    db_url = None
    with open('Azk2Server.properties', 'r') as azk:
        lines = []
        regex_db_name = re.compile('azk.db.accessmode=ORACLE')
        regex_db_url = re.compile('\Aazk.db.url')
        config = azk.readlines()
        for line in config:
            if regex_db_name.search(line):
                db_name = line.split('=')[1].strip()
            if regex_db_url.search(line):
                db_url = line.split('=')[1].strip()
            lines.append(line)

    if db_name is None:
        logging.info('Не удалось определить режим работы с базой данных!')
        sys.exit(1)

    if db_url is None:
        logging.info('Не удалось определить путь к базе данных!')
        sys.exit(1)

    if db_url != 'jdbc:oracle:thin:@x3-server:1521:support11' or db_url != 'jdbc:oracle:thin:@172.21.10.56:1521:support11':
        logging.warning('Возможно путь к базе данных неверный! Создание эталона может прекратиться!')

    # Правим конфиг
    logging.info('Изменяем Azk2Server.properties для создания эталона БД')
    with open('Azk2Server.properties', 'w') as azk:
        regex_user = re.compile('\Aazk.db.user')
        regex_password = re.compile('\Aazk.db.password')
        regex_sysuser = re.compile('azk.db.sysuser')
        regex_syspassword = re.compile('azk.db.syspassword')
        for line in lines:
            if regex_user.search(line):
                azk.write('')
                continue
            if regex_password.search(line):
                azk.write('')
                continue
            azk.write(line)
        logging.info('Записываем в конфиг {0}'.format(azk_db_user))
        azk.write(azk_db_user)
        logging.info('Записываем в конфиг {0}'.format(azk_db_password))
        azk.write(azk_db_password)
        logging.info('Записываем в конфиг {0}'.format(azk_db_sysuser))
        azk.write(azk_db_sysuser)
        logging.info('Записываем в конфиг {0}'.format(azk_db_syspassword))
        azk.write(azk_db_syspassword)

    SQL = os.path.join(os.getcwd(), 'SQL')
    os.chdir(SQL)

    # SQL\executer.cmd create_user
    logging.info('Запускаем executer.cmd create_user')
    subprocess.call(['executer.cmd', 'create_user'], cwd=SQL, shell=True)

    if os.path.isfile('grant_user.sql'):
        os.remove('grant_user.sql')

    # Создадим sql файл
    logging.info('Создаем grant_user.sql')
    with open('grant_user.sql', 'w') as grant_sql:
        text = '''--oracle
grant select on v_$locked_object to ET_{0}
               ''' .format(folder_name.replace('.', '_') )
        grant_sql.write(text)

    os.chdir(config_folder)
    # Правим конфиг для выдачи гранта пользователю
    logging.info('Изменяем Azk2Server.properties для запуска sql.cmd grant_user.sql')
    with open('Azk2Server.properties', 'r') as azk:
        lines = []
        config = azk.readlines()
        for line in config:
            lines.append(line)
    with open('Azk2Server.properties', 'w') as azk:
        for line in lines:
            if regex_sysuser.search(line):
                logging.info('Записываем в конфиг azk.db.user=SYS AS SYSDBA')
                azk.write('azk.db.user=SYS AS SYSDBA\n')
                continue
            azk.write(line)

    # Выполняем SQL\sql.cmd grant_user.sql
    logging.info('Выполняем sql.cmd grant_user.sql')
    subprocess.call(['sql.cmd', 'grant_user.sql'], cwd=SQL, shell=True)

    # Правим конфиг
    logging.info('Изменяем Azk2Server.properties для запуска executer.cmd -site 0 perform_all perform.lst')
    with open('Azk2Server.properties', 'w') as azk:
        logging.info('Удаляем azk.db.user=SYS AS SYSDBA')
        logging.info('Записываем в конфиг {0}'.format(azk_db_sysuser))
        for line in lines:
            azk.write(line)

    # Выполняем команду SQL\executer.cmd -site 0 perform_all perform.lst
    logging.info('Выполняем executer.cmd -site 0 perform_all perform.lst')
    subprocess.call(['executer.cmd', '-site', '0', 'perform_all', 'perform.lst'], cwd=SQL, shell=True)

    # Удаляем из конфига sys пользователя
    logging.info('Изменяем Azk2Server.properties')
    with open('Azk2Server.properties', 'r') as azk:
        lines = []
        config = azk.readlines()
        for line in config:
            lines.append(line)
    with open('Azk2Server.properties', 'w') as azk:
        for line in lines:
            if regex_sysuser.search(line):
                logging.info('Удаляем из конфига {0}'.format(azk_db_sysuser))
                azk.write('')
                continue
            if regex_syspassword.search(line):
                logging.info('Удаляем из конфига {0}'.format(azk_db_password))
                azk.write('')
                continue
            azk.write(line)