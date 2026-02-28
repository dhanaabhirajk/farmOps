# Agricultural Weather API Research for Tamil Nadu

## Executive Summary

**Decision**: Indian Meteorological Department (IMD) API + OpenWeatherMap (hybrid approach)

**Rationale**: IMD provides the most accurate, authoritative data specifically calibrated for Indian agricultural zones including Tamil Nadu. Complementing with OpenWeatherMap ensures 24/7 reliability and redundancy for a production system.

---

## Detailed API Comparison

### 1. Indian Meteorological Department (IMD)
**Cost**: Free (government service)
**Coverage**: Extremely high - India-specific with 36 meteorological subdivisions including Tamil Nadu
**Forecast Horizon**: 5-7 day forecasts available
**Historical Data**: Available but limited free access
**Reliability**: High (government authority, 150+ years data)

**Strengths**:
- Official Indian agriculture ministry data source
- Calibrated for Indian monsoons and agricultural cycles
- Regional subdivisions down to district level
- Free access essential for startup budget
- Tamil Nadu has dedicated meteorological centers (Chennai, Coimbatore)
- Used by agricultural extension services (ICAR)

**Weaknesses**:
- API documentation sparse; requires reverse-engineering from web interfaces
- Occasional latency during monsoon season
- Limited real-time data availability
- No structured REST API (XML/JSON endpoints are inconsistent)

**Python Integration**:
```python
# Unofficial but reliable wrappers available
# Example: python-imdlib package (though deprecated)
# Better: Parse IMD website data or use regional forecasts
import requests
from bs4 import BeautifulSoup

# IMD provides data via: https://mausam.imd.gov.in/
# Tamil Nadu regional: agriculture.tamil.gov.in weather integration
```

**Key Endpoints**:
- `https://mausam.imd.gov.in/api/` (meteorological subdivisions)
- `https://www.imdaws.gov.in/` (automated weather stations)

---

### 2. OpenWeatherMap
**Cost Structure**:
- Free tier: 60 calls/min, 5-day forecast, 7-day history
- Professional: $10-$100/month depending on calls
- Agricultural: ~$99-299/month (specialized endpoints)

**Coverage**: Global 0.1° grid; accurate in India but not specifically optimized
**Forecast Horizon**: 5 (free), 16 (paid days available)
**Historical Data**: 10 years available
**Reliability**: 99.9% uptime SLA (paid)
**Python Integration**: Excellent (`python-dotenv`, `requests`, or `pyowm` library)

**Strengths**:
- Excellent API documentation and SDKs
- Real-time solar radiation data (relevant for crop irrigation)
- Reliable infrastructure suitable for production
- Easy Python integration (`pip install pyowm`)
- Premium agricultural tier includes soil moisture

**Weaknesses**:
- Not India-specific; data derived from global models
- Premium agricultural tier required for soil/moisture (~$299/month)
- Pricing prohibitive for startups on thin margins

**Code Example**:
```python
from pyowm.owm25.owm25 import OWM25
owm = OWM25(api_key='your_key')
forecast = owm.weather_manager().forecast_at_coords(11.0168, 76.8194, 'daily')  # Coimbatore
for weather in forecast.forecast_list[:7]:
    print(f"Date: {weather.reference_time}, Temp: {weather.temperature('celsius')}, Rain: {weather.rain}")
```

---

### 3. Visual Crossing
**Cost Structure**:
- Free tier: 1000 calls/day, limited to current/past data
- Premium: $15-99/month (includes 7-14 day forecasts)

**Coverage**: Global; adequate for India but not optimized
**Forecast Horizon**: 14-15 days available
**Historical Data**: 50+ years comprehensive historical data (unique strength)
**Reliability**: Good (99.5% uptime)

**Strengths**:
- Best historical weather data (50+ years) - excellent for ML model training
- Affordable premium tier ($15/month starter)
- Timeline API for backtesting agricultural interventions
- Good for agricultural analysis (includes wind, UV index)
- Direct CSV/JSON downloads for data science workflows

**Weaknesses**:
- Free tier doesn't include forecasts (only historical)
- Not specifically calibrated for Indian agriculture
- Smaller company = less reliability guarantee

**Python Integration**:
```python
import requests
import pandas as pd

url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline/Coimbatore/today"
params = {
    'key': 'YOUR_KEY',
    'include': 'days,hours,alerts'
}
response = requests.get(url, params=params)
data = response.json()
```

---

### 4. Other Relevant APIs

#### NOAA (US National Oceanic & Atmospheric Administration)
- **Cost**: Free
- **Strength**: Global model data, accurate
- **Weakness**: Optimized for Americas, not India-specific
- **Forecast**: 7 days

#### Weatherstack
- **Cost**: Free tier + $9.99/month
- **Strength**: Reliable, 40+ years historical
- **Weakness**: Minimal agricultural specificity

#### Agritech-specific: Krishi APIs (Indian government initiative)
- **Status**: In development phase as of 2024
- **Promise**: Agricultural-specific indices (soil moisture from satellites)
- **Timeline**: Check `agritech.gov.in` for current status

---

## Regional Specifics for Tamil Nadu

### Geographical Considerations:
- **Coordinates**: Latitude 11-13°N, Longitude 76-80°E
- **Key Agricultural Zones**: 
  - Coimbatore (11.01°N, 76.82°E) - tea, spices, cotton
  - Madurai (9.93°N, 78.12°E) - sugarcane, rice
  - Tiruppur (11.11°N, 77.36°E) - cotton, vegetables
  - Chennai (13.05°N, 80.27°E) - coastal crops

### Required Parameters for Tamil Nadu Agriculture:
1. **Rainfall** (critical during SW monsoon: June-August)
2. **Temperature** (stress during January heat: 35°C+)
3. **Humidity** (fungal disease indicator)
4. **Wind Speed** (irrigation efficiency)
5. **Solar Radiation** (crop yield correlator)
6. **Soil Moisture** (if available via API)

---

## Recommended Implementation Stack

### For Minimum Viable Product (MVP):

```python
# Hybrid approach: IMD primary, OpenWeatherMap fallback
import requests
from datetime import datetime

class AgriculturalWeatherService:
    def __init__(self, owm_key):
        self.owm_key = owm_key
        
    def get_imd_forecast(self, region='TAMILNADU'):
        """Fetch from IMD (free, authoritative)"""
        try:
            # IMD regional forecast endpoint
            url = f"https://mausam.imd.gov.in/region/india/"
            response = requests.get(url, timeout=5)
            # Parse XML/HTML response
            return self._parse_imd_response(response)
        except:
            return None
    
    def get_owm_forecast(self, lat, lon):
        """Fallback to OpenWeatherMap (reliable)"""
        url = "https://api.openweathermap.org/data/2.5/forecast"
        params = {
            'lat': lat, 'lon': lon,
            'appid': self.owm_key,
            'units': 'metric'
        }
        response = requests.get(url, params=params)
        return response.json()
    
    def get_agricultural_forecast(self, location_lat, location_lon):
        """Composite forecast"""
        imd_data = self.get_imd_forecast()
        owm_data = self.get_owm_forecast(location_lat, location_lon)
        
        # Merge data: use IMD if available, fall back to OWM
        return {
            'primary_source': 'imd' if imd_data else 'owm',
            'forecast': imd_data or owm_data,
            'timestamp': datetime.now().isoformat()
        }
```

### For Production System:

1. **Primary**: IMD (free, India-specific)
2. **Secondary Cache**: OpenWeatherMap (reliable fallback)
3. **Historical Analysis**: Visual Crossing ($15/month for research)
4. **Monitoring**: Track accuracy against actual rainfall/temperature

---

## Cost Analysis for Startup

### Option 1: Minimum Cost (Recommended)
- **IMD**: Free
- **OpenWeatherMap**: Free tier (60 calls/min)
- **Monthly Cost**: $0
- **Limitation**: Limited to non-commercial use initially

### Option 2: Production Ready
- **IMD**: Free
- **OpenWeatherMap**: Professional tier - $10/month
- **Visual Crossing**: Historical data - $15/month
- **Monthly Cost**: $25
- **Benefit**: Reliable API infrastructure + historical backtesting capability

### Option 3: Premium (Future Scale)
- **OpenWeatherMap Agricultural**: $299/month (soil moisture, UV)
- **Visual Crossing Premium**: $49/month
- **IMD**: Free
- **Monthly Cost**: $348

**For MVP**: Option 1  
**For 6-month runway**: Option 2 (highly recommended)

---

## Final Recommendation Logic

| Criterion | Winner | Rationale |
|-----------|--------|-----------|
| **Accuracy for Tamil Nadu** | IMD | Government authority, locally calibrated models |
| **Reliability/Uptime** | OpenWeatherMap | 99.9% SLA for paid tier |
| **Cost** | IMD | Free government service |
| **Forecast Horizon** | Visual Crossing | 14 days vs 5-7 for others |
| **Historical Data** | Visual Crossing | 50+ years for ML training |
| **Python Integration** | OpenWeatherMap | Best documented, `pyowm` library excellent |
| **Agricultural Specificity** | IMD | Direct integration with ICAR advisory system |

---

## Implementation Roadmap

### Week 1-2: Research & Setup
- [ ] Create IMD data scraper or find working wrapper
- [ ] Register free OpenWeatherMap tier
- [ ] Identify 3-5 representative Tamil Nadu locations
- [ ] Test API response times during peak hours

### Week 3-4: Prototype
- [ ] Build hybrid weather service class
- [ ] Integrate with crop advisory logic (N days before sowing, etc.)
- [ ] Test fallback mechanisms

### Month 2: MVP Launch
- [ ] Deploy with IMD + OWM free tier
- [ ] Monitor accuracy vs real-world ground truth
- [ ] Track decision tree: when did each API work best?

### Month 3-6: Scale
- [ ] Upgrade to Visual Crossing ($15/month) if backtesting is valuable
- [ ] Consider OpenWeatherMap professional ($10/month) if call volumes exceed free tier
- [ ] Evaluate Krishi APIs if government platform matures

---

## Critical Success Factors

1. **Data Validation**: Compare API forecasts to actual observed weather at farm location
2. **Latency Requirements**: IMD updates ~2x daily; OWM updates every 3 hours
3. **Seasonal Adjustments**: Monsoon season (June-Aug) requires more frequent updates
4. **User Trust**: Show confidence intervals, not point forecasts
5. **Legal**: IMD data is public domain; ensure OWM API terms compliance

---

## Conclusion

**Use IMD as primary source** for agricultural credibility + government adoption, **supplement with OpenWeatherMap free tier** for operational reliability, and **add Visual Crossing ($15/month) for historical analysis and ML model training**. Total startup cost: **$15/month** for a production-ready system.

This approach balances **accuracy (IMD), reliability (OWM), and cost ($15/month)** while remaining compliant with Indian government agricultural frameworks.
