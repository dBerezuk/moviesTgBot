import pymysql
import config

class Db():

    def __init__(self):
        """Подлючение к бд и сохрание курсора соединения"""
        self.con = pymysql.connect(
            host=config.HOST,
            port=config.PORT,
            user=config.USER,
            password=config.PASSWORD,
            database=config.DATABASE,

        )
        self.cur = self.con.cursor()

    def searchMovies(self, code):
        """Поиск фильма по коду"""
        self.cur.execute('SELECT * FROM allmovies WHERE code = \'%s\'' % code)
        return self.cur.fetchall()

    def listOfMovies(self):
        """Список фильмов"""
        self.cur.execute('SELECT * FROM allmovies')
        listMovies = ''
        for movie in self.cur.fetchall():
            listMovies += f'id: {movie[0]} | название: {movie[1]} | код: {movie[2]}\n------------\n'
        return listMovies

    def addMovie(self, title, code):
        """Добавление фильма"""
        # проверка существует ли уже фильм с таким кодом
        self.cur.execute('SELECT code FROM allmovies WHERE code = \'%s\'' % code)
        validate = self.cur.fetchall()
        if len(validate) >= 1:
            return f'Фильм с таким кодом {code} уже добавлен.\nПопробуйте еще раз добавить фильм с другим кодом'
        # добавление
        self.cur.execute('INSERT INTO allmovies (title, code) VALUES(\'' + title + '\',\'' + code + '\')')
        self.con.commit()
        return f'Фильм добавлен: (код: {code})'

    def removeMovie(self, code):
        """Удаление фильма"""
        result = self.cur.execute('DELETE FROM allmovies WHERE code =  \'%s\'' % code)
        self.con.commit()
        if result == 0:
            return f'Фильм не найден по коду: {code}'
        else:
            return f'Фильм удален'

    def editMovice(self, new_title, new_code, code):
        """Редактирование данных"""
        self.cur.execute('UPDATE allmovies SET title=\'' + new_title + '\',code=\'' + new_code + '\' WHERE code = \'' + code + '\'')
        self.con.commit()
        return f'Данные о фильме обновлены (Название: {new_title}, Код: {new_code})'


    def close(self):
        """Закрытие соединение с БД"""
        self.cur.close()
        self.con.close()

