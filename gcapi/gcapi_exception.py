class GCapiException(Exception):
	def __init__(self, exception):
		self.exception = exception

	def get_exception(self):
		return self.exception

	def get_error_message(self):
		if self.exception['ErrorMessage']:
			return self.exception['ErrorMessage']

	def get_status_code(self):
		if self.exception['StatusCode']:
			return self.exception['StatusCode']

	def get_additional_info(self):
		if self.exception['AdditionalInfo']:
			return self.exception['AdditionalInfo']

	def get_http_status(self):
		if self.exception['HttpStatus']:
			return self.exception['HttpStatus']

	def get_error_code(self):
		if self.exception['ErrorCode']:
			return self.exception['ErrorCode']
