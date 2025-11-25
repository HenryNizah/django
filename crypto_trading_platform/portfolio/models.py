from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
import uuid

User = get_user_model()


class Cryptocurrency(models.Model):
    """Cryptocurrency information"""
    
    symbol = models.CharField(max_length=10, unique=True)  # BTC, ETH, etc.
    name = models.CharField(max_length=100)  # Bitcoin, Ethereum, etc.
    coingecko_id = models.CharField(max_length=100, unique=True)
    coinmarketcap_id = models.IntegerField(null=True, blank=True)
    
    # Market Information
    current_price_usd = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    market_cap = models.BigIntegerField(default=0)
    volume_24h = models.BigIntegerField(default=0)
    price_change_24h = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    price_change_percentage_24h = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Metadata
    logo_url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    website_url = models.URLField(blank=True)
    whitepaper_url = models.URLField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_tradeable = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_price_update = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'cryptocurrencies'
        verbose_name = 'Cryptocurrency'
        verbose_name_plural = 'Cryptocurrencies'
        ordering = ['symbol']
    
    def __str__(self):
        return f"{self.symbol} - {self.name}"


class Portfolio(models.Model):
    """User's cryptocurrency portfolio"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='portfolio')
    
    # Portfolio Statistics
    total_value_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    total_profit_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    profit_loss_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'portfolios'
        verbose_name = 'Portfolio'
        verbose_name_plural = 'Portfolios'
    
    def __str__(self):
        return f"{self.user.email}'s Portfolio"
    
    def calculate_total_value(self):
        """Calculate total portfolio value"""
        total = sum(holding.current_value_usd for holding in self.holdings.all())
        self.total_value_usd = total
        self.save()
        return total
    
    def calculate_profit_loss(self):
        """Calculate total profit/loss"""
        total_current = self.total_value_usd
        total_invested = self.total_invested
        
        if total_invested > 0:
            self.total_profit_loss = total_current - total_invested
            self.profit_loss_percentage = (self.total_profit_loss / total_invested) * 100
        else:
            self.total_profit_loss = 0
            self.profit_loss_percentage = 0
        
        self.save()
        return self.total_profit_loss


class PortfolioHolding(models.Model):
    """Individual cryptocurrency holdings in a portfolio"""
    
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    
    # Holding Information
    quantity = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    average_buy_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    total_invested = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    current_value_usd = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    
    # Performance Metrics
    unrealized_profit_loss = models.DecimalField(max_digits=20, decimal_places=2, default=0)
    unrealized_profit_loss_percentage = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_updated = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'portfolio_holdings'
        verbose_name = 'Portfolio Holding'
        verbose_name_plural = 'Portfolio Holdings'
        unique_together = ['portfolio', 'cryptocurrency']
    
    def __str__(self):
        return f"{self.portfolio.user.email} - {self.cryptocurrency.symbol}: {self.quantity}"
    
    def update_current_value(self):
        """Update current value based on latest price"""
        if self.quantity > 0:
            self.current_value_usd = self.quantity * self.cryptocurrency.current_price_usd
            self.unrealized_profit_loss = self.current_value_usd - self.total_invested
            
            if self.total_invested > 0:
                self.unrealized_profit_loss_percentage = (
                    self.unrealized_profit_loss / self.total_invested
                ) * 100
            else:
                self.unrealized_profit_loss_percentage = 0
            
            self.save()
        return self.current_value_usd


class Transaction(models.Model):
    """Transaction history for portfolio tracking"""
    
    TRANSACTION_TYPES = [
        ('buy', 'Buy'),
        ('sell', 'Sell'),
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('transfer_in', 'Transfer In'),
        ('transfer_out', 'Transfer Out'),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='transactions')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    
    # Transaction Details
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=20, decimal_places=8)
    price_per_unit = models.DecimalField(max_digits=20, decimal_places=8)
    total_amount_usd = models.DecimalField(max_digits=20, decimal_places=2)
    
    # Fees
    transaction_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    network_fee = models.DecimalField(max_digits=10, decimal_places=8, default=0)
    
    # Status and Metadata
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    transaction_hash = models.CharField(max_length=255, blank=True)  # Blockchain transaction hash
    exchange_order_id = models.CharField(max_length=255, blank=True)  # Exchange order ID
    
    # Additional Information
    notes = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    executed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_type.title()} {self.quantity} {self.cryptocurrency.symbol} - {self.user.email}"
    
    def update_portfolio_holding(self):
        """Update portfolio holding based on this transaction"""
        if self.status != 'completed':
            return
        
        holding, created = PortfolioHolding.objects.get_or_create(
            portfolio=self.portfolio,
            cryptocurrency=self.cryptocurrency,
            defaults={
                'quantity': 0,
                'average_buy_price': 0,
                'total_invested': 0,
            }
        )
        
        if self.transaction_type == 'buy':
            # Calculate new average buy price
            total_quantity = holding.quantity + self.quantity
            total_invested = holding.total_invested + self.total_amount_usd
            
            if total_quantity > 0:
                holding.average_buy_price = total_invested / total_quantity
            
            holding.quantity = total_quantity
            holding.total_invested = total_invested
            
        elif self.transaction_type == 'sell':
            # Reduce quantity and proportionally reduce total invested
            if holding.quantity >= self.quantity:
                proportion_sold = self.quantity / holding.quantity
                holding.total_invested -= holding.total_invested * proportion_sold
                holding.quantity -= self.quantity
            
        holding.save()
        holding.update_current_value()


class PriceAlert(models.Model):
    """Price alerts for cryptocurrencies"""
    
    ALERT_TYPES = [
        ('above', 'Price Above'),
        ('below', 'Price Below'),
        ('percentage_change', 'Percentage Change'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='price_alerts')
    cryptocurrency = models.ForeignKey(Cryptocurrency, on_delete=models.CASCADE)
    
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    target_price = models.DecimalField(max_digits=20, decimal_places=8, null=True, blank=True)
    percentage_change = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_triggered = models.BooleanField(default=False)
    triggered_at = models.DateTimeField(null=True, blank=True)
    
    # Notification preferences
    email_notification = models.BooleanField(default=True)
    sms_notification = models.BooleanField(default=False)
    push_notification = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'price_alerts'
        verbose_name = 'Price Alert'
        verbose_name_plural = 'Price Alerts'
    
    def __str__(self):
        return f"{self.user.email} - {self.cryptocurrency.symbol} {self.get_alert_type_display()}"
