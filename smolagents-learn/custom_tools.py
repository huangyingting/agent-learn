from smolagents import tool
from urllib.parse import urlparse
import os
import requests
import io
from openai import AzureOpenAI
from pydub import AudioSegment
import magic
from fast_flights import FlightData, Passengers, Result, get_flights
from datetime import datetime
from lxml import html


@tool
def transcribe(filepath_or_url: str, end_seconds: int = -1) -> str:
  """
  Transcribe audio from a file or URL.
  Args:
      filepath_or_url: The file path or URL of the audio to transcribe, supported formats .mpeg, .mp4, .mp3, .wav, .webm, .m4a, .mpga
      end_seconds: The end time in seconds to trim the audio (default: -1 for no trim)
  """
  ALLOWED_MIME_TYPES = {
      "audio/mpeg", "audio/mp4", "audio/mp3",
      "audio/wav", "audio/webm", "audio/m4a",
      "audio/mpga"
  }

  parsed_url = urlparse(filepath_or_url)
  is_remote = parsed_url.scheme in ['http', 'https']

  if is_remote:
    response = requests.get(filepath_or_url, stream=True)
    response.raise_for_status()  # Raise exception for HTTP errors

    content = io.BytesIO(response.content)

    content_type = response.headers.get('Content-Type')
    if not content_type or content_type not in ALLOWED_MIME_TYPES:
      content.seek(0)
      mime = magic.from_buffer(content.read(2048), mime=True)
      content.seek(0)
      if mime not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported file format: {mime}")

    audio = AudioSegment.from_file(content)

  else:
    file_path = filepath_or_url

    mime = magic.from_file(file_path, mime=True)
    if mime not in ALLOWED_MIME_TYPES:
      raise ValueError(f"Unsupported file format: {mime}")

    audio = AudioSegment.from_file(file_path)

  if end_seconds > 0 and end_seconds < len(audio) / 1000:
    trimed_audio = audio[:end_seconds * 1000]
  else:
    trimed_audio = audio

  buffer = io.BytesIO()
  trimed_audio.export(buffer, format="mp3")
  buffer.seek(0)
  buffer.name = "trimed_audio.mp3"

  client = AzureOpenAI(
      azure_deployment=os.getenv("AZURE_OPEN_TRANSCRIBE_DEPLOYMENT"),
      api_version=os.getenv("OPENAI_API_VERSION"),
      azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
      api_key=os.getenv("AZURE_OPENAI_API_KEY"),
  )

  transcript = client.audio.transcriptions.create(
      model=os.getenv("AZURE_OPEN_TRANSCRIBE_DEPLOYMENT"),
      file=buffer,
  )
  return transcript.text


def get_hotel_search_repsonse(query_string):
  """This function will send a request to the google server with the given
  query_string as parameter and returns the response object.

  Args:
  query_string (str): Keyword used to search hotels._

  Returns:
  Response : response object received from google server
  """
  url = "https://www.google.com/travel/search"

  headers = {
      'authority': 'www.google.com',
      'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image'
      '/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange'
      ';v=b3;q=0.7',
      'accept-language': 'en-GB,en;q=0.9',
      'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119",'
      '"Not?A_Brand";v="24"',
      'sec-ch-ua-arch': '"x86"',
      'sec-ch-ua-bitness': '"64"',
      'sec-ch-ua-full-version': '"119.0.6045.123"',
      'sec-ch-ua-full-version-list': '"Google Chrome";v="119.0.6045.123",'
      '"Chromium";v="119.0.6045.123", "Not?A_Brand";v="24.0.0.0"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-model': '""',
      'sec-ch-ua-platform': '"Linux"',
      'sec-ch-ua-platform-version': '"6.2.0"',
      'sec-ch-ua-wow64': '?0',
      'sec-fetch-dest': 'document',
      'sec-fetch-mode': 'navigate',
      'sec-fetch-site': 'none',
      'sec-fetch-user': '?1',
      'upgrade-insecure-requests': '1',
      'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
      '(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  }

  params = {
      'q': query_string,
  }

  response = requests.get(url=url, headers=headers, params=params)
  return response


def parse_hotel_search_response(response):
  """This function parses the response received from the google server,
  finds all the hotel data from the html and returns this data as
  list of dictionaries.


  Args:
  response (response_object): Response of request send to google server


  Returns:
  list: Returns a list of dictionaries where each dictionary contains
  data of a particular hotel.
  """
  parser = html.fromstring(response.text)
  hotels_data = []
  hotels_list = parser.xpath("//div[@jsname='mutHjb']")
  for hotel in hotels_list:
    name = hotel.xpath(".//h2[@class='BgYkof ogfYpf ykx2he']/text()")
    price = hotel.xpath(
        ".//span[@jsaction='mouseenter:JttVIc;mouseleave:VqIRre;']//text()"
    )[0]
    rating = hotel.xpath(".//span[@class='ta47le ']/@aria-label")
    amenities = get_hotel_amenities(hotel)
    hotel_data = {
        "name": convert_list_to_str(name),
        "price": price,
        "rating": convert_list_to_str(rating),
        "amenities": convert_list_to_str(amenities, " | ")}
    hotels_data.append(hotel_data)
  return hotels_data


def get_hotel_amenities(hotel_html):
  """This function extracts the amenities of a hotel from its HTML content.

  Args:
  hotel_html (html_element): html_element that represents a hotel

  Returns:
  ist_: each element is an amenity provided by the hotel
  """
  amenities = hotel_html.xpath(".//span[@class='lXJaOd']/text()")
  amenities_str = convert_list_to_str(amenities)
  amenities_list = amenities_str.split(":")[1].split(",")
  return amenities_list


def convert_list_to_str(input_list, separator=" "):
  """This function converts a list of strings to a single string joined by a 
  seperator.

  Args:
  input_list (_list_): List of strings tho be combined
  separator (str, optional): The separator to be used between the 
  strings. Defaults to " ".

  Returns:
  str: A single string formed by concatenating the elements of the input list
  """
  cleaned_elements = []
  for element in input_list:
    if element == " ":
      continue
    cleaned_element = element.replace("\\", "")
    cleaned_elements.append(cleaned_element)
  return separator.join(cleaned_elements)


@tool
def search_flights(
    from_airport: str,
    to_airport: str,
    date: str = datetime.now().strftime("%Y-%m-%d"),
    seat_class: str = "economy",
    adults: int = 1,
    children: int = 0,
    max_stops: int = 0,
) -> dict:
  """
  Search for available flights based on the specified travel parameters.

  Args:
      from_airport (str): The 3-letter IATA code for the departure airport (e.g., "TPE" for Taipei)
      to_airport (str): The 3-letter IATA code for the destination airport (e.g., "MYJ" for Matsuyama)
      date (str): The departure date in YYYY-MM-DD format (e.g., "2025-05-15")
      seat_class (str): Class of service - "economy", "premium_economy", "business", or "first"
      adults (int): Number of adult passengers (12+ years)
      children (int): Number of child passengers (2-11 years)
      max_stops (int): Maximum number of stopovers allowed (0 for direct flights only)

  Returns:
      dict: A dictionary containing flight search results with the following structure:
          - current_price: The total price for all passengers
          - flights: A list of available flights, each containing details such as:
              - is_best: Whether this is flagged as the best flight option
              - name: The airline and flight number
              - departure: Departure time and date
              - arrival: Arrival time and date
              - arrival_time_ahead: If arrival is on a different day
              - duration: Total flight duration
              - stops: Number of stopovers
              - delay: Any known delay information
              - price: Cost per flight
  """
  result: Result = get_flights(
      flight_data=[
          FlightData(date=date, from_airport=from_airport,
                     to_airport=to_airport)
      ],
      trip="one-way",
      seat=seat_class,
      passengers=Passengers(
          adults=adults,
          children=children,
      ),
      fetch_mode="fallback",
      max_stops=max_stops,
  )

  flights_list = []
  for flight in result.flights:
    flight_dict = {
        "is_best": flight.is_best,
        "name": flight.name,
        "departure": flight.departure,
        "arrival": flight.arrival,
        "arrival_time_ahead": flight.arrival_time_ahead,
        "duration": flight.duration,
        "stops": flight.stops,
        "delay": flight.delay,
        "price": flight.price
    }
    flights_list.append(flight_dict)

  return {
      "current_price": result.current_price,
      "flights": flights_list
  }


@tool
def search_hotels(
    location: str,
) -> list:
  """
  Search for hotels in the specified location using Google Travel.

  Args:
      location (str): The location to search for hotels (e.g., "New York", "Paris", "Tokyo")

  Returns:
      list: A list of dictionaries containing hotel information with the following structure:
          - name: The name of the hotel
          - price: The price per night
          - rating: The hotel's rating
          - amenities: A string of amenities offered by the hotel
  """
  response = get_hotel_search_repsonse(location)

  if response.status_code == 200:
    hotels_data = parse_hotel_search_response(response)
    return hotels_data
  else:
    return {"error": f"Failed to get hotel data. Status code: {response.status_code}"}
