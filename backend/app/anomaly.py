"""
Anomaly detection module for mutual fund NAV data.
Uses simple statistical methods (z-score) to detect anomalies.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# Anomaly thresholds
ZSCORE_THRESHOLD = 2.0
HIGH_SEVERITY_THRESHOLD = 3.0


def detect_anomalies(
    df: pd.DataFrame,
    zscore_threshold: float = ZSCORE_THRESHOLD
) -> pd.DataFrame:
    """
    Detect anomalies in NAV data based on z-score.
    
    Args:
        df: DataFrame with 'zscore' column
        zscore_threshold: Threshold for anomaly detection
        
    Returns:
        DataFrame with anomaly flags and metadata
    """
    df = df.copy()
    
    # Mark anomalies
    df['is_anomaly'] = df['zscore'].abs() > zscore_threshold
    
    # Severity classification
    df['severity'] = 'normal'
    df.loc[df['zscore'].abs() > zscore_threshold, 'severity'] = 'medium'
    df.loc[df['zscore'].abs() > HIGH_SEVERITY_THRESHOLD, 'severity'] = 'high'
    
    # Direction
    df['anomaly_direction'] = 'none'
    df.loc[(df['is_anomaly']) & (df['zscore'] > 0), 'anomaly_direction'] = 'up'
    df.loc[(df['is_anomaly']) & (df['zscore'] < 0), 'anomaly_direction'] = 'down'
    
    # Generate explanations
    df['explanation'] = df.apply(generate_explanation, axis=1)
    
    return df


def generate_explanation(row: pd.Series) -> str:
    """Generate human-readable explanation for an anomaly."""
    if not row.get('is_anomaly', False):
        return "Normal market behavior"
    
    zscore = row.get('zscore', 0)
    daily_return = row.get('daily_return', 0) * 100
    severity = row.get('severity', 'medium')
    
    direction = "increase" if zscore > 0 else "decrease"
    severity_text = "Significant" if severity == 'high' else "Moderate"
    
    explanations = [
        f"{severity_text} NAV {direction} detected",
        f"Unusual deviation from rolling mean (z-score: {abs(zscore):.1f})",
    ]
    
    if abs(daily_return) > 3:
        explanations.append(f"Daily return of {daily_return:.2f}% exceeds normal range")
    
    if severity == 'high':
        explanations.append("Recommend immediate review")
    
    return ". ".join(explanations)


def get_anomaly_summary(df: pd.DataFrame) -> Dict:
    """Get summary statistics for anomalies."""
    anomalies = df[df['is_anomaly'] == True]
    
    if anomalies.empty:
        return {
            'total_anomalies': 0,
            'high_severity': 0,
            'medium_severity': 0,
            'up_movements': 0,
            'down_movements': 0,
            'affected_funds': 0,
            'anomaly_rate': 0,
        }
    
    return {
        'total_anomalies': len(anomalies),
        'high_severity': len(anomalies[anomalies['severity'] == 'high']),
        'medium_severity': len(anomalies[anomalies['severity'] == 'medium']),
        'up_movements': len(anomalies[anomalies['anomaly_direction'] == 'up']),
        'down_movements': len(anomalies[anomalies['anomaly_direction'] == 'down']),
        'affected_funds': anomalies['scheme_code'].nunique(),
        'anomaly_rate': round(len(anomalies) / len(df) * 100, 2),
    }


def get_recent_anomalies(
    df: pd.DataFrame,
    days: int = 7,
    limit: int = 50
) -> List[Dict]:
    """Get list of recent anomalies."""
    df = df.copy()
    
    # Ensure anomaly detection has been run
    if 'is_anomaly' not in df.columns:
        df = detect_anomalies(df)
    
    # Filter recent anomalies
    max_date = df['date'].max()
    cutoff_date = max_date - pd.Timedelta(days=days)
    
    recent = df[
        (df['is_anomaly'] == True) & 
        (df['date'] >= cutoff_date)
    ].sort_values('date', ascending=False)
    
    anomalies = []
    for _, row in recent.head(limit).iterrows():
        scheme_code = str(row.get('scheme_code', ''))
        fund_name = row.get('scheme_name', '')
        if not isinstance(fund_name, str) or not fund_name.strip():
            fund_name = scheme_code or 'Unknown'
        category = row.get('category', '')
        if not isinstance(category, str) or not category.strip():
            category = 'Unknown'

        anomalies.append({
            'id': f"{row['scheme_code']}_{row['date'].strftime('%Y%m%d')}",
            'scheme_code': scheme_code,
            'fund_name': fund_name,
            'category': category,
            'date': row['date'].strftime('%Y-%m-%d'),
            'timestamp': row['date'].isoformat(),
            'nav': round(row['nav'], 4),
            'daily_return': round(row.get('daily_return', 0) * 100, 2),
            'zscore': round(row['zscore'], 2),
            'severity': row['severity'],
            'direction': row['anomaly_direction'],
            'explanation': row['explanation'],
        })
    
    return anomalies


def calculate_confidence_score(zscore: float) -> float:
    """Calculate anomaly confidence score (0-1)."""
    # Higher absolute z-score = higher confidence
    abs_zscore = abs(zscore)
    
    if abs_zscore < ZSCORE_THRESHOLD:
        return 0.0
    
    # Scale from threshold to max expected value
    confidence = min((abs_zscore - ZSCORE_THRESHOLD) / 3.0, 1.0)
    return round(confidence, 2)


def get_anomaly_signals(df: pd.DataFrame, limit: int = 20) -> List[Dict]:
    """
    Generate trading-style signals from anomalies.
    Returns formatted signals for the signal feed.
    """
    df = df.copy()
    
    if 'is_anomaly' not in df.columns:
        df = detect_anomalies(df)
    
    # Get recent anomalies
    max_date = df['date'].max()
    recent = df[
        (df['is_anomaly'] == True) & 
        (df['date'] >= max_date - pd.Timedelta(days=3))
    ].sort_values('date', ascending=False)
    
    signals = []
    for _, row in recent.head(limit).iterrows():
        scheme_code = str(row.get('scheme_code', ''))
        fund_name = row.get('scheme_name', '')
        if not isinstance(fund_name, str) or not fund_name.strip():
            fund_name = scheme_code or 'Unknown'
        category = row.get('category', '')
        if not isinstance(category, str) or not category.strip():
            category = 'Unknown'
        signal_type = _determine_signal_type(row)
        
        signals.append({
            'id': f"sig_{row['scheme_code']}_{row['date'].strftime('%Y%m%d%H%M')}",
            'timestamp': row['date'].isoformat(),
            'type': signal_type['type'],
            'icon': signal_type['icon'],
            'color': signal_type['color'],
            'title': signal_type['title'],
            'fund_name': fund_name,
            'scheme_code': scheme_code,
            'category': category,
            'message': row['explanation'],
            'severity': row['severity'],
            'confidence': calculate_confidence_score(row['zscore']),
            'metrics': {
                'nav': round(row['nav'], 4),
                'change': round(row.get('daily_return', 0) * 100, 2),
                'zscore': round(row['zscore'], 2),
            }
        })
    
    return signals


def _determine_signal_type(row: pd.Series) -> Dict:
    """Determine signal type and styling based on anomaly characteristics."""
    severity = row.get('severity', 'medium')
    direction = row.get('anomaly_direction', 'down')
    category = row.get('category', 'Unknown')
    
    if severity == 'high' and direction == 'down':
        return {
            'type': 'critical',
            'icon': '⚠️',
            'color': 'red',
            'title': f'{category} fund major drop detected'
        }
    elif severity == 'high' and direction == 'up':
        return {
            'type': 'alert',
            'icon': '📈',
            'color': 'yellow',
            'title': f'{category} fund unusual spike'
        }
    elif direction == 'down':
        return {
            'type': 'warning',
            'icon': '📉',
            'color': 'orange',
            'title': f'{category} fund volatility alert'
        }
    else:
        return {
            'type': 'info',
            'icon': '📊',
            'color': 'blue',
            'title': f'{category} fund movement detected'
        }


def analyze_fund_risk(df: pd.DataFrame, scheme_code: str) -> Dict:
    """Analyze risk metrics for a specific fund."""
    fund_df = df[df['scheme_code'] == scheme_code].copy()
    
    if fund_df.empty:
        return None
    
    fund_df = fund_df.sort_values('date')
    
    # Calculate risk metrics
    returns = fund_df['daily_return'].dropna()
    
    risk_metrics = {
        'volatility': round(returns.std() * np.sqrt(252) * 100, 2),
        'max_drawdown': round(fund_df['drawdown'].min() * 100, 2),
        'sharpe_estimate': round(returns.mean() / returns.std() * np.sqrt(252), 2) if returns.std() > 0 else 0,
        'anomaly_frequency': round(fund_df['is_anomaly'].mean() * 100, 2) if 'is_anomaly' in fund_df.columns else 0,
        'avg_anomaly_magnitude': round(fund_df[fund_df.get('is_anomaly', False) == True]['zscore'].abs().mean(), 2) if 'is_anomaly' in fund_df.columns else 0,
        'risk_score': _calculate_risk_score(fund_df),
    }
    
    return risk_metrics


def _calculate_risk_score(df: pd.DataFrame) -> str:
    """Calculate overall risk score for a fund."""
    volatility = df['volatility'].iloc[-1] if 'volatility' in df.columns else 0
    anomaly_rate = df.get('is_anomaly', pd.Series([False])).mean()
    
    score = 0
    if volatility > 0.3:
        score += 3
    elif volatility > 0.2:
        score += 2
    elif volatility > 0.1:
        score += 1
    
    if anomaly_rate > 0.1:
        score += 3
    elif anomaly_rate > 0.05:
        score += 2
    elif anomaly_rate > 0.02:
        score += 1
    
    if score >= 5:
        return 'High'
    elif score >= 3:
        return 'Medium'
    else:
        return 'Low'
