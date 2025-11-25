import requests
import logging
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CoinGeckoClient:
    """Client for CoinGecko API"""
    
    BASE_URL = "https://api.coingecko.com/api/v3"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COINGECKO_API_KEY
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'x-cg-demo-api-key': self.api_key
            })
    
    def get_coins_list(self) -> List[Dict]:
        """Get list of all supported coins"""
        try:
            response = self.session.get(f"{self.BASE_URL}/coins/list")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinGecko API error getting coins list: {e}")
            return []
    
    def get_coin_prices(self, coin_ids: List[str], vs_currencies: List[str] = None) -> Dict:
        """Get current prices for specified coins"""
        if vs_currencies is None:
            vs_currencies = ['usd']
        
        try:
            params = {
                'ids': ','.join(coin_ids),
                'vs_currencies': ','.join(vs_currencies),
                'include_market_cap': 'true',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_last_updated_at': 'true'
            }
            
            response = self.session.get(f"{self.BASE_URL}/simple/price", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinGecko API error getting prices: {e}")
            return {}
    
    def get_coin_market_data(self, vs_currency: str = 'usd', per_page: int = 100, page: int = 1) -> List[Dict]:
        """Get market data for coins"""
        try:
            params = {
                'vs_currency': vs_currency,
                'order': 'market_cap_desc',
                'per_page': per_page,
                'page': page,
                'sparkline': 'false',
                'price_change_percentage': '24h'
            }
            
            response = self.session.get(f"{self.BASE_URL}/coins/markets", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinGecko API error getting market data: {e}")
            return []
    
    def get_coin_history(self, coin_id: str, days: int = 30, vs_currency: str = 'usd') -> Dict:
        """Get historical price data for a coin"""
        try:
            params = {
                'vs_currency': vs_currency,
                'days': days,
                'interval': 'daily' if days > 1 else 'hourly'
            }
            
            response = self.session.get(f"{self.BASE_URL}/coins/{coin_id}/market_chart", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinGecko API error getting history for {coin_id}: {e}")
            return {}


class CoinMarketCapClient:
    """Client for CoinMarketCap API"""
    
    BASE_URL = "https://pro-api.coinmarketcap.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.COINMARKETCAP_API_KEY
        self.session = requests.Session()
        
        if self.api_key:
            self.session.headers.update({
                'X-CMC_PRO_API_KEY': self.api_key,
                'Accept': 'application/json'
            })
    
    def get_cryptocurrency_listings(self, start: int = 1, limit: int = 100, convert: str = 'USD') -> Dict:
        """Get cryptocurrency listings"""
        try:
            params = {
                'start': start,
                'limit': limit,
                'convert': convert
            }
            
            response = self.session.get(f"{self.BASE_URL}/cryptocurrency/listings/latest", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinMarketCap API error getting listings: {e}")
            return {}
    
    def get_cryptocurrency_quotes(self, symbols: List[str], convert: str = 'USD') -> Dict:
        """Get quotes for specific cryptocurrencies"""
        try:
            params = {
                'symbol': ','.join(symbols),
                'convert': convert
            }
            
            response = self.session.get(f"{self.BASE_URL}/cryptocurrency/quotes/latest", params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"CoinMarketCap API error getting quotes: {e}")
            return {}


class MarketDataService:
    """Service for managing market data from multiple sources"""
    
    def __init__(self):
        self.coingecko = CoinGeckoClient()
        self.coinmarketcap = CoinMarketCapClient()
    
    def update_cryptocurrency_prices(self) -> int:
        """Update cryptocurrency prices from CoinGecko"""
        from portfolio.models import Cryptocurrency
        
        updated_count = 0
        
        try:
            # Get market data from CoinGecko
            market_data = self.coingecko.get_coin_market_data(per_page=250)
            
            for coin_data in market_data:
                try:
                    # Try to find existing cryptocurrency by CoinGecko ID
                    crypto, created = Cryptocurrency.objects.get_or_create(
                        coingecko_id=coin_data['id'],
                        defaults={
                            'symbol': coin_data['symbol'].upper(),
                            'name': coin_data['name'],
                        }
                    )
                    
                    # Update price and market data
                    crypto.current_price_usd = Decimal(str(coin_data.get('current_price', 0)))
                    crypto.market_cap = coin_data.get('market_cap', 0) or 0
                    crypto.volume_24h = coin_data.get('total_volume', 0) or 0
                    crypto.price_change_24h = Decimal(str(coin_data.get('price_change_24h', 0) or 0))
                    crypto.price_change_percentage_24h = Decimal(str(coin_data.get('price_change_percentage_24h', 0) or 0))
                    crypto.last_price_update = timezone.now()
                    
                    # Update metadata if available
                    if coin_data.get('image'):
                        crypto.logo_url = coin_data['image']
                    
                    crypto.save()
                    updated_count += 1
                    
                except Exception as e:
                    logger.error(f"Error updating cryptocurrency {coin_data.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Updated {updated_count} cryptocurrency prices")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating cryptocurrency prices: {e}")
            return 0
    
    def get_trending_cryptocurrencies(self, limit: int = 10) -> List[Dict]:
        """Get trending cryptocurrencies"""
        try:
            market_data = self.coingecko.get_coin_market_data(per_page=limit)
            return [
                {
                    'symbol': coin['symbol'].upper(),
                    'name': coin['name'],
                    'current_price': coin.get('current_price', 0),
                    'price_change_percentage_24h': coin.get('price_change_percentage_24h', 0),
                    'market_cap': coin.get('market_cap', 0),
                    'volume_24h': coin.get('total_volume', 0),
                    'image': coin.get('image', ''),
                }
                for coin in market_data
            ]
        except Exception as e:
            logger.error(f"Error getting trending cryptocurrencies: {e}")
            return []
    
    def get_price_history(self, coingecko_id: str, days: int = 30) -> Dict:
        """Get price history for a cryptocurrency"""
        try:
            history_data = self.coingecko.get_coin_history(coingecko_id, days)
            
            if 'prices' in history_data:
                return {
                    'prices': history_data['prices'],
                    'market_caps': history_data.get('market_caps', []),
                    'total_volumes': history_data.get('total_volumes', [])
                }
            
            return {}
        except Exception as e:
            logger.error(f"Error getting price history for {coingecko_id}: {e}")
            return {}


# Global instance
market_data_service = MarketDataService()

