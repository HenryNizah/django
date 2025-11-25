import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from portfolio.models import Portfolio, Cryptocurrency

User = get_user_model()


class MarketDataConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time market data"""
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.room_group_name = 'market_data'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial market data
        await self.send_market_data()
    
    async def disconnect(self, close_code):
        """Leave room group"""
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'subscribe':
                symbols = text_data_json.get('symbols', [])
                await self.subscribe_to_symbols(symbols)
            elif message_type == 'unsubscribe':
                symbols = text_data_json.get('symbols', [])
                await self.unsubscribe_from_symbols(symbols)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def market_data_update(self, event):
        """Receive market data update from room group"""
        await self.send(text_data=json.dumps({
            'type': 'market_data',
            'data': event['data']
        }))
    
    async def send_market_data(self):
        """Send current market data"""
        market_data = await self.get_market_data()
        await self.send(text_data=json.dumps({
            'type': 'market_data',
            'data': market_data
        }))
    
    async def subscribe_to_symbols(self, symbols):
        """Subscribe to specific cryptocurrency symbols"""
        # Store subscribed symbols in the consumer
        if not hasattr(self, 'subscribed_symbols'):
            self.subscribed_symbols = set()
        
        self.subscribed_symbols.update(symbols)
        
        await self.send(text_data=json.dumps({
            'type': 'subscription_confirmed',
            'symbols': list(self.subscribed_symbols)
        }))
    
    async def unsubscribe_from_symbols(self, symbols):
        """Unsubscribe from specific cryptocurrency symbols"""
        if hasattr(self, 'subscribed_symbols'):
            self.subscribed_symbols.difference_update(symbols)
        
        await self.send(text_data=json.dumps({
            'type': 'unsubscription_confirmed',
            'symbols': symbols
        }))
    
    @database_sync_to_async
    def get_market_data(self):
        """Get current market data from database"""
        cryptocurrencies = Cryptocurrency.objects.filter(is_active=True)[:20]
        return [
            {
                'symbol': crypto.symbol,
                'name': crypto.name,
                'current_price_usd': str(crypto.current_price_usd),
                'price_change_24h': str(crypto.price_change_24h),
                'price_change_percentage_24h': str(crypto.price_change_percentage_24h),
                'market_cap': crypto.market_cap,
                'volume_24h': crypto.volume_24h,
            }
            for crypto in cryptocurrencies
        ]


class PortfolioConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time portfolio updates"""
    
    async def connect(self):
        """Accept WebSocket connection for authenticated users"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_id = str(self.user.id)
        self.room_group_name = f'portfolio_{self.user_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial portfolio data
        await self.send_portfolio_data()
    
    async def disconnect(self, close_code):
        """Leave room group"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'refresh_portfolio':
                await self.send_portfolio_data()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def portfolio_update(self, event):
        """Receive portfolio update from room group"""
        await self.send(text_data=json.dumps({
            'type': 'portfolio_update',
            'data': event['data']
        }))
    
    async def send_portfolio_data(self):
        """Send current portfolio data"""
        portfolio_data = await self.get_portfolio_data()
        await self.send(text_data=json.dumps({
            'type': 'portfolio_data',
            'data': portfolio_data
        }))
    
    @database_sync_to_async
    def get_portfolio_data(self):
        """Get current portfolio data from database"""
        try:
            portfolio = Portfolio.objects.get(user=self.user)
            holdings = portfolio.holdings.select_related('cryptocurrency').all()
            
            return {
                'total_value_usd': str(portfolio.total_value_usd),
                'total_invested': str(portfolio.total_invested),
                'total_profit_loss': str(portfolio.total_profit_loss),
                'profit_loss_percentage': str(portfolio.profit_loss_percentage),
                'holdings': [
                    {
                        'symbol': holding.cryptocurrency.symbol,
                        'name': holding.cryptocurrency.name,
                        'quantity': str(holding.quantity),
                        'current_value_usd': str(holding.current_value_usd),
                        'unrealized_profit_loss': str(holding.unrealized_profit_loss),
                        'unrealized_profit_loss_percentage': str(holding.unrealized_profit_loss_percentage),
                    }
                    for holding in holdings
                ]
            }
        except Portfolio.DoesNotExist:
            return {
                'total_value_usd': '0.00',
                'total_invested': '0.00',
                'total_profit_loss': '0.00',
                'profit_loss_percentage': '0.00',
                'holdings': []
            }


class TradingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time trading updates"""
    
    async def connect(self):
        """Accept WebSocket connection for authenticated users"""
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
        
        self.user_id = str(self.user.id)
        self.room_group_name = f'trading_{self.user_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Leave room group"""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong'
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'error': 'Invalid JSON format'
            }))
    
    async def trading_update(self, event):
        """Receive trading update from room group"""
        await self.send(text_data=json.dumps({
            'type': 'trading_update',
            'data': event['data']
        }))
    
    async def order_update(self, event):
        """Receive order update from room group"""
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'data': event['data']
        }))

