"""
Data loader for mutual fund NAV dataset.
Loads historical NAV data from parquet file, computes rolling metrics.
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Data path - parquet file
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "nav"
PARQUET_FILE = DATA_DIR / "mutual_fund_nav_history.parquet"

# Performance settings for demo
MAX_FUNDS = 200          # Limit number of funds for fast loading
MAX_ROWS_PER_SCHEME = 60 # Only keep latest 60 NAV records per fund
MAX_DETAIL_POINTS = 60   # Chart detail points

# Cache for loaded data
_nav_cache: Optional[pd.DataFrame] = None
_scheme_cache: Optional[pd.DataFrame] = None
_processed_cache: Optional[pd.DataFrame] = None
_overview_cache: Optional[Dict] = None


def _clear_cache():
    """Clear all cached data to force reload."""
    global _nav_cache, _scheme_cache, _processed_cache, _overview_cache
    _nav_cache = None
    _scheme_cache = None
    _processed_cache = None
    _overview_cache = None


def _safe_str(value, default: str) -> str:
    """Return a safe string value for API responses."""
    if value is None:
        return default

    # Reject datetime-like values
    if isinstance(value, (pd.Timestamp, datetime)):
        return default

    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return default

        # Reject date-like strings used as names
        try:
            parsed = pd.to_datetime(trimmed, errors='raise')
            if pd.notna(parsed):
                return default
        except Exception:
            pass

        return trimmed

    return default


def _safe_float(value, default: float = 0.0) -> float:
    """Return a finite float value for API responses."""
    try:
        val = float(value)
    except Exception:
        return default
    return val if np.isfinite(val) else default


def load_nav_data() -> pd.DataFrame:
    """Load historical NAV data from parquet file."""
    global _nav_cache
    
    if _nav_cache is not None:
        return _nav_cache
    
    if not PARQUET_FILE.exists():
        # Generate sample data if file doesn't exist
        print(f"⚠️ Parquet file not found at {PARQUET_FILE}")
        print("   Generating sample data for demo...")
        _nav_cache = generate_sample_nav_data()
        return _nav_cache
    
    print(f"📊 Loading NAV data from {PARQUET_FILE}")
    df = pd.read_parquet(PARQUET_FILE)
    
    # Reset index if scheme_code is stored as index (e.g., "Scheme_Code")
    if df.index.name and 'scheme' in df.index.name.lower():
        df = df.reset_index()
        print(f"   ↳ Reset index '{df.columns[0]}' to column")
    
    # Standardize column names to lowercase and normalize separators
    df.columns = [re.sub(r"[^a-z0-9]+", "_", str(c).lower().strip()).strip("_") for c in df.columns]
    
    # Map common column name variations
    column_mapping = {
        'code': 'scheme_code',
        'fund_code': 'scheme_code',
        'scheme': 'scheme_code',
        'scheme_code': 'scheme_code',
        'scheme_code_id': 'scheme_code',
        'schemeid': 'scheme_code',
        'scheme_id': 'scheme_code',
        'scheme_code_no': 'scheme_code',
        'name': 'scheme_name',
        'fund_name': 'scheme_name',
        'category_name': 'category',
        'scheme_category': 'category',
        'fund_category': 'category',
        'value': 'nav',
        'net_asset_value': 'nav',
    }
    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
    
    # Ensure required columns exist
    if 'scheme_code' not in df.columns:
        df['scheme_code'] = df.iloc[:, 0]
    
    if 'date' not in df.columns:
        date_cols = [c for c in df.columns if 'date' in c.lower()]
        if date_cols:
            df['date'] = df[date_cols[0]]
    
    # Convert types - scheme_code must be string, date must be datetime
    df['scheme_code'] = df['scheme_code'].astype(str)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['nav'] = pd.to_numeric(df['nav'], errors='coerce')
    
    # Drop invalid rows
    df = df.dropna(subset=['date', 'nav', 'scheme_code'])

    # If scheme_code looks like a date column, try to find a better code column
    def _is_mostly_date_like(series: pd.Series) -> bool:
        sample = series.dropna().astype(str).head(200)
        if sample.empty:
            return False
        parsed = pd.to_datetime(sample, errors='coerce')
        return parsed.notna().mean() > 0.8

    if _is_mostly_date_like(df['scheme_code']):
        candidate_cols = [c for c in df.columns if 'code' in c or 'scheme' in c]
        for col in candidate_cols:
            if col == 'scheme_code':
                continue
            if not _is_mostly_date_like(df[col]):
                df['scheme_code'] = df[col].astype(str)
                break
    
    # Sort by scheme and date
    df = df.sort_values(['scheme_code', 'date'])

    # Limit to MAX_FUNDS random funds for demo performance
    unique_schemes = df['scheme_code'].unique()
    if len(unique_schemes) > MAX_FUNDS:
        # Pick a diverse sample of funds
        np.random.seed(42)  # Reproducible sampling
        selected_schemes = np.random.choice(unique_schemes, MAX_FUNDS, replace=False)
        df = df[df['scheme_code'].isin(selected_schemes)]
        print(f"   ↳ Sampled {MAX_FUNDS} funds from {len(unique_schemes)} total")
    
    # Keep only latest N records per scheme
    df = df.groupby('scheme_code', group_keys=False).tail(MAX_ROWS_PER_SCHEME)
    
    print(f"✅ Loaded {len(df):,} NAV records for {df['scheme_code'].nunique()} funds")
    
    _nav_cache = df
    return df


def load_scheme_details() -> pd.DataFrame:
    """Extract scheme details from NAV data."""
    global _scheme_cache
    
    if _scheme_cache is not None:
        return _scheme_cache
    
    # Try to extract from NAV data
    nav_df = load_nav_data()
    
    # Check if we have scheme details in the NAV data
    detail_cols = ['scheme_code']
    if 'scheme_name' in nav_df.columns:
        detail_cols.append('scheme_name')
    if 'category' in nav_df.columns:
        detail_cols.append('category')
    if 'fund_type' in nav_df.columns:
        detail_cols.append('fund_type')
    
    if len(detail_cols) > 1:
        # Extract unique scheme details
        df = nav_df[detail_cols].drop_duplicates('scheme_code')
    else:
        # Generate sample scheme data
        df = generate_sample_scheme_data()

    # Normalize types for safe merges and API responses
    if 'scheme_code' in df.columns:
        df['scheme_code'] = df['scheme_code'].astype(str)
    for col in ['scheme_name', 'category', 'fund_type']:
        if col in df.columns:
            df[col] = df[col].fillna('')
    
    _scheme_cache = df
    return df


def generate_sample_nav_data() -> pd.DataFrame:
    """Generate sample NAV data for demo purposes."""
    np.random.seed(42)
    
    schemes = [
        ('MF001', 'Blue Chip Growth Fund'),
        ('MF002', 'Stable Income Fund'),
        ('MF003', 'Tech Innovation Fund'),
        ('MF004', 'Balanced Advantage Fund'),
        ('MF005', 'Small Cap Opportunities'),
        ('MF006', 'Government Securities Fund'),
        ('MF007', 'Emerging Markets Fund'),
        ('MF008', 'Healthcare Sector Fund'),
        ('MF009', 'ESG Leaders Fund'),
        ('MF010', 'Global Equity Fund'),
        ('MF011', 'Infrastructure Fund'),
        ('MF012', 'Banking & Financial Fund'),
        ('MF013', 'Energy Sector Fund'),
        ('MF014', 'Consumer Goods Fund'),
        ('MF015', 'Real Estate Fund'),
    ]
    
    # Generate 2 years of daily data
    dates = pd.date_range(start='2024-01-01', end='2026-02-01', freq='B')
    
    records = []
    for scheme_code, scheme_name in schemes:
        base_nav = np.random.uniform(50, 500)
        volatility = np.random.uniform(0.005, 0.025)
        
        nav = base_nav
        for date in dates:
            # Random walk with occasional spikes (anomalies)
            change = np.random.normal(0.0003, volatility)
            
            # Inject anomalies randomly
            if np.random.random() < 0.02:
                change = np.random.choice([-1, 1]) * np.random.uniform(0.03, 0.08)
            
            nav = nav * (1 + change)
            records.append({
                'scheme_code': scheme_code,
                'scheme_name': scheme_name,
                'date': date,
                'nav': round(nav, 4)
            })
    
    return pd.DataFrame(records)


def generate_sample_scheme_data() -> pd.DataFrame:
    """Generate sample scheme details."""
    schemes = [
        ('MF001', 'Blue Chip Growth Fund', 'Large Cap', 'Equity'),
        ('MF002', 'Stable Income Fund', 'Debt', 'Debt'),
        ('MF003', 'Tech Innovation Fund', 'Sectoral', 'Equity'),
        ('MF004', 'Balanced Advantage Fund', 'Hybrid', 'Hybrid'),
        ('MF005', 'Small Cap Opportunities', 'Small Cap', 'Equity'),
        ('MF006', 'Government Securities Fund', 'Gilt', 'Debt'),
        ('MF007', 'Emerging Markets Fund', 'International', 'Equity'),
        ('MF008', 'Healthcare Sector Fund', 'Sectoral', 'Equity'),
        ('MF009', 'ESG Leaders Fund', 'Thematic', 'Equity'),
        ('MF010', 'Global Equity Fund', 'International', 'Equity'),
        ('MF011', 'Infrastructure Fund', 'Sectoral', 'Equity'),
        ('MF012', 'Banking & Financial Fund', 'Sectoral', 'Equity'),
        ('MF013', 'Energy Sector Fund', 'Sectoral', 'Equity'),
        ('MF014', 'Consumer Goods Fund', 'Sectoral', 'Equity'),
        ('MF015', 'Real Estate Fund', 'Sectoral', 'Equity'),
    ]
    
    return pd.DataFrame(schemes, columns=['scheme_code', 'scheme_name', 'category', 'fund_type'])


def compute_rolling_metrics(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Compute rolling metrics for each scheme.
    - daily returns
    - rolling mean
    - rolling std
    - z-score
    """
    global _processed_cache
    
    if _processed_cache is not None:
        return _processed_cache
    
    df = df.copy()
    df = df.sort_values(['scheme_code', 'date'])
    
    # Compute daily returns
    df['daily_return'] = df.groupby('scheme_code')['nav'].pct_change()
    
    # Compute rolling statistics
    df['rolling_mean'] = df.groupby('scheme_code')['daily_return'].transform(
        lambda x: x.rolling(window=window, min_periods=5).mean()
    )
    df['rolling_std'] = df.groupby('scheme_code')['daily_return'].transform(
        lambda x: x.rolling(window=window, min_periods=5).std()
    )
    
    # Compute z-score
    df['zscore'] = (df['daily_return'] - df['rolling_mean']) / df['rolling_std']
    df['zscore'] = df['zscore'].fillna(0)
    
    # Compute volatility (annualized)
    df['volatility'] = df['rolling_std'] * np.sqrt(252)
    
    # Compute drawdown
    df['cummax'] = df.groupby('scheme_code')['nav'].cummax()
    df['drawdown'] = (df['nav'] - df['cummax']) / df['cummax']

    # Replace non-finite values to keep API responses JSON-safe
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df['daily_return'] = df['daily_return'].fillna(0)
    df['rolling_mean'] = df['rolling_mean'].fillna(0)
    df['rolling_std'] = df['rolling_std'].fillna(0)
    df['zscore'] = df['zscore'].fillna(0)
    df['volatility'] = df['volatility'].fillna(0)
    df['drawdown'] = df['drawdown'].fillna(0)
    
    _processed_cache = df
    return df


def get_processed_data() -> pd.DataFrame:
    """Get fully processed NAV data with all metrics."""
    nav_df = load_nav_data()
    scheme_df = load_scheme_details()
    
    # Merge with scheme details
    if 'scheme_name' not in nav_df.columns:
        nav_df = nav_df.merge(scheme_df, on='scheme_code', how='left')
    
    return compute_rolling_metrics(nav_df)


def get_fund_list() -> List[Dict]:
    """Get list of all funds with latest metrics."""
    df = get_processed_data()
    scheme_df = load_scheme_details()
    
    # Get latest record for each scheme
    latest = df.sort_values('date').groupby('scheme_code').last().reset_index()
    
    # Merge with scheme details
    if 'category' not in latest.columns:
        latest = latest.merge(scheme_df[['scheme_code', 'category', 'fund_type']],
                              on='scheme_code', how='left')

    # Normalize string fields to avoid NaN validation errors
    for col in ['scheme_name', 'category', 'fund_type']:
        if col in latest.columns:
            latest[col] = latest[col].fillna('')
    
    funds = []
    for _, row in latest.iterrows():
        scheme_code = str(row['scheme_code'])
        fund_name = scheme_code
        category = _safe_str(row.get('category', ''), 'Unknown')
        fund_type = _safe_str(row.get('fund_type', ''), 'Unknown')

        funds.append({
            'scheme_code': scheme_code,
            'fund_name': fund_name,
            'category': category,
            'fund_type': fund_type,
            'latest_nav': round(_safe_float(row.get('nav', 0)), 2),
            'daily_return': round(_safe_float(row.get('daily_return', 0)) * 100, 2),
            'volatility': round(_safe_float(row.get('volatility', 0)) * 100, 2),
            'anomaly_flag': abs(_safe_float(row.get('zscore', 0))) > 2,
            'zscore': round(_safe_float(row.get('zscore', 0)), 2),
            'drawdown': round(_safe_float(row.get('drawdown', 0)) * 100, 2),
        })
    
    return funds


def get_fund_details(scheme_code: str) -> Dict:
    """Get detailed data for a specific fund."""
    df = get_processed_data()
    scheme_df = load_scheme_details()
    
    fund_df = df[df['scheme_code'] == scheme_code].copy()
    
    if fund_df.empty:
        return None
    
    # Get scheme info
    scheme_info = scheme_df[scheme_df['scheme_code'] == scheme_code]
    fund_name = scheme_code
    category = _safe_str(
        scheme_info['category'].iloc[0] if not scheme_info.empty and 'category' in scheme_info.columns else '',
        'Unknown'
    )
    
    # Prepare history (cap to recent points for responsiveness)
    fund_df = fund_df.sort_values('date')
    if MAX_DETAIL_POINTS and len(fund_df) > MAX_DETAIL_POINTS:
        fund_df = fund_df.tail(MAX_DETAIL_POINTS)
    
    history = []
    anomalies = []
    
    for _, row in fund_df.iterrows():
        record = {
            'date': row['date'].strftime('%Y-%m-%d'),
            'nav': round(_safe_float(row.get('nav', 0)), 4),
            'daily_return': round(_safe_float(row.get('daily_return', 0)) * 100, 4),
            'zscore': round(_safe_float(row.get('zscore', 0)), 2),
            'volatility': round(_safe_float(row.get('volatility', 0)) * 100, 2),
        }
        history.append(record)
        
        if abs(_safe_float(row.get('zscore', 0))) > 2:
            anomalies.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'nav': round(_safe_float(row.get('nav', 0)), 4),
                'zscore': round(_safe_float(row.get('zscore', 0)), 2),
                'severity': 'high' if abs(_safe_float(row.get('zscore', 0))) > 3 else 'medium',
                'direction': 'up' if _safe_float(row.get('zscore', 0)) > 0 else 'down',
            })
    
    latest = fund_df.iloc[-1]
    
    return {
        'scheme_code': scheme_code,
        'fund_name': fund_name,
        'category': category,
        'latest_nav': round(_safe_float(latest.get('nav', 0)), 2),
        'volatility': round(_safe_float(latest.get('volatility', 0)) * 100, 2),
        'drawdown': round(_safe_float(latest.get('drawdown', 0)) * 100, 2),
        'total_return': round((_safe_float(latest.get('nav', 0)) / max(_safe_float(fund_df.iloc[0].get('nav', 0)), 1e-9) - 1) * 100, 2),
        'history': history,
        'anomalies': anomalies,
        'anomaly_count': len(anomalies),
    }


def get_overview() -> Dict:
    """Get overall dashboard statistics."""
    global _overview_cache

    if _overview_cache is not None:
        return _overview_cache

    df = get_processed_data()
    
    # Get latest records
    latest = df.sort_values('date').groupby('scheme_code').last().reset_index()

    # Use recent window for realistic headline metrics
    max_date = df['date'].max()
    window_start = max_date - pd.Timedelta(days=30)
    recent_df = df[df['date'] >= window_start]
    if recent_df.empty:
        recent_df = df

    # Normalize category values for grouping
    if 'category' not in latest.columns:
        latest['category'] = 'Unknown'
    else:
        latest['category'] = latest['category'].fillna('Unknown').replace('', 'Unknown')
    
    total_funds = len(latest)
    funds_in_anomaly = len(latest[latest['zscore'].abs() > 2])
    
    # Category stats (recent window)
    category_stats = recent_df.groupby('category').agg({
        'scheme_code': 'count',
        'daily_return': 'mean',
        'volatility': 'mean',
    }).reset_index()
    category_stats.columns = ['category', 'count', 'avg_return', 'avg_volatility']

    # Headline metrics based on recent window
    avg_nav_change = recent_df['daily_return'].mean() * 100
    
    # Recent anomalies
    recent_anomalies = df[
        (df['zscore'].abs() > 2) & 
        (df['date'] >= df['date'].max() - pd.Timedelta(days=7))
    ].sort_values('date', ascending=False)
    
    # Replace non-finite values to keep JSON serialization safe
    category_stats = category_stats.replace([np.inf, -np.inf], np.nan).fillna(0)
    avg_nav_change = float(avg_nav_change) if np.isfinite(avg_nav_change) else 0
    avg_volatility = recent_df['volatility'].mean() * 100
    avg_volatility = float(avg_volatility) if np.isfinite(avg_volatility) else 0

    # Cap for demo realism
    avg_nav_change = float(np.clip(avg_nav_change, -5, 5))
    avg_volatility = float(np.clip(avg_volatility, 0, 50))

    _overview_cache = {
        'total_funds': total_funds,
        'funds_in_anomaly': funds_in_anomaly,
        'anomaly_rate': round(funds_in_anomaly / total_funds * 100, 1) if total_funds > 0 else 0,
        'avg_nav_change': round(avg_nav_change, 2),
        'avg_volatility': round(avg_volatility, 2),
        'category_stats': category_stats.to_dict('records'),
        'recent_anomaly_count': len(recent_anomalies),
        'last_updated': datetime.now().isoformat(),
    }
    return _overview_cache


def clear_cache():
    """Clear all cached data."""
    global _nav_cache, _scheme_cache, _processed_cache, _overview_cache
    _nav_cache = None
    _scheme_cache = None
    _processed_cache = None
    _overview_cache = None
