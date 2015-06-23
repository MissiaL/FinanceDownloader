import re
import logging
import configparser
import os
import sys

config = configparser.ConfigParser()
config.read(os.path.join(sys.argv[0][:-14], 'conf.ini'))
if config.has_option('Server.properties', 'azkdburl_orcl'):
    azkdburl_orcl = config['Server.properties']['azkdburl_orcl']
else:
    azkdburl_orcl = None
if config.has_option('Server.properties', 'azkdburl_fb'):
    azkdburl_fb = config['Server.properties']['azkdburl_fb']
else:
    azkdburl_fb = None


regex_db = re.compile('\A#azk.db.accessmode=ORACLE')
regex_db_interbase = re.compile('\A#azk.db.accessmode=INTERBASE')
regex_db_planing = re.compile('\Aazk.db.accessmode=INTERBASE')
regex_db_user = re.compile('\Aazk.db.user=SYSDBA')
regex_db_password = re.compile('\Aazk.db.password=masterkey')
regex_db_url = re.compile('\Aazk.db.url=jdbc:firebirdsql:127.0.0.1')
regex_db_lic = re.compile('\Aazk.license.name=')


cfg_name = 'Azk2Server.properties'
# arg = ['ORACLE', 'AZ_ROSTOVOBL_20150203', 'AZ_ROSTOVOBL_20150203']
def edit_cfg(arg):
    with open(cfg_name, 'r') as azk:
        lines = [line for line in azk.readlines()]
    logging.info('Изменяем %s', cfg_name)
    if arg:
        db = arg[0]
        if db == 'ORACLE':
            login = arg[1]
            password = arg[2]
            with open(cfg_name, 'w') as azk:
                for line in lines:
                    if regex_db.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.db.accessmode=ORACLE')
                        azk.write('azk.db.accessmode=ORACLE\n')
                        continue
                    # Если сборка АЦК-Планирование
                    elif regex_db_planing.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.db.accessmode=ORACLE')
                        azk.write('azk.db.accessmode=ORACLE\n')
                        continue
                    if regex_db_url.search(line):
                        if azkdburl_orcl is not None:
                            logging.info('Заменяем %s на %s', line.strip(), 'azk.db.url=' + azkdburl_orcl)
                            azk.write('azk.db.url=' + azkdburl_orcl + '\n')
                            continue
                        else:
                            logging.info('Заменяем %s на %s', line.strip(), 'azk.db.url=jdbc:oracle:thin:@172.21.10.56:1521:support11')
                            azk.write('azk.db.url=jdbc:oracle:thin:@172.21.10.56:1521:support11\n')
                            continue
                    if regex_db_user.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.db.user=' + login)
                        azk.write('azk.db.user=' + login + '\n')
                        continue
                    if regex_db_password.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.db.password=' + password)
                        azk.write('azk.db.password=' + password + '\n')
                        continue
                    if regex_db_lic.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.license.name=bft.lic')
                        azk.write('azk.license.name=bft.lic' + '\n')
                        continue
                    azk.write(line)

        elif db == 'INTERBASE':
            path = arg[1].replace('\\', '/')
            with open(cfg_name, 'w') as azk:
                for line in lines:
                    if regex_db_interbase.search(line) or regex_db_planing.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.db.accessmode=INTERBASE')
                        azk.write('azk.db.accessmode=INTERBASE' + '\n')
                        continue
                    if regex_db_url.search(line):
                        if azkdburl_fb is not None:
                            logging.info('Заменяем %s на %s', line.strip(), 'azk.db.url=' + azkdburl_fb + ':' + path)
                            azk.write('azk.db.url=' + azkdburl_fb + ':' + path + '\n')
                            continue
                        else:
                            logging.info('Заменяем %s на %s', line.strip(), 'azk.db.url=jdbc:firebirdsql:127.0.0.1/3050' + ':' + path)
                            azk.write('azk.db.url=jdbc:firebirdsql:127.0.0.1/3050' + ':' + path + '\n')
                            continue
                    if regex_db_lic.search(line):
                        logging.info('Заменяем %s на %s', line.strip(), 'azk.license.name=bft.lic')
                        azk.write('azk.license.name=bft.lic' + '\n')
                        continue
                    azk.write(line)
    else:
        with open(cfg_name, 'w') as azk:
            for line in lines:
                if regex_db_lic.search(line):
                    logging.info('Заменяем %s на %s', line.strip(), 'azk.license.name=bft.lic')
                    azk.write('azk.license.name=bft.lic' + '\n')
                    continue
                azk.write(line)