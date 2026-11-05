from typing import Any


class GCapiException(Exception):
	def __init__(self, exception: dict[str, Any]) -> None:
		super().__init__(exception)
		self.exception = exception

	def _get_field(self, key: str) -> Any:
		# Error payloads vary by endpoint (e.g. a 401 ApiErrorResponseDTO has no
		# StatusCode), so missing and empty fields both return None.
		value = self.exception.get(key)
		if value:
			return value
		return None

	def get_exception(self) -> dict[str, Any]:
		return self.exception

	def get_error_message(self) -> str | None:
		return self._get_field('ErrorMessage')

	def get_status_code(self) -> int | None:
		return self._get_field('StatusCode')

	def get_additional_info(self) -> Any:
		return self._get_field('AdditionalInfo')

	def get_http_status(self) -> int | None:
		return self._get_field('HttpStatus')

	def get_error_code(self) -> int | None:
		return self._get_field('ErrorCode')
