import requests
from datetime import date, timedelta, timezone, datetime

def requestWeather(email, lat, lon):

    url = f"https://api.met.no/weatherapi/locationforecast/2.0/compact?lat={lat}&lon={lon}"

    response = requests.get(url, headers={"User-Agent": f"Surface-Weather/1.0 {email}"})

    data = response.json()
    return data

def parse_met_time(iso_str):
    """Parse ISO 8601 time string to a datetime object (aware, UTC)."""
    return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

def extract_weather_tuple(entry):
    """
    Extracts and returns:
    (air_temperature, cloud_area_fraction, wind_speed, relative_humidity, precipitation_amount)
    """
    details = entry["data"]["instant"]["details"]
    next_1h = entry["data"].get("next_1_hours", {})
    precip = next_1h.get("details", {}).get("precipitation_amount", None)

    return (
        details.get("air_temperature"),
        details.get("cloud_area_fraction"),
        details.get("wind_speed"),
        details.get("relative_humidity"),
        precip
    )

def getCurrentWeather(json_data, now=None):
    """
    Returns closest weather to current time as tuple:
    (air_temperature, cloud_area_fraction, wind_speed, relative_humidity, precipitation_amount)
    """
    now = now or datetime.utcnow().replace(tzinfo=timezone.utc)
    timeseries = json_data["properties"]["timeseries"]
    closest = min(timeseries, key=lambda entry: abs(parse_met_time(entry["time"]) - now))
    return extract_weather_tuple(closest)

def getForecastPrecise(json_data, day_offset, hour, include_date=False):
    """
    Returns forecast tuple for a given day and hour in UTC.
    (air_temperature, cloud_area_fraction, wind_speed, relative_humidity, precipitation_amount)
    If include_date is True, appends a 'DD/MM' string to the tuple.
    """
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0, tzinfo=timezone.utc)
    target_time = now + timedelta(days=day_offset)
    target_time = target_time.replace(hour=hour)
    
    timeseries = json_data["properties"]["timeseries"]
    closest = min(timeseries, key=lambda entry: abs(parse_met_time(entry["time"]) - target_time))
    
    result = extract_weather_tuple(closest)
    
    if include_date:
        date_str = target_time.strftime("%d/%m")
        result = result + (date_str,)
    
    return result


#===========================================================================

#IP API to get relative location without GPS hassle (+ time zone)
def getIPstuff():
    response = requests.get("http://ip-api.com/csv/?fields=33554640")

    rawCSV = response.text

    city, lat, lon, UTCsec = rawCSV.split(',')
    pCSV = (str(city), float(lat), float(lon), int(UTCsec))

    city, lat, lon, UTCsec = pCSV

    UTCh = (UTCsec / 3600)

    tupleThing = city, lat, lon, int(UTCh)
    return tupleThing

def getWeekday(source=date.weekday(date.today()), shorten=False):
    numberWeekday = source

    if not shorten:
        if numberWeekday == 0:
            return "monday"
        if numberWeekday == 1:
            return "tuesday"
        if numberWeekday == 2:
            return "wednesday"
        if numberWeekday == 3:
            return "thursday"
        if numberWeekday == 4:
            return "friday"
        if numberWeekday == 5:
            return "saturday"
        if numberWeekday == 6:
            return "sunday"
          
    if shorten:
        if numberWeekday == 0:
            return "mon"
        if numberWeekday == 1:
            return "tue"
        if numberWeekday == 2:
            return "wed"
        if numberWeekday == 3:
            return "thu"
        if numberWeekday == 4:
            return "fri"
        if numberWeekday == 5:
            return "sat"
        if numberWeekday == 6:
            return "sun"

def shortenMonth(monthIO):
    if monthIO == "January":
        return "Jan"
    elif monthIO == "February":
        return "Feb"
    elif monthIO == "March":
        return "Mar"
    elif monthIO == "April":
        return "Apr"
    elif monthIO == "May":
        return "May"
    elif monthIO == "June":
        return "Jun"
    elif monthIO == "July":
        return "Jul"
    elif monthIO == "August":
        return "Aug"
    elif monthIO == "September":
        return "Sep"
    elif monthIO == "October":
        return "Oct"
    elif monthIO == "November":
        return "Nov"
    elif monthIO == "December":
        return "Dec"

#ToDo: make region selection automatic
def hemisphereTimeOps(UTCoffset, inputHour, Western=True):
    if Western:
        return (inputHour + UTCoffset) % 24
    if not Western:
        return (inputHour - UTCoffset) % 24

#if statements to deduce rain (precipitation) probability from quantity
def getRainProbability(source):
    if source:
        currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = source
    else:
        source = (0, 0, 0, 0, 0)
        currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = source

    if currentPrecpAmount:
        rawAmount = currentPrecpAmount
    else:
        rawAmount = 0

    if rawAmount <= 0:
        probCalc = 0
    elif rawAmount > 0 and rawAmount <= 1:
        probCalc = 5
    elif rawAmount > 1 and rawAmount <= 3:
        probCalc = 12
    elif rawAmount > 3 and rawAmount <= 4:
        probCalc = 20
    elif rawAmount > 4 and rawAmount <= 5:
        probCalc = 40
    elif rawAmount > 5 and rawAmount <= 6:
        probCalc = 70
    elif rawAmount > 6 and rawAmount <= 7:
        probCalc = 80
    elif rawAmount > 7 and rawAmount <= 8:
        probCalc = 100
    else:
        probCalc = 100

    return probCalc

#if statements to find the appropriate weather icon, with the current parameter to select whether to find the icon for current weather
#or for forecasting
def getWeatherIcon(source):
    if source:
        currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = source
    else:
        source = (0, 0, 0, 0, 0)
        currentTemperature, currentCloudArea, currentWindSpeed, currentRelHumidity, currentPrecpAmount = source

    rainProb = getRainProbability(source)

    icon = None
    vocabIcon = None

    #first, in order of least importance, get cloud state:
    if currentCloudArea < 60:
        icon = "weather-sunny"
        vocabIcon = "sunny"
    if currentCloudArea >= 60 and currentCloudArea < 80:
        icon = "weather-sunny"
        vocabIcon = "partly cloudy"
    if currentCloudArea >= 80:
        icon = "weather-cloudy"
        vocabIcon = "cloudy"

    #then, get sun state:
    if not icon:
        if currentTemperature < 30:
            icon = "weather-sunny"
            vocabIcon = "sunny"
        elif currentTemperature >= 30:
            icon = "weather-sunny-alert"
            vocabIcon = "quite hot"

    #finally, get rain-iness state (last so it overrides anything less important):
    if rainProb < 25:
        icon = icon
    elif 25 <= rainProb < 40:
        icon = "weather-rainy"
        vocabIcon = "rainy"
    elif rainProb >= 40:
        icon = "weather-pouring"
        vocabIcon = "pouring"

    return icon, vocabIcon
