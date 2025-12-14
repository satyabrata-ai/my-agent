

def get_city_temperature(country: str) -> dict:
    """
    Returns the current temperature and weather condition for a country's capital city.
    
    Args:
        country: Name of the country
        
    Returns:
        A dictionary with temperature, weather condition, and city name
    """
    # Mock data: dictionary of countries and their temperatures (in Celsius)
    temperature_data = {
        "india": {"city": "New Delhi", "temperature": "32", "condition": "Rainy"},
        "united states": {"city": "Washington, D.C.", "temperature": "22", "condition": "Partly Cloudy"},
        "usa": {"city": "Washington, D.C.", "temperature": "22", "condition": "Partly Cloudy"},
        "united kingdom": {"city": "London", "temperature": "15", "condition": "Rainy"},
        "uk": {"city": "London", "temperature": "15", "condition": "Rainy"},
        "france": {"city": "Paris", "temperature": "18", "condition": "Cloudy"},
        "germany": {"city": "Berlin", "temperature": "16", "condition": "Overcast"},
        "japan": {"city": "Tokyo", "temperature": "25", "condition": "Clear"},
        "china": {"city": "Beijing", "temperature": "28", "condition": "Hazy"},
        "brazil": {"city": "Brasília", "temperature": "30", "condition": "Sunny"},
        "canada": {"city": "Ottawa", "temperature": "10", "condition": "Cold"},
        "australia": {"city": "Canberra", "temperature": "20", "condition": "Sunny"},
        "russia": {"city": "Moscow", "temperature": "5", "condition": "Snowy"},
        "italy": {"city": "Rome", "temperature": "24", "condition": "Sunny"},
        "spain": {"city": "Madrid", "temperature": "26", "condition": "Hot and Sunny"},
        "mexico": {"city": "Mexico City", "temperature": "23", "condition": "Warm"},
        "south korea": {"city": "Seoul", "temperature": "20", "condition": "Clear"},
        "argentina": {"city": "Buenos Aires", "temperature": "19", "condition": "Mild"},
        "egypt": {"city": "Cairo", "temperature": "35", "condition": "Very Hot"},
        "south africa": {"city": "Pretoria", "temperature": "22", "condition": "Pleasant"},
    }
    
    # Normalize the country name to lowercase for case-insensitive lookup
    country_normalized = country.lower().strip()
    
    # Look up the temperature
    if country_normalized in temperature_data:
        data = temperature_data[country_normalized]
        return {
            "country": country,
            "city": data["city"],
            "temperature": f"{data['temperature']}°C",
            "condition": data["condition"],
            "status": "success"
        }
    else:
        return {
            "country": country,
            "city": None,
            "temperature": None,
            "condition": None,
            "status": "error",
            "message": f"Temperature data for '{country}' not found in the database"
        }