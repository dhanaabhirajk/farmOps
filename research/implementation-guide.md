# Implementation Guide: Mandi Price Data Integration

## Setup Instructions

### 1. Install Required Dependencies

```bash
# Core libraries
pip install requests beautifulsoup4 pandas python-dotenv

# For advanced scraping (if needed)
pip install selenium playwright

# Community AGMARKNET library (recommended)
pip install agmarknet-python

# Database (choose one)
pip install psycopg2-binary  # PostgreSQL
# OR
pip install pymongo  # MongoDB
```

---

## Implementation Approach 1: Using agmarknet-python (Recommended)

```python
# File: src/data_sources/agmarknet_client.py

from agmarknet import AgMarkNet
from datetime import datetime, timedelta
import pandas as pd
import logging
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MandiPriceClient:
    """
    Client for fetching mandi prices from AGMARKNET
    """
    
    def __init__(self):
        self.client = AgMarkNet()
        self.tn_mandis = {
            'koyambedu': 506,
            'krishnagiri': 507,
            'salem': 680,
            'erode': 681,
            'madurai': 608,
            'villupuram': None,
        }
    
    def get_prices_for_date(self, date: str, mandi_name: str = 'koyambedu') -> Optional[pd.DataFrame]:
        """
        Fetch prices for a specific date and mandi.
        
        Args:
            date (str): Date in format 'YYYY-MM-DD' or 'DD-MM-YYYY'
            mandi_name (str): Mandi name (lowercase, use keys from tn_mandis)
        
        Returns:
            pd.DataFrame: Price data or None if error
        """
        try:
            mandi_id = self.tn_mandis.get(mandi_name.lower())
            if not mandi_id:
                logger.error(f"Unknown mandi: {mandi_name}")
                return None
            
            # Convert date format if needed
            if '-' in date and len(date.split('-')[0]) == 4:
                # YYYY-MM-DD format - convert to DD-MM-YYYY
                date = '-'.join(date.split('-')[::-1])
            
            prices = self.client.get_prices(
                market_id=mandi_id,
                date=date,
            )
            
            if prices:
                df = pd.DataFrame(prices)
                logger.info(f"Fetched {len(df)} records for {mandi_name} on {date}")
                return df
            else:
                logger.warning(f"No data found for {mandi_name} on {date}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching prices: {str(e)}")
            return None
    
    def get_latest_prices(self, mandi_name: str = 'koyambedu') -> Optional[pd.DataFrame]:
        """
        Fetch latest available prices (typically latest trading day).
        """
        return self.get_prices_for_date(
            date=datetime.now().strftime('%d-%m-%Y'),
            mandi_name=mandi_name
        )
    
    def get_historical_prices(self, 
                             mandi_name: str = 'koyambedu',
                             days: int = 30,
                             commodity: str = None) -> pd.DataFrame:
        """
        Fetch prices for the last N days.
        
        Args:
            mandi_name (str): Mandi name
            days (int): Number of days of history
            commodity (str): Optional - filter by commodity name
        
        Returns:
            pd.DataFrame: Combined historical data
        """
        all_data = []
        current_date = datetime.now()
        
        for i in range(days):
            date = (current_date - timedelta(days=i)).strftime('%d-%m-%Y')
            df = self.get_prices_for_date(date, mandi_name)
            
            if df is not None:
                if commodity:
                    df = df[df['commodity'].str.lower().str.contains(commodity.lower())]
                all_data.append(df)
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            logger.info(f"Fetched {len(result)} records for {days} days")
            return result
        else:
            return pd.DataFrame()
    
    def get_all_tn_mandis(self) -> List[str]:
        """Return list of available Tamil Nadu mandis."""
        return list(self.tn_mandis.keys())


# Usage Example
if __name__ == '__main__':
    client = MandiPriceClient()
    
    # Get latest prices
    latest = client.get_latest_prices('koyambedu')
    print(latest)
    
    # Get 7-day history for tomatoes
    history = client.get_historical_prices('koyambedu', days=7, commodity='tomato')
    print(history)
    
    # Export to CSV
    if not history.empty:
        history.to_csv('tomato_prices.csv', index=False)
```

---

## Implementation Approach 2: Manual Web Scraping (Fallback)

```python
# File: src/data_sources/agmarknet_scraper.py

import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MandiScraper:
    """
    Fallback scraper for AGMARKNET if library is unavailable.
    """
    
    BASE_URL = 'https://agmarknet.gov.in/SearchMarketArrivalsDefault.aspx'
    
    # Mandi IDs for Tamil Nadu
    MANDI_IDS = {
        'koyambedu': 506,
        'krishnagiri': 507,
        'salem': 680,
        'erode': 681,
        'madurai': 608,
    }
    
    def __init__(self, delay=2):
        """
        Initialize scraper.
        
        Args:
            delay (int): Delay between requests in seconds (to avoid blocking)
        """
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def scrape_prices(self, mandi_id: int, date: str) -> Optional[pd.DataFrame]:
        """
        Scrape prices for a specific mandi and date.
        
        Args:
            mandi_id (int): Mandi ID number
            date (str): Date in DD-MM-YYYY format
        
        Returns:
            pd.DataFrame: Price data or None if error
        """
        try:
            params = {
                'State': '25',  # Tamil Nadu code
                'Market': str(mandi_id),
                'Commodity': '0',
                'From_Date': date,
                'To_Date': date,
                'Sort': 'Lmark',
            }
            
            response = self.session.get(self.BASE_URL, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the main data table (adjust selector as needed)
            table = soup.find('table', {'id': 'gvMarketArrivals'})
            
            if table:
                df = pd.read_html(str(table))[0]
                logger.info(f"Scraped {len(df)} records for mandi {mandi_id}")
                return df
            else:
                logger.warning(f"No table found for date {date}")
                return None
        
        except Exception as e:
            logger.error(f"Scraping error: {str(e)}")
            return None
        
        finally:
            time.sleep(self.delay)
    
    def scrape_mandi_prices(self, mandi_name: str, date: str) -> Optional[pd.DataFrame]:
        """
        Scrape prices for a named mandi.
        
        Args:
            mandi_name (str): Mandi name (lowercase)
            date (str): Date in DD-MM-YYYY or YYYY-MM-DD format
        
        Returns:
            pd.DataFrame: Price data
        """
        # Convert date format if needed
        if len(date.split('-')[0]) == 4:
            date = '-'.join(date.split('-')[::-1])
        
        mandi_id = self.MANDI_IDS.get(mandi_name.lower())
        if not mandi_id:
            logger.error(f"Unknown mandi: {mandi_name}")
            return None
        
        return self.scrape_prices(mandi_id, date)


# Usage Example
if __name__ == '__main__':
    scraper = MandiScraper(delay=2)
    
    today = datetime.now().strftime('%d-%m-%Y')
    data = scraper.scrape_mandi_prices('koyambedu', today)
    
    if data is not None:
        print(data.head())
```

---

## Implementation Approach 3: Database Storage

```python
# File: src/database/mandi_db.py

from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import pandas as pd
import os

Base = declarative_base()

class MandiPrice(Base):
    """SQLAlchemy model for mandi prices."""
    __tablename__ = 'mandi_prices'
    
    id = Column(Integer, primary_key=True)
    state = Column(String(50))
    mandi_id = Column(Integer)
    mandi_name = Column(String(100))
    commodity = Column(String(100))
    variety = Column(String(100))
    min_price = Column(Float)  # ₹/quintal
    max_price = Column(Float)  # ₹/quintal
    modal_price = Column(Float)  # ₹/quintal
    daily_volume = Column(Float)  # quintals
    grade = Column(String(20))
    price_date = Column(String(10))  # YYYY-MM-DD
    updated_at = Column(DateTime, default=datetime.utcnow)


class MandiDatabase:
    """Manager for mandi price database."""
    
    def __init__(self, db_url: str = None):
        """
        Initialize database connection.
        
        Args:
            db_url (str): Database URL (e.g., 'postgresql://user:pass@localhost/mandi_db')
                         If None, uses DATABASE_URL env var or SQLite fallback
        """
        if db_url is None:
            db_url = os.getenv('DATABASE_URL', 'sqlite:///mandi_prices.db')
        
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def store_prices(self, df: pd.DataFrame):
        """
        Store prices from DataFrame into database.
        
        Args:
            df (pd.DataFrame): Price data from agmarknet or scraper
        """
        session = self.Session()
        
        try:
            for _, row in df.iterrows():
                price = MandiPrice(
                    state=row.get('state', 'Tamil Nadu'),
                    mandi_id=row.get('mandi_id'),
                    mandi_name=row.get('mandi'),
                    commodity=row.get('commodity'),
                    variety=row.get('variety', '-'),
                    min_price=row.get('min_price'),
                    max_price=row.get('max_price'),
                    modal_price=row.get('modal_price'),
                    daily_volume=row.get('daily_volume', 0),
                    grade=row.get('grade', 'A'),
                    price_date=row.get('date'),
                )
                session.add(price)
            
            session.commit()
            print(f"Stored {len(df)} records")
        
        except Exception as e:
            session.rollback()
            print(f"Error storing data: {str(e)}")
        
        finally:
            session.close()
    
    def get_latest_prices(self, mandi_name: str = None, commodity: str = None) -> pd.DataFrame:
        """
        Query latest prices from database.
        
        Args:
            mandi_name (str): Optional filter by mandi
            commodity (str): Optional filter by commodity
        
        Returns:
            pd.DataFrame: Query results
        """
        session = self.Session()
        
        query = session.query(MandiPrice)
        
        if mandi_name:
            query = query.filter(MandiPrice.mandi_name.ilike(f"%{mandi_name}%"))
        
        if commodity:
            query = query.filter(MandiPrice.commodity.ilike(f"%{commodity}%"))
        
        # Order by date descending, get latest
        results = query.order_by(MandiPrice.price_date.desc()).limit(100).all()
        
        session.close()
        
        # Convert to DataFrame
        data = [{
            'mandi': r.mandi_name,
            'commodity': r.commodity,
            'min_price': r.min_price,
            'max_price': r.max_price,
            'modal_price': r.modal_price,
            'date': r.price_date,
        } for r in results]
        
        return pd.DataFrame(data)


# Usage Example
if __name__ == '__main__':
    # Initialize database
    db = MandiDatabase('sqlite:///mandi.db')
    
    # Create sample data
    sample_data = pd.DataFrame({
        'state': ['Tamil Nadu'],
        'mandi_id': [506],
        'mandi': ['Koyambedu'],
        'commodity': ['Tomato'],
        'variety': ['Local'],
        'min_price': [800.0],
        'max_price': [1200.0],
        'modal_price': [1000.0],
        'daily_volume': [250.0],
        'grade': ['A'],
        'date': ['2024-02-28'],
    })
    
    # Store in database
    db.store_prices(sample_data)
    
    # Query prices
    prices = db.get_latest_prices(mandi_name='Koyambedu', commodity='Tomato')
    print(prices)
```

---

## Daily Scheduler (Cron / APScheduler)

```python
# File: src/scheduler/daily_updater.py

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging

from src.data_sources.agmarknet_client import MandiPriceClient
from src.database.mandi_db import MandiDatabase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MandiPriceScheduler:
    """Scheduler for daily mandi price updates."""
    
    def __init__(self, db_url: str = None):
        self.client = MandiPriceClient()
        self.db = MandiDatabase(db_url)
        self.scheduler = BackgroundScheduler()
    
    def update_prices(self):
        """Fetch and store latest prices."""
        try:
            logger.info("Starting daily price update...")
            
            for mandi_name in ['koyambedu', 'krishnagiri', 'salem', 'erode']:
                prices = self.client.get_latest_prices(mandi_name)
                
                if prices is not None and not prices.empty:
                    self.db.store_prices(prices)
            
            logger.info("Daily update completed successfully")
        
        except Exception as e:
            logger.error(f"Update failed: {str(e)}")
    
    def start(self):
        """Start the scheduler."""
        # Schedule for 10:30 PM every day (after AGMARKNET updates)
        self.scheduler.add_job(
            self.update_prices,
            CronTrigger(hour=22, minute=30),
            name='daily_mandi_update'
        )
        
        self.scheduler.start()
        logger.info("Scheduler started - updates at 22:30 daily")
    
    def stop(self):
        """Stop the scheduler."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")


# Usage
if __name__ == '__main__':
    scheduler = MandiPriceScheduler()
    scheduler.start()
    
    # Keep running
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        scheduler.stop()
```

---

## Installation & Setup

```bash
# Create project structure
mkdir -p src/{data_sources,database,scheduler}
touch src/__init__.py
touch src/data_sources/__init__.py
touch src/database/__init__.py
touch src/scheduler/__init__.py

# Install dependencies
pip install -r requirements.txt

# Copy code files
# - Place agmarknet_client.py in src/data_sources/
# - Place mandi_db.py in src/database/
# - Place daily_updater.py in src/scheduler/

# Test the setup
python -m src.data_sources.agmarknet_client

# In production, run scheduler
python -m src.scheduler.daily_updater
```

## requirements.txt

```
requests==2.31.0
beautifulsoup4==4.12.0
pandas==2.1.0
python-dotenv==1.0.0
sqlalchemy==2.0.0
agmarknet-python==1.0.0
apscheduler==3.10.0
psycopg2-binary==2.9.0
```

---

**Note**: Monitor AGMARKNET website for any changes to structure. The scraper may need adjustments if DOM changes significantly.
