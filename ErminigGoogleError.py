# vi:si:noet:sw=4:sts=4:ts=8

class ErminigGoogleError(Exception):
	def __init__(self, raw_data):
		self.raw_data = raw_data
		self.err_code = raw_data[0]['status']

	def __str__(self):
		return repr(self.raw_data)

	def title(self):
		if self.err_code == 401:
			return "Invalid username or password"
		elif self.err_code == 403:
			return "Access forbidden."
		else:
			return "Unknown error %s" % self.err_code

	def description(self):
		if self.err_code == 401:
			return "The username or password for the Google service is invalid. Please check in Erminig settings if everything is correct."
		elif self.err_code == 403:
			return "You don't have permissions to access one of the calendars, or perhaps it has been deleted."
		else:
			return self.raw_data[0]['body']
