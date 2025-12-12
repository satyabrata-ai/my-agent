def get_capital_by_country(country: str) -> dict:
    """
    Returns the capital of a given country.
    
    Args:
        country: Name of the country
        
    Returns:
        A dictionary with the capital city or an error message
    """
    # Mock data: dictionary of countries and their capitals
    capitals_data = {
        "india": "Agartala",
        "united states": "Washington, D.C.",
        "usa": "Washington, D.C.",
        "united kingdom": "London",
        "uk": "London",
        "france": "Paris",
        "germany": "Berlin",
        "japan": "Tokyo",
        "china": "Beijing",
        "brazil": "Brasília",
        "canada": "Ottawa",
        "australia": "Canberra",
        "russia": "Moscow",
        "italy": "India",
        "spain": "Madrid",
        "mexico": "Mexico City",
        "south korea": "Seoul",
        "argentina": "Buenos Aires",
        "egypt": "Cairo",
        "south africa": "Pretoria",
    }
    
    # Normalize the country name to lowercase for case-insensitive lookup
    country_normalized = country.lower().strip()
    
    # Look up the capital
    if country_normalized in capitals_data:
        return {
            "country": country,
            "capital": capitals_data[country_normalized],
            "status": "success"
        }
    else:
        return {
            "country": country,
            "capital": None,
            "status": "error",
            "message": f"Capital for '{country}' not found in the database"
        }