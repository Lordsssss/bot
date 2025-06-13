"""
Crypto chart generator with customizable timelines
"""
import discord
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
import re

from .models import CryptoModels
from bot.utils.discord_helpers import create_embed


class ChartGenerator:
    """Generate crypto price charts with flexible timelines"""
    
    @staticmethod
    def parse_timeline(timeline_str: str) -> Tuple[bool, float, str]:
        """
        Parse timeline string into hours
        Returns: (is_valid, hours, error_message)
        
        Supported formats:
        - "5m", "30m" (minutes)
        - "1h", "2h", "24h" (hours)  
        - "1d", "7d" (days)
        - Just numbers default to hours: "2" = "2h"
        """
        if not timeline_str:
            return False, 0, "Timeline cannot be empty"
        
        timeline_str = timeline_str.lower().strip()
        
        # Try to match pattern like "5m", "2h", "1d"
        match = re.match(r'^(\d+(?:\.\d+)?)\s*([mhd]?)$', timeline_str)
        
        if not match:
            return False, 0, f"Invalid timeline format: '{timeline_str}'. Use formats like '5m', '2h', '1d' or just '2' for hours"
        
        value_str, unit = match.groups()
        
        try:
            value = float(value_str)
        except ValueError:
            return False, 0, f"Invalid number: '{value_str}'"
        
        if value <= 0:
            return False, 0, "Timeline must be positive"
        
        # Convert to hours based on unit
        if unit == 'm':
            hours = value / 60.0
            if hours > 24:  # Limit minutes to 24 hours max
                return False, 0, "Timeline too long for minutes (max 24 hours)"
        elif unit == 'd':
            hours = value * 24
            if hours > 24 * 30:  # Limit to 30 days max
                return False, 0, "Timeline too long (max 30 days)"
        else:  # 'h' or no unit (defaults to hours)
            hours = value
            if hours > 24 * 7:  # Limit to 7 days max for hours
                return False, 0, "Timeline too long (max 7 days)"
        
        # Minimum 1 minute
        if hours < 1/60:
            return False, 0, "Timeline too short (minimum 1 minute)"
        
        return True, hours, ""
    
    @staticmethod
    def format_timeline_display(hours: float) -> str:
        """Format hours back to readable string for display"""
        if hours < 1:
            minutes = int(hours * 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''}"
        elif hours < 24:
            if hours == int(hours):
                return f"{int(hours)} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours:.1f} hours"
        else:
            days = hours / 24
            if days == int(days):
                return f"{int(days)} day{'s' if days != 1 else ''}"
            else:
                return f"{days:.1f} days"
    
    @staticmethod
    async def generate_chart(tickers: List[str], coin_data: Dict[str, Any], hours: float) -> Tuple[discord.File, discord.Embed]:
        """Generate price chart for given tickers and timeline"""
        
        # Configure chart style
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(14, 8))
        
        colors = ['#00ff00', '#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', 
                 '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43',
                 '#ff6348', '#2ed573', '#3742fa', '#f368e0', '#feca57']
        
        chart_data = {}
        
        # Get data for each ticker
        for i, ticker in enumerate(tickers):
            price_history = await CryptoModels.get_price_history(ticker, hours=hours)
            
            if len(price_history) < 2:
                continue
            
            times = [p['timestamp'] for p in price_history]
            prices = [p['price'] for p in price_history]
            
            # For single crypto, show actual prices. For multiple, show percentage change
            if len(tickers) == 1:
                plot_values = prices
                ylabel = 'Price ($)'
            else:
                # Multiple cryptos - normalize to percentage change for comparison
                base_price = prices[0]
                plot_values = [(p / base_price - 1) * 100 for p in prices]
                ylabel = 'Price Change (%)'
            
            chart_data[ticker] = {
                'times': times,
                'prices': prices,
                'plot_values': plot_values,
                'coin': coin_data[ticker],
                'color': colors[i % len(colors)]
            }
        
        if not chart_data:
            raise Exception(f"Not enough price data for the last {ChartGenerator.format_timeline_display(hours)}. Try a shorter timeframe.")
        
        # Plot all lines
        for ticker, data in chart_data.items():
            ax.plot(data['times'], data['plot_values'], 
                   color=data['color'], linewidth=2, 
                   marker='o' if len(tickers) == 1 else '.', 
                   markersize=4 if len(tickers) == 1 else 2,
                   label=f"{ticker}" if len(tickers) > 1 else f"{ticker} ({data['coin']['name']})", 
                   alpha=0.9)
        
        # Configure chart appearance
        timeline_display = ChartGenerator.format_timeline_display(hours)
        
        if len(tickers) == 1:
            title = f"{coin_data[tickers[0]]['name']} ({tickers[0]}) - {timeline_display}"
        elif len(tickers) <= 3:
            title = f"Crypto Comparison - {', '.join(tickers)} ({timeline_display})"
        else:
            title = f"Crypto Comparison ({len(tickers)} coins) - {timeline_display}"
        
        ax.set_title(title, fontsize=16, color='white', pad=20)
        ax.set_xlabel('Time', fontsize=12, color='white')
        ax.set_ylabel(ylabel, fontsize=12, color='white')
        
        # Format x-axis based on timeline
        ChartGenerator._format_time_axis(ax, hours)
        
        plt.xticks(rotation=45)
        ax.grid(True, alpha=0.3, color='gray')
        
        if len(tickers) > 1:
            ax.legend(loc='upper left', fontsize=9, ncol=2 if len(tickers) > 6 else 1)
            ax.axhline(y=0, color='white', linestyle='--', alpha=0.5)
        
        # Add annotations for single crypto
        if len(tickers) == 1:
            ChartGenerator._add_single_crypto_annotations(ax, chart_data[tickers[0]])
        
        # Add stats box
        ChartGenerator._add_stats_box(ax, chart_data, tickers)
        
        plt.tight_layout()
        
        # Save to bytes
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', facecolor='#2f3136', dpi=100)
        img_buffer.seek(0)
        plt.close()
        
        # Create file and embed
        filename = f"{tickers[0]}_chart_{hours}h.png" if len(tickers) == 1 else f"crypto_comparison_{hours}h.png"
        file = discord.File(img_buffer, filename=filename)
        
        # Create embed
        embed = ChartGenerator._create_chart_embed(chart_data, tickers, timeline_display, filename)
        
        return file, embed
    
    @staticmethod
    def _format_time_axis(ax, hours: float):
        """Format x-axis based on timeline length"""
        if hours <= 1:  # 1 hour or less - show every 10 minutes
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=10))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif hours <= 6:  # 6 hours or less - show every 30 minutes
            ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif hours <= 24:  # 24 hours or less - show every 2 hours
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        elif hours <= 72:  # 3 days or less - show every 6 hours
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
        else:  # More than 3 days - show every day
            ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
    
    @staticmethod
    def _add_single_crypto_annotations(ax, data: Dict[str, Any]):
        """Add annotations for single crypto charts"""
        current_price = data['coin']['current_price']
        
        # Current price annotation
        ax.annotate(f'${current_price:.4f}', 
                   xy=(data['times'][-1], data['prices'][-1]), 
                   xytext=(10, 10), 
                   textcoords='offset points',
                   bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.8),
                   arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                   fontsize=12, color='black', weight='bold')
    
    @staticmethod
    def _add_stats_box(ax, chart_data: Dict[str, Dict[str, Any]], tickers: List[str]):
        """Add statistics box to chart"""
        if len(tickers) == 1:
            # Detailed stats for single crypto
            ticker = tickers[0]
            data = chart_data[ticker]
            current_price = data['coin']['current_price']
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            stats_text = f"Current: ${current_price:.4f}\n"
            stats_text += f"Change: {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
            stats_text += f"High: ${max(data['prices']):.4f}\n"
            stats_text += f"Low: ${min(data['prices']):.4f}\n"
            stats_text += f"Volatility: {data['coin']['daily_volatility']:.2f}"
            
            box_x, box_ha = 0.02, 'left'
        else:
            # Summary stats for multiple cryptos
            stats_text = "Performance:\n"
            performance_data = []
            
            for ticker, data in chart_data.items():
                current_price = data['coin']['current_price']
                change_pct = data['plot_values'][-1]
                performance_data.append((ticker, current_price, change_pct))
            
            # Sort by performance (best first)
            performance_data.sort(key=lambda x: x[2], reverse=True)
            
            # Show top performers (limit to 8 lines in stats box)
            for ticker, current_price, change_pct in performance_data[:8]:
                stats_text += f"{ticker}: ${current_price:.4f} ({change_pct:+.2f}%)\n"
            
            if len(performance_data) > 8:
                stats_text += f"... and {len(performance_data) - 8} more"
            
            box_x, box_ha = 0.98, 'right'
        
        ax.text(box_x, 0.98, stats_text, transform=ax.transAxes, 
                verticalalignment='top', horizontalalignment=box_ha,
                bbox=dict(boxstyle='round', facecolor='black', alpha=0.8),
                fontsize=9, color='white')
    
    @staticmethod
    def _create_chart_embed(chart_data: Dict[str, Dict[str, Any]], tickers: List[str], 
                          timeline_display: str, filename: str) -> discord.Embed:
        """Create Discord embed for chart"""
        if len(tickers) == 1:
            # Single crypto embed
            ticker = tickers[0]
            data = chart_data[ticker]
            current_price = data['coin']['current_price']
            price_change = data['prices'][-1] - data['prices'][0]
            price_change_percent = (price_change / data['prices'][0]) * 100
            
            embed = create_embed(
                title=f"📈 {data['coin']['name']} ({ticker})",
                description=(
                    f"**Current Price:** ${current_price:.4f}\n"
                    f"**Change:** {price_change:+.4f} ({price_change_percent:+.2f}%)\n"
                    f"**Volatility:** {data['coin']['daily_volatility']:.2f}"
                ),
                color=0x00ff00 if price_change >= 0 else 0xff0000,
                footer=f"Chart shows {timeline_display} of trading data"
            )
        else:
            # Multiple cryptos embed
            description = f"**Comparing {len(tickers)} cryptocurrencies over {timeline_display}**\n\n"
            
            # Show top 5 performers in embed
            performance_data = []
            for ticker, data in chart_data.items():
                current_price = data['coin']['current_price']
                change_pct = data['plot_values'][-1]
                performance_data.append((ticker, current_price, change_pct))
            
            performance_data.sort(key=lambda x: x[2], reverse=True)
            
            for ticker, current_price, change_pct in performance_data[:5]:
                description += f"**{ticker}:** ${current_price:.4f} ({change_pct:+.2f}%)\n"
            
            if len(performance_data) > 5:
                description += f"\n*... and {len(performance_data) - 5} more cryptos*"
            
            embed = create_embed(
                title="📈 Crypto Comparison Chart",
                description=description,
                color=0x00ff00,
                footer=f"Chart shows percentage change over {timeline_display} | All lines superposed for comparison"
            )
        
        embed.set_image(url=f"attachment://{filename}")
        return embed