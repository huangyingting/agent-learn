import requests
from bs4 import BeautifulSoup
import urllib.parse
import datetime
import pytz

# Define a simple web search tool using DuckDuckGo without API key
def web_search(query: str) -> str:
  """Search the web for information using DuckDuckGo.
  
  Args:
      query: A string containing the search query to look up online
      
  Returns:
      A string containing the top search results
  """
  try:
    # URL encode the query for use in the URL
    encoded_query = urllib.parse.quote_plus(query)

    # Create headers to simulate a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    # Make request to DuckDuckGo HTML search
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
      return f"Search failed with status code {response.status_code}"

    # Parse the HTML response
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract search results
    results = []
    result_elements = soup.select('.result')[:3]  # Get first 3 results

    if not result_elements:
      return "No search results found or page format has changed."

    for result in result_elements:
      title_elem = result.select_one('.result__title')
      snippet_elem = result.select_one('.result__snippet')
      link_elem = result.select_one('.result__url')

      title = title_elem.get_text(strip=True) if title_elem else "No title"
      snippet = snippet_elem.get_text(
          strip=True) if snippet_elem else "No description"

      # Extract href and clean it
      if link_elem:
        link = link_elem.get_text(strip=True)
      else:
        link_anchor = title_elem.select_one('a') if title_elem else None
        link = link_anchor.get('href', "No link") if link_anchor else "No link"
        # DuckDuckGo sometimes uses redirects
        if link.startswith('/'):
          link = "https://duckduckgo.com" + link

      results.append(f"Title: {title}\nSnippet: {snippet}\nLink: {link}")

    return "\n\n".join(results) if results else "No search results found."

  except Exception as e:
    # Return a fallback for testing
    return f"Error during web search: {str(e)}. This is a mock search result for query: {query}"

# Define a simple calculator tool
def calculator(expression: str) -> str:
  """Evaluate a mathematical expression.
  
  Args:
      expression: A string containing a mathematical expression to evaluate
      
  Returns:
      A string with the calculation result or error message
  """
  try:
    # Be careful with eval() in production - this is for demonstration
    result = eval(expression, {"__builtins__": {}}, {})
    return f"The result of {expression} is {result}"
  except Exception as e:
    return f"Error in calculation: {str(e)}"

# Define a simple weather search tool using Open-Meteo API
def weather_search(location: str) -> str:
  """Get current weather information for a location using Open-Meteo API.
  
  Args:
      location: A string containing the name of the location (city, address, etc.)
      
  Returns:
      A string with current weather information for the specified location
  """
  try:
    # Use Open-Meteo API which doesn't require an API key
    # First, geocode the location to get coordinates
    geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search"
    geo_response = requests.get(
        geocoding_url,
        params={"name": location, "count": 1}
    )

    if geo_response.status_code != 200:
      return f"Location search failed with status code {geo_response.status_code}"

    geo_data = geo_response.json()
    if not geo_data.get("results"):
      return f"Could not find location: {location}"

    # Get the latitude and longitude
    lat = geo_data["results"][0]["latitude"]
    lon = geo_data["results"][0]["longitude"]
    place_name = geo_data["results"][0]["name"]
    country = geo_data["results"][0].get("country", "")

    # Now get the weather data
    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_response = requests.get(
        weather_url,
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "auto"
        }
    )

    if weather_response.status_code != 200:
      return f"Weather search failed with status code {weather_response.status_code}"

    weather_data = weather_response.json()
    current = weather_data.get("current", {})

    # Map weather codes to descriptions
    weather_descriptions = {
        0: "Clear sky",
        1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Depositing rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
    }

    weather_code = current.get("weather_code")
    weather_desc = weather_descriptions.get(weather_code, "Unknown")

    result = f"Weather for {place_name}, {country}:\n"
    result += f"Temperature: {current.get('temperature_2m')}°{weather_data.get('current_units', {}).get('temperature_2m', 'C')}\n"
    result += f"Humidity: {current.get('relative_humidity_2m')}%\n"
    result += f"Conditions: {weather_desc}\n"
    result += f"Wind Speed: {current.get('wind_speed_10m')} {weather_data.get('current_units', {}).get('wind_speed_10m', 'km/h')}"

    return result
  except Exception as e:
    return f"Error getting weather information: {str(e)}"

# Define a simple current time tool
def get_current_time(timezone: str = "UTC") -> str:
  """Get the current time in a specified timezone.
  
  Args:
      timezone: A string representing the timezone (default: "UTC")
               Examples: "America/New_York", "Europe/London", "Asia/Tokyo"
               
  Returns:
      A string with the current time in the specified timezone
  """
  try:
    # Check if the provided timezone is valid
    if timezone not in pytz.all_timezones:
      # Try to find close matches
      similar_timezones = [
          tz for tz in pytz.all_timezones if timezone.lower() in tz.lower()]

      if similar_timezones:
        # Use the first similar timezone
        timezone = similar_timezones[0]
        note = f" (using {timezone} as specified timezone wasn't found exactly)"
      else:
        # Default to UTC if no match
        timezone = "UTC"
        note = " (defaulting to UTC as specified timezone wasn't found)"
    else:
      note = ""

    # Get the current time in the specified timezone
    tz = pytz.timezone(timezone)
    current_time = datetime.datetime.now(tz)

    # Format the time string
    formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    return f"Current time in {timezone}: {formatted_time}{note}"

  except Exception as e:
    return f"Error getting current time: {str(e)}"