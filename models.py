
#Use the hashed password preferably with a salt
class User(db.Document):
    name = db.StringField(unique=True)
    password = db.StringField(default=True)
    isAdmin = db.BooleanField(default=False)
    active = db.BooleanField(default=True)

