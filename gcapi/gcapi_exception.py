class GCapiException(Exception):
	def __init__(self, exception):
		super().__init__(exception)
		self.exception = exception

	def _get_field(self, key):
		# Error payloads vary by endpoint (e.g. a 401 ApiErrorResponseDTO has no
		# StatusCode), so missing and empty fields both return None.
		value = self.exception.get(key)
		if value:
			return value
		return None

	def get_exception(self):
		return self.exception

	def get_error_message(self):
		return self._get_field('ErrorMessage')

	def get_status_code(self):
		return self._get_field('StatusCode')

	def get_additional_info(self):
		return self._get_field('AdditionalInfo')

	def get_http_status(self):
		return self._get_field('HttpStatus')

	def get_error_code(self):
		return self._get_field('ErrorCode')
