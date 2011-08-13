# vi:si:noet:sw=4:sts=4:ts=8

import consts

class ErminigError(Exception):
	def __init__(self, err_id):
		self.err_id = err_id

	def title(self):
		if self.err_id == consts.INVALID_USER_PWD:
			return "Invalid username or password"
		if self.err_id == consts.NO_INET_CONNECTION:
			return "Cannot connect to Google"
		else:
			return "Unknown error %s" % self.err_id

	def description(self):
		if self.err_id == consts.INVALID_USER_PWD:
			return "The username or password for the Google service is invalid. Please check in Erminig settings if everything is correct."
		if self.err_id == consts.NO_INET_CONNECTION:
			return "Unable to connect to Google. Please check your Internet connection"
		else:
			return ""
