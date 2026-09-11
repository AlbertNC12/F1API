"""
Configuration module for Formula 1 API.
Contains constants, headers, and HTTP configuration.
"""
import os
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

# Country and Nationality Dictionary for flexible search
NATIONALITY_TO_CODE = {
    "british": "GBR", "great britain": "GBR", "uk": "GBR", "united kingdom": "GBR", "england": "GBR", "scotland": "GBR", "gbr": "GBR",
    "italian": "ITA", "italy": "ITA", "ita": "ITA",
    "dutch": "NED", "netherlands": "NED", "holland": "NED", "ned": "NED",
    "german": "GER", "germany": "GER", "ger": "GER", "deu": "GER",
    "spanish": "ESP", "spain": "ESP", "esp": "ESP",
    "french": "FRA", "france": "FRA", "fra": "FRA",
    "australian": "AUS", "australia": "AUS", "aus": "AUS",
    "brazilian": "BRA", "brazil": "BRA", "bra": "BRA",
    "finnish": "FIN", "finland": "FIN", "fin": "FIN",
    "japanese": "JPN", "japan": "JPN", "jpn": "JPN",
    "canadian": "CAN", "canada": "CAN", "can": "CAN",
    "american": "USA", "united states": "USA", "usa": "USA", "us": "USA",
    "mexican": "MEX", "mexico": "MEX", "mex": "MEX",
    "austrian": "AUT", "austria": "AUT", "aut": "AUT",
    "belgian": "BEL", "belgium": "BEL", "bel": "BEL",
    "swiss": "SUI", "switzerland": "SUI", "sui": "SUI",
    "monacan": "MON", "monégasque": "MON", "monegasque": "MON", "monaco": "MON", "mon": "MON",
    "thai": "THA", "thailand": "THA", "tha": "THA",
    "danish": "DEN", "denmark": "DEN", "den": "DEN",
    "chinese": "CHN", "china": "CHN", "chn": "CHN",
    "new zealander": "NZL", "new zealand": "NZL", "nzl": "NZL",
    "argentine": "ARG", "argentina": "ARG", "arg": "ARG",
    "south african": "RSA", "south africa": "RSA", "rsa": "RSA",
    "swedish": "SWE", "sweden": "SWE", "swe": "SWE",
    "colombian": "COL", "colombia": "COL", "col": "COL",
    "venezuelan": "VEN", "venezuela": "VEN", "ven": "VEN",
    "polish": "POL", "poland": "POL", "pol": "POL",
    "russian": "RUS", "russia": "RUS", "rus": "RUS",
    "indonesian": "INA", "indonesia": "INA", "ina": "INA",
    "indian": "IND", "india": "IND", "ind": "IND",
    "irish": "IRL", "ireland": "IRL", "irl": "IRL",
    "portuguese": "POR", "portugal": "POR", "por": "POR",
}

COUNTRY_MAP = {
    "italy": ["italy", "italian", "emilia-romagna", "emilia romagna", "san marino", "pescara", "monza", "imola"],
    "italian": ["italy", "italian", "emilia-romagna", "emilia romagna", "san marino", "pescara", "monza", "imola"],
    "uk": ["great britain", "british", "great-britain", "silverstone", "donington", "brands hatch", "european"],
    "britain": ["great britain", "british", "great-britain", "silverstone", "donington", "brands hatch"],
    "british": ["great britain", "british", "great-britain", "silverstone", "donington", "brands hatch"],
    "usa": ["united states", "usa", "miami", "las vegas", "austin", "indianapolis", "detroit", "dallas", "long beach", "caesars palace"],
    "united states": ["united states", "usa", "miami", "las vegas", "austin", "indianapolis", "detroit", "dallas", "long beach"],
    "america": ["united states", "usa", "miami", "las vegas", "austin", "indianapolis", "detroit", "dallas", "long beach"],
    "spain": ["spain", "spanish", "europe", "valencia", "jerez", "barcelona", "catalunya"],
    "spanish": ["spain", "spanish", "europe", "valencia", "jerez", "barcelona", "catalunya"],
    "germany": ["germany", "german", "nurburgring", "hockenheim", "europe", "luxembourg"],
    "german": ["germany", "german", "nurburgring", "hockenheim", "europe", "luxembourg"],
    "france": ["france", "french", "paul ricard", "magny-cours", "reims", "dijon"],
    "french": ["france", "french", "paul ricard", "magny-cours", "reims", "dijon"],
    "japan": ["japan", "japanese", "suzuka", "fuji", "pacific"],
    "japanese": ["japan", "japanese", "suzuka", "fuji", "pacific"],
    "australia": ["australia", "australian", "melbourne", "adelaide", "albert park"],
    "australian": ["australia", "australian", "melbourne", "adelaide", "albert park"],
    "brazil": ["brazil", "brazilian", "sao paulo", "interlagos", "rio", "jacarepagua"],
    "brazilian": ["brazil", "brazilian", "sao paulo", "interlagos", "rio", "jacarepagua"],
    "monaco": ["monaco", "monacan", "monte carlo"],
    "canada": ["canada", "canadian", "montreal"],
    "canadian": ["canada", "canadian", "montreal"],
    "mexico": ["mexico", "mexican", "mexico city", "rodriguez"],
    "mexican": ["mexico", "mexican", "mexico city", "rodriguez"],
    "austria": ["austria", "austrian", "styria", "spielberg", "red bull ring", "ozsterreichring"],
    "austrian": ["austria", "austrian", "styria", "spielberg", "red bull ring"],
    "belgium": ["belgium", "belgian", "spa", "francorchamps", "zolder"],
    "belgian": ["belgium", "belgian", "spa", "francorchamps", "zolder"],
    "netherlands": ["netherlands", "dutch", "zandvoort"],
    "dutch": ["netherlands", "dutch", "zandvoort"],
    "hungary": ["hungary", "hungarian", "hungaroring", "budapest"],
    "hungarian": ["hungary", "hungarian", "hungaroring", "budapest"],
    "bahrain": ["bahrain", "sakhir"],
    "saudi arabia": ["saudi arabia", "saudi", "jeddah"],
    "azerbaijan": ["azerbaijan", "baku"],
    "singapore": ["singapore", "marina bay"],
    "qatar": ["qatar", "losail"],
    "uae": ["abu dhabi", "uae", "yas marina"],
    "abu dhabi": ["abu dhabi", "uae", "yas marina"],
    "china": ["china", "chinese", "shanghai"],
    "chinese": ["china", "chinese", "shanghai"],
}


def create_resilient_session() -> requests.Session:
    """Create an HTTP session with automatic retry logic and connection pooling."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update(HEADERS)
    return session


HTTP_SESSION = create_resilient_session()
HTTP_TIMEOUT = (3.05, 8.0)

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
).split(",")
ALLOWED_ORIGINS = [origin.strip() for origin in ALLOWED_ORIGINS]
