"""
WebSocket simulator for real-time NAV updates and anomaly events.
Simulates live data streaming for demo purposes.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import List, Set
import numpy as np

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        """Send message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass


# Global connection manager
manager = ConnectionManager()


# Sample fund data for simulation fallback
SAMPLE_FUNDS = [
    {'code': 'MF001', 'name': 'Blue Chip Growth Fund', 'category': 'Large Cap', 'base_nav': 245.50},
    {'code': 'MF002', 'name': 'Stable Income Fund', 'category': 'Debt', 'base_nav': 125.30},
    {'code': 'MF003', 'name': 'Tech Innovation Fund', 'category': 'Sectoral', 'base_nav': 89.75},
    {'code': 'MF004', 'name': 'Balanced Advantage Fund', 'category': 'Hybrid', 'base_nav': 156.40},
    {'code': 'MF005', 'name': 'Small Cap Opportunities', 'category': 'Small Cap', 'base_nav': 67.80},
    {'code': 'MF006', 'name': 'Government Securities Fund', 'category': 'Gilt', 'base_nav': 42.15},
    {'code': 'MF007', 'name': 'Emerging Markets Fund', 'category': 'International', 'base_nav': 198.60},
    {'code': 'MF008', 'name': 'Healthcare Sector Fund', 'category': 'Sectoral', 'base_nav': 312.25},
    {'code': 'MF009', 'name': 'ESG Leaders Fund', 'category': 'Thematic', 'base_nav': 78.90},
    {'code': 'MF010', 'name': 'Global Equity Fund', 'category': 'International', 'base_nav': 445.00},
]

# Current simulated NAV values
current_navs = {}
_simulation_funds = []


def _load_simulation_funds():
    """Load simulation funds from dataset; fallback to samples."""
    global _simulation_funds, current_navs

    if _simulation_funds:
        return _simulation_funds

    try:
        from .data_loader import get_fund_list
        funds = get_fund_list()
        if funds:
            _simulation_funds = [
                {
                    'code': f['scheme_code'],
                    'name': f['fund_name'],
                    'category': f['category'],
                    'base_nav': f['latest_nav'],
                }
                for f in funds
            ]
    except Exception:
        _simulation_funds = []

    if not _simulation_funds:
        _simulation_funds = SAMPLE_FUNDS

    current_navs = {f['code']: f['base_nav'] for f in _simulation_funds}
    return _simulation_funds


def generate_nav_update() -> dict:
    """Generate a simulated NAV update for a random fund."""
    funds = _load_simulation_funds()
    fund = random.choice(funds)
    code = fund['code']
    
    # Simulate price movement
    volatility = 0.005 if fund['category'] in ['Debt', 'Gilt'] else 0.015
    change_pct = np.random.normal(0, volatility)
    
    # Occasionally inject larger moves (potential anomalies)
    if random.random() < 0.05:
        change_pct = random.choice([-1, 1]) * random.uniform(0.02, 0.05)
    
    new_nav = current_navs[code] * (1 + change_pct)
    current_navs[code] = new_nav
    
    # Calculate z-score approximation
    zscore = change_pct / volatility
    is_anomaly = abs(zscore) > 2
    
    return {
        'type': 'nav_update',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'scheme_code': code,
            'fund_name': fund['name'],
            'category': fund['category'],
            'nav': round(new_nav, 4),
            'change_pct': round(change_pct * 100, 3),
            'zscore': round(zscore, 2),
            'is_anomaly': is_anomaly,
        }
    }


def generate_anomaly_event() -> dict:
    """Generate a simulated anomaly alert."""
    funds = _load_simulation_funds()
    fund = random.choice(funds)
    
    severity = random.choice(['high', 'medium'])
    direction = random.choice(['up', 'down'])
    zscore = random.uniform(2.2, 4.5) * (1 if direction == 'up' else -1)
    
    explanations = [
        f"Unusual NAV {'increase' if direction == 'up' else 'decrease'} detected",
        f"Significant deviation from rolling mean (z-score: {abs(zscore):.1f})",
        f"{'Major' if severity == 'high' else 'Moderate'} volatility spike observed",
        f"{fund['category']} sector showing abnormal movement",
    ]
    
    signals = [
        f"{fund['category']} fund {'spike' if direction == 'up' else 'drop'} detected",
        f"Volatility alert: {fund['name']}",
        f"Anomaly detected in {fund['category']} sector",
        f"Risk alert: {fund['name']} deviation",
    ]
    
    return {
        'type': 'anomaly',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'id': f"anom_{fund['code']}_{datetime.now().strftime('%H%M%S')}",
            'scheme_code': fund['code'],
            'fund_name': fund['name'],
            'category': fund['category'],
            'severity': severity,
            'direction': direction,
            'zscore': round(zscore, 2),
            'nav': round(current_navs[fund['code']], 4),
            'signal': random.choice(signals),
            'explanation': random.choice(explanations),
            'confidence': round(random.uniform(0.7, 0.95), 2),
        }
    }


def generate_market_summary() -> dict:
    """Generate market summary statistics."""
    funds = _load_simulation_funds()
    total_up = sum(1 for code in current_navs if random.random() > 0.45)
    total_down = len(current_navs) - total_up
    
    return {
        'type': 'market_summary',
        'timestamp': datetime.now().isoformat(),
        'data': {
            'total_funds': len(funds),
            'funds_up': total_up,
            'funds_down': total_down,
            'anomaly_count': random.randint(0, 3),
            'avg_change': round(random.uniform(-0.5, 0.5), 2),
            'market_status': 'active',
        }
    }


async def simulate_stream(websocket: WebSocket):
    """
    Main simulation loop for WebSocket streaming.
    Sends various types of updates at random intervals.
    """
    await manager.connect(websocket)
    
    try:
        # Send initial market summary
        await websocket.send_json(generate_market_summary())
        
        # Counter for periodic events
        tick_count = 0
        
        while True:
            tick_count += 1
            
            # Generate event based on probability
            event_type = random.random()
            
            if event_type < 0.6:
                # NAV update (most common)
                message = generate_nav_update()
            elif event_type < 0.85:
                # Anomaly event
                message = generate_anomaly_event()
            else:
                # Market summary
                message = generate_market_summary()
            
            await websocket.send_json(message)
            
            # Random delay between 0.5 and 3 seconds
            delay = random.uniform(0.5, 3.0)
            await asyncio.sleep(delay)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        manager.disconnect(websocket)


async def broadcast_update(message: dict):
    """Broadcast an update to all connected clients."""
    await manager.broadcast(message)


class HistoricalSimulator:
    """
    Simulates streaming through historical data.
    Iterates through dates and sends anomaly events.
    """
    
    def __init__(self, df):
        self.df = df.sort_values(['date', 'scheme_code'])
        self.current_index = 0
        self.dates = sorted(df['date'].unique())
    
    def reset(self):
        self.current_index = 0
    
    def get_next_batch(self, batch_size: int = 10) -> List[dict]:
        """Get next batch of historical records."""
        if self.current_index >= len(self.dates):
            self.reset()
        
        events = []
        current_date = self.dates[self.current_index]
        date_data = self.df[self.df['date'] == current_date]
        
        for _, row in date_data.head(batch_size).iterrows():
            if row.get('is_anomaly', False):
                events.append({
                    'type': 'historical_anomaly',
                    'timestamp': row['date'].isoformat(),
                    'data': {
                        'scheme_code': row['scheme_code'],
                        'fund_name': row.get('scheme_name', ''),
                        'nav': round(row['nav'], 4),
                        'zscore': round(row.get('zscore', 0), 2),
                        'severity': row.get('severity', 'medium'),
                        'explanation': row.get('explanation', 'Anomaly detected'),
                    }
                })
        
        self.current_index += 1
        return events
