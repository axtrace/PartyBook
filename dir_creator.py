import os


class DirCreator(object):
    path_for_save = ''

    def __init__(self, path_for_save=''):
        self.path_for_save = path_for_save

    def create_directory_if_no_exist(self):
        try:
            os.makedirs(self.path_for_save)
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise
