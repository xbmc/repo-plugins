import urllib.request, urllib.parse, urllib.error
import json
import time
import socket
from typing import Any, Optional, Dict

import xbmc


def buildUrl(query, base_url):
    return base_url + '?' + urllib.parse.urlencode(query)


class NetworkError(Exception):
    """Custom exception for network-related errors"""
    pass


def getJsonData(apiUrl: str, max_retries: int = 2, retry_delay: int = 1) -> Dict[str, Any]:
    """
    Fetch JSON data from a URL with retry logic and proper error handling.

    Args:
        apiUrl: The URL to fetch data from
        max_retries: Maximum number of retry attempts (default: 3)
        retry_delay: Delay between retries in seconds (default: 2)

    Returns:
        Dict containing the parsed JSON data

    Raises:
        NetworkError: If all retry attempts fail or other network issues occur
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(apiUrl, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    return json.loads(response.read().decode('utf-8'))
                else:
                    raise NetworkError(f"Server returned status code: {response.status}")

        except (urllib.error.URLError, socket.error) as e:
            is_last_attempt = attempt == max_retries - 1
            error_msg = f"Network error on attempt {attempt + 1}/{max_retries}: {str(e)}"

            if is_last_attempt:
                raise NetworkError(f"Failed to fetch data after {max_retries} attempts: {str(e)}")
            else:
                xbmc.log(error_msg, xbmc.LOGERROR)  # Log the error
                time.sleep(retry_delay)  # Wait before retrying

        except json.JSONDecodeError as e:
            raise NetworkError(f"Failed to parse JSON response: {str(e)}")

        except Exception as e:
            raise NetworkError(f"Unexpected error while fetching data: {str(e)}")


def safe_request(url: str) -> Optional[str]:
    """
    Make a safe HTTP request that handles common network errors

    Args:
        url: The URL to request

    Returns:
        Optional[str]: The response content if successful, None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        xbmc.log(f"Error making request to {url}: {str(e)}", xbmc.LOGERROR)
        return None