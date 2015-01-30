import models

class User(UserMixin):
	def __init__(self, password = None, active= True, admin = False, name = None):
		self.name = name
		self.password = password
		self.isAdmin = admin
		self.active = active
		self.id = None
	
	def save(self):
		newUser = models.User(name=self.name, password=self.password, admin=self.isAdmin)
		newUser.save()
		self.id = newUser.id
		return self.id

	def get_by_name(self, name):
		dbUser = models.User.objects.get(name=name)
		if dbUser:
			self.email=dbUser.email
			self.active=dbUser.active
			self.password=dbUser.password
			self.isAdmin=dbUser.isAdmin
			return self
		else:
			return None
