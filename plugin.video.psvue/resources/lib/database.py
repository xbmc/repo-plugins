import sqlite3
from globals import *


class Database:
    db_path = os.path.join(SAVE_LOCATION, 'epg.db')
    xml_path = os.path.join(SAVE_LOCATION, 'epg.xml')
    db_copy = os.path.join(COPY_LOCATION, 'epg.db')
    xml_copy = os.path.join(COPY_LOCATION, 'epg.xml')
    date_format = "%Y%m%d%H%M%S"

    def __init__(self):
        if not xbmcvfs.exists(self.db_path):
            # Create db file if it doesn't exist
            open(self.db_path, 'a').close()

        db_connection = sqlite3.connect(self.db_path)

        sql = 'create table if not exists epg (' \
            'StartTime integer,' \
            'EndTime integer,' \
            'Channel integer,' \
            'Title text,' \
            'TitleSub text,' \
            'Desc text,' \
            'Icon text,' \
            'Genre text,' \
            'PRIMARY KEY (StartTime, EndTime, Channel)' \
            ')'
        db_connection.execute(sql)

        sql = 'create table if not exists channels (' \
            'Id integer,' \
            'Title text,' \
            'Logo text,' \
            'SortOrder integer,' \
            'PRIMARY KEY (Id)' \
            ')'
        db_connection.execute(sql)

        db_connection.commit()
        db_connection.close()

    def get_last_start_time(self):
        last_start = ''
        db_connection = sqlite3.connect(self.db_path)
        cursor = db_connection.cursor()
        cursor.execute('select StartTime from epg order by StartTime desc limit 1')
        last_start = cursor.fetchone()
        db_connection.close()
        if last_start:
            last_start = string_to_date(last_start[0], self.date_format)

        return last_start

    def update_epg_info(self, program_list):
        db_connection = sqlite3.connect(self.db_path)
        db_connection.executemany('replace into epg (StartTime, EndTime, Channel, Title, TitleSub, Desc, Icon, Genre) '
                                  'values (?,?,?,?,?,?,?,?)', program_list)
        db_connection.commit()
        db_connection.close()

    def clean_db_epg(self):
        db_connection = sqlite3.connect(self.db_path)
        now = ((datetime.utcnow() - timedelta(hours=1)).strftime('%Y%m%d%H%M%S'),)
        db_connection.execute('delete from epg where endtime < ?', now)
        db_connection.commit()

    def set_db_channels(self, channel_list):
        db_connection = sqlite3.connect(self.db_path)
        db_connection.executemany('replace into channels (Id, Title, Logo, SortOrder) values (?,?,?,?)', channel_list)
        db_connection.commit()
        db_connection.close()

    def get_db_channels(self):
        channels = []
        db_connection = sqlite3.connect(self.db_path)
        db_cursor = db_connection.cursor()
        db_cursor.execute('select * from channels order by SortOrder asc')
        for row in db_cursor:
            id = str(row[0])
            title = str(row[1].encode('utf-8'))
            logo = str(row[2])

            channels.append([id, title, logo])
        db_connection.close()

        return channels

    def build_epg_xml(self):
        xbmc.log('BuildGuide: Building master file...')
        db_connection = sqlite3.connect(self.db_path)
        db_cursor = db_connection.cursor()

        master_file = open(self.xml_path, 'w')
        master_file.write('<?xml version="1.0" encoding="utf-8" ?>\n')
        master_file.write("<tv>\n")

        channels = self.get_db_channels()
        for channel_id, title, logo in channels:
            master_file.write('<channel id="' + channel_id + '">\n')
            master_file.write('    <display-name lang="en">' + title + '</display-name>\n')
            master_file.write('</channel>\n')

        db_cursor.execute("select * from epg")
        for row in db_cursor:
            start_time = str(row[0])
            stop_time = str(row[1])
            channel_id = str(row[2])
            title = row[3]
            sub_title = row[4]
            desc = row[5]
            icon = row[6]
            genres = row[7]
            genres = genres.split(',')

            prg = ''
            prg += '<programme start="' + start_time + '" stop="' + stop_time + '" channel="' + channel_id + '">\n'
            prg += '    <title lang="en">' + title.encode('utf-8') + '</title>\n'
            prg += '    <sub-title lang="en">' + sub_title.encode('utf-8') + '</sub-title>\n'
            prg += '    <desc lang="en">' + desc.encode('utf-8') + '</desc>\n'
            for item in genres:
                genre = item.encode('utf-8')
                prg += '    <category lang="en">' + genre.encode('utf-8') + '</category>\n'
            prg += '    <icon src="' + icon.encode('utf-8') + '"/>\n'
            prg += '</programme>\n'

            master_file.write(prg)

        master_file.write('</tv>')
        master_file.close()
        # Copy xml file to specified location from settings
        if ADDON.getSetting(id='custom_directory') == 'true':
            xbmc.log("Copying XML file... ")
            xbmcvfs.copy(self.xml_path, self.xml_copy)
            xbmc.log("COPIED XML file!!! ")
        db_connection.close()
        xbmc.log('BuildGuide: Master file built.')

        check_iptv_setting('epgPath', self.xml_path)
        # Copy db file to specified location from settings
        if ADDON.getSetting(id='custom_directory') == 'true':
            xbmc.log("Copying DataBase file... ")
            xbmcvfs.copy(self.db_path, self.db_copy)
            xbmc.log("COPIED DataBase file!!! ")
