import sqlite3
import cPickle
import os
from random import randint
import string


class Course:
    def __init__(self, name, title, description, category):
        self.category = category
        self.description = description
        self.title = title
        self.name = name


class Module:
    def __init__(self, name, title, clips, author, duration):
        self.duration = duration
        self.author = author
        self.name = name
        self.title = title
        self.clips = clips


class Author:
    def __init__(self, display_name, handle):
        self.handle = handle
        self.display_name = display_name


class Clip:
    def __init__(self, title, duration, index, course_name, author_handle, module_name):
        self.module_name = module_name
        self.author_handle = author_handle
        self.course_name = course_name
        self.index = index
        self.duration = duration
        self.title = title


class Catalogue:
    def __init__(self, database_path):
        if not os.path.exists(database_path):
            database = sqlite3.connect(database_path)

            database.execute('''
                CREATE TABLE cache_status (
                    etag TEXT
                ) ''')
            database.execute('''
                CREATE TABLE auth (
                    token TEXT
                ) ''')
            database.execute('''
                CREATE TABLE author (
                    id INTEGER,
                    handle TEXT,
                    displayname TEXT
                ) ''')
            database.execute('''
                CREATE TABLE course (
                    id INTEGER,
                    name TEXT,
                    title TEXT,
                    category_id INTEGER,
                    description TEXT,
                    level TEXT,
                    duration INTEGER,
                    is_new INTEGER
                ) ''')
            database.execute('''
                CREATE TABLE module (
                    id INTEGER,
                    author INT,
                    name TEXT,
                    title TEXT,
                    duration INT
                ) ''')
            database.execute('''
                CREATE TABLE course_module (
                    course_id INTEGER,
                    module_id INTEGER,
                    PRIMARY KEY(course_id, module_id)
                ) ''')
            database.execute('''
                CREATE TABLE category (
                    id INTEGER,
                    name TEXT
                ) ''')
            database.execute('''
                CREATE TABLE clip (
                    id INTEGER,
                    module_id INT,
                    title TEXT,
                    duration TEXT
                ) ''')
            database.execute('''
                CREATE TABLE search_history (
                    id INTEGER PRIMARY KEY ASC,
                    search_term TEXT
                ) ''')
            database.executescript('''
                 CREATE TRIGGER ten_rows_only AFTER INSERT ON search_history
                       BEGIN
                         DELETE FROM search_history WHERE id <= (
                                            SELECT id FROM search_history
                                            ORDER BY id DESC
                                            LIMIT 10, 1);
                       END;
                 ''')
            database.execute('''
                CREATE TABLE favourite (
                    course_name INT,
                    title TEXT
                ) ''')

            database.commit()
        else:
            database = sqlite3.connect(database_path)
            # Deviations from the original schema should be
            # defined here so that upgrades will work correctly
            database.execute('''
                CREATE TABLE IF NOT EXISTS cookies (
                    cookieblob TEXT
            )''')

        database.row_factory = sqlite3.Row
        self.database = database

    def update(self, etag, data):

        raw_courses = data["Courses"]
        raw_modules = data["Modules"]
        raw_authors = data["Authors"]
        raw_categories = data["Categories"]

        self.database.execute('DELETE FROM cache_status')
        self.database.execute('DELETE FROM category')
        self.database.execute('DELETE FROM course')
        self.database.execute('DELETE FROM clip')
        self.database.execute('DELETE FROM module')
        self.database.execute('DELETE FROM author')
        self.database.execute('DELETE FROM course_module')

        self.database.execute('INSERT INTO cache_status (etag) VALUES(?)', (etag,))

        for author_index,author in enumerate(raw_authors):
            self.database.execute('INSERT INTO author(id,handle, displayname) VALUES(?,?,?)',
                                  (author_index, author["Handle"], author["DisplayName"]))

        for category_index,category in enumerate(raw_categories):
            self.database.execute('INSERT INTO category(id,name) VALUES(?,?)', (category_index,category,))

        for module_index,module in enumerate(raw_modules):
            self.database.execute('INSERT INTO module(id,author, name, title, duration) VALUES(?,?,?,?,?)',
                                           (module_index,int(module["Author"]), module["Name"], module["Title"], module["Duration"]))

            for clip_index, clip in enumerate(module["Clips"]):
                self.database.execute('INSERT INTO clip (id, module_id, title, duration) VALUES(?,?,?,?)',
                                      (clip_index, module_index, clip["Title"], clip["Duration"]))

        for course_index, course in enumerate(raw_courses):
            self.database.execute(
                'INSERT INTO course(id,name, description, category_id, title, level, duration, is_new) VALUES (?,?,?,?,?,?,?,?)',
                (course_index,course["Name"], course["Description"], int(course["Category"]), course["Title"], course["Level"],
                 course["Duration"], course["New"]))

            for module_id in course["Modules"].split(","):
                self.database.execute('INSERT INTO course_module(course_id, module_id) VALUES(?,?)',
                                      (course_index, int(module_id)))

        self.database.commit()

    def update_token(self,token):
        self.database.execute('DELETE FROM auth')
        self.database.execute('INSERT INTO auth(token) VALUES(?)', (token,))
        self.database.commit()
        
    def update_cookies(self,cookies):
        self.database.execute('DELETE FROM cookies')
        self.database.execute('INSERT INTO cookies(cookieblob) VALUES(?)', (cPickle.dumps(cookies), ))
        self.database.commit()

    @property
    def etag(self):
        etag_from_db = self.database.cursor().execute('SELECT etag FROM cache_status').fetchone()
        if etag_from_db is not None:
            return etag_from_db[0]
        return ""

    @property
    def token(self):
        token_from_db = self.database.cursor().execute('SELECT token FROM auth').fetchone()
        if token_from_db is not None:
            return token_from_db[0]
        return ""

    @property
    def courses(self):
        return self.database.cursor().execute('SELECT * FROM course ORDER BY title asc').fetchall()

    @property
    def new_courses(self):
        return self.database.cursor().execute('SELECT * FROM course WHERE is_new = 1').fetchall()

    @property
    def authors(self):
        return self.database.cursor().execute('SELECT * FROM author').fetchall()

    @property
    def categories(self):
        return self.database.cursor().execute('SELECT * FROM category').fetchall()

    @property
    def favourites(self):
        return self.database.cursor().execute('SELECT * FROM favourite').fetchall()
        
    @property
    def cookies(self):
        return cPickle.loads( str( self.database.cursor().execute('SELECT * FROM cookies').fetchall()[0]["cookieblob"] ) )

    @property
    def search_history(self):
        return self.database.cursor().execute('SELECT * FROM search_history ORDER BY id DESC').fetchall()

    def get_course_by_name(self, name):
        return self.database.cursor().execute('SELECT * FROM course WHERE name=?', (name,)).fetchone()

    def get_course_by_id(self, id):
        return self.database.cursor().execute('SELECT * FROM course WHERE id=?', (id,)).fetchone()

    def get_course_by_author_id(self,author_id):
        return self.database.cursor().execute(
            '''SELECT * FROM course
                    INNER JOIN course_module
                        ON course_module.course_id = course.id
                    INNER JOIN module
                        ON course_module.module_id = module.id
                    WHERE module.author = ?
                    GROUP BY course.id
        ''', (author_id,)).fetchall()

    def get_module_by_id(self, id):
        return self.database.cursor().execute('SELECT * FROM module WHERE id=?', (id,)).fetchone()

    def get_modules_by_course_id(self, course_id):
        modules = self.database.cursor().execute('''
                SELECT module.id, module.title FROM module
                    INNER JOIN course_module
                        ON course_module.module_id = module.id
                    WHERE course_module.course_id = ?
            ''', (course_id,)).fetchall()
        return modules

    def get_clips_by_module_id(self,module_id,course_id):
        clips = []
        raw_course = self.database.cursor().execute('SELECT * FROM course WHERE id=?', (course_id,)).fetchone()
        raw_module = self.database.cursor().execute('SELECT * FROM module WHERE id=?', (module_id,)).fetchone()
        raw_author = self.database.cursor().execute('SELECT * FROM author WHERE id=?', (raw_module["author"],)).fetchone()

        raw_clips = self.database.cursor().execute('SELECT * FROM clip WHERE module_id=?', (module_id,)).fetchall()
        for clip in raw_clips:
            clips.append(Clip(clip["title"], clip["duration"] ,clip["id"], raw_course["name"] ,raw_author["handle"], raw_module["name"]))

        return clips

    def get_clip_by_title(self,title,module_name,course_name):
        raw_course = self.database.cursor().execute('SELECT * FROM course WHERE name=?', (course_name,)).fetchone()
        raw_module = self.database.cursor().execute('SELECT * FROM module WHERE name=?', (module_name,)).fetchone()
        raw_author = self.database.cursor().execute('SELECT * FROM author WHERE id=?', (raw_module["author"],)).fetchone()

        clip = self.database.cursor().execute('SELECT * FROM clip WHERE module_id=? and title=?', (raw_module["id"],title,)).fetchone()

        return Clip(clip["title"], clip["duration"] ,clip["id"], raw_course["name"] ,raw_author["handle"], raw_module["name"])

    def get_clip_by_id(self,id,module_name,course_name):
        raw_course = self.database.cursor().execute('SELECT * FROM course WHERE name=?', (course_name,)).fetchone()
        raw_module = self.database.cursor().execute('SELECT * FROM module WHERE name=?', (module_name,)).fetchone()
        raw_author = self.database.cursor().execute('SELECT * FROM author WHERE id=?', (raw_module["author"],)).fetchone()

        clip = self.database.cursor().execute('SELECT * FROM clip WHERE module_id=? and id=?', (raw_module["id"],id,)).fetchone()

        return Clip(clip["title"], clip["duration"] ,clip["id"], raw_course["name"] ,raw_author["handle"], raw_module["name"])


    def get_course_by_title(self, title):
        return self.database.cursor().execute('SELECT * FROM course WHERE title=?', (title,)).fetchone()

    def get_random_course(self):
        max_id = self.database.cursor().execute('SELECT MAX(id) FROM course').fetchone()[0]
        min_id = self.database.cursor().execute('SELECT MIN(id) FROM course').fetchone()[0]
        course_id = randint(min_id,max_id)
        return self.database.cursor().execute('SELECT * FROM course WHERE id =?',(course_id,)).fetchone()


    def get_courses_by_category_id(self, category_id):
        return self.database.cursor().execute('SELECT * FROM course WHERE category_id=? ORDER BY title asc', (category_id,)).fetchall()

    def save_search(self,search_term):
        self.database.execute('INSERT INTO search_history(search_term) VALUES(?)', (search_term,))
        self.database.commit()

    def close_db(self):
        self.database.close()

    @staticmethod
    def add_favourite(course_name, title, database_path):
         database = sqlite3.connect(database_path)
         database.execute('INSERT INTO favourite(course_name, title) VALUES(?,?)',(course_name, title,))
         database.commit()
         database.close()

    @staticmethod
    def remove_favourite(course_name, database_path):
        database = sqlite3.connect(database_path)
        database.execute('DELETE FROM favourite where course_name =?',(course_name,))
        database.commit()
        database.close()

