class User:
    def __init__(self, **fields):
        if 'login' not in fields.keys():
            raise Exception('User class requires "login" field')
        self.__dict__.update(fields)

    def __repr__(self):
        return '<{}>'.format('\n '.join(['{} : {}'.format(k, repr(v))
                                         for k, v in self.__dict__.items()]))

    def is_authenticated(sefl):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.login

