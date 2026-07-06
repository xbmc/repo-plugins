import requests


class AudioBookShelfService:
	def __init__(self, base_url):
		self.base_url = base_url

	def login(self, username, password):
		url = f"{self.base_url}/login"
		payload = {
			"username": username,
			"password": password
		}
		data = self._post(url, payload, extra_headers={"x-return-tokens": "true"})
		user = data.get("user", {}) or {}
		access_token = data.get("accessToken") or user.get("accessToken")
		refresh_token = data.get("refreshToken") or user.get("refreshToken")
		if not access_token:
			raise ValueError("Server did not return an accessToken. Audiobookshelf 2.26.0+ is required.")
		return {
			"user": user,
			"accessToken": access_token,
			"refreshToken": refresh_token,
		}

	def refresh(self, refresh_token):
		url = f"{self.base_url}/auth/refresh"
		headers = {"x-refresh-token": refresh_token, "x-return-tokens": "true"}
		data = self._post(url, payload=None, extra_headers=headers)
		user = data.get("user", {}) or {}
		access_token = data.get("accessToken") or user.get("accessToken")
		new_refresh_token = data.get("refreshToken") or user.get("refreshToken") or refresh_token
		if not access_token:
			raise ValueError("Refresh did not return an accessToken")
		return {
			"user": user,
			"accessToken": access_token,
			"refreshToken": new_refresh_token,
		}

	def logout(self, access_token=None, socketId=None):
		url = f"{self.base_url}/logout"
		payload = {}
		if socketId:
			payload["socketId"] = socketId
		headers = {}
		if access_token:
			headers["Authorization"] = f"Bearer {access_token}"
		self._post(url, payload, extra_headers=headers)

	def server_status(self):
		url = f"{self.base_url}/status"
		return self._get(url)

	def ping(self):
		url = f"{self.base_url}/ping"
		return self._get(url)

	def healthcheck(self):
		url = f"{self.base_url}/healthcheck"
		self._get(url)

	def _post(self, url, payload=None, extra_headers=None):
		headers = {"Content-Type": "application/json"}
		if extra_headers:
			headers.update(extra_headers)
		response = requests.post(url, headers=headers, json=payload)
		response.raise_for_status()
		return response.json()

	def _get(self, url):
		response = requests.get(url)
		response.raise_for_status()
		return response.json()
