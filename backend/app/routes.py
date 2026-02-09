"""
FastAPI routes for the mutual fund anomaly dashboard.
"""

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel

from .data_loader import get_fund_list, get_fund_details, get_overview, get_processed_data, _clear_cache, DATA_DIR
from .anomaly import detect_anomalies, get_anomaly_signals, get_recent_anomalies, analyze_fund_risk

router = APIRouter()


# Response models
class FundSummary(BaseModel):
    scheme_code: str
    fund_name: str
    category: str
    fund_type: str
    latest_nav: float
    daily_return: float
    volatility: float
    anomaly_flag: bool
    zscore: float
    drawdown: float


class OverviewStats(BaseModel):
    total_funds: int
    funds_in_anomaly: int
    anomaly_rate: float
    avg_nav_change: float
    avg_volatility: float
    category_stats: List[dict]
    recent_anomaly_count: int
    last_updated: str


class AnomalySignal(BaseModel):
    id: str
    timestamp: str
    type: str
    icon: str
    color: str
    title: str
    fund_name: str
    scheme_code: str
    category: str
    message: str
    severity: str
    confidence: float
    metrics: dict


@router.get("/funds", response_model=List[FundSummary])
async def get_funds(
    category: Optional[str] = Query(None, description="Filter by category"),
    anomaly_only: bool = Query(False, description="Show only funds with anomalies"),
    sort_by: Optional[str] = Query(None, description="Sort field"),
    limit: int = Query(50, description="Maximum number of funds to return")
):
    """Get list of all funds with latest metrics."""
    funds = get_fund_list()
    
    # Apply filters
    if category:
        funds = [f for f in funds if f['category'].lower() == category.lower()]
    
    if anomaly_only:
        funds = [f for f in funds if f['anomaly_flag']]
    
    # Apply sorting
    if sort_by:
        reverse = sort_by.startswith('-')
        sort_key = sort_by.lstrip('-')
        if sort_key in funds[0] if funds else []:
            funds = sorted(funds, key=lambda x: x.get(sort_key, 0), reverse=reverse)
    
    return funds[:limit]


@router.get("/fund/{scheme_code}")
async def get_fund(scheme_code: str):
    """Get detailed data for a specific fund."""
    details = get_fund_details(scheme_code)
    
    if not details:
        raise HTTPException(status_code=404, detail=f"Fund {scheme_code} not found")
    
    # Add risk analysis (compute on the single fund for speed)
    df = get_processed_data()
    fund_df = df[df['scheme_code'] == scheme_code]
    fund_df = detect_anomalies(fund_df)
    risk_metrics = analyze_fund_risk(fund_df, scheme_code)
    
    if risk_metrics:
        details['risk_metrics'] = risk_metrics
    
    return details


@router.get("/overview", response_model=OverviewStats)
async def get_dashboard_overview():
    """Get overall dashboard statistics."""
    return get_overview()


@router.get("/signals", response_model=List[AnomalySignal])
async def get_signals(
    limit: int = Query(20, description="Maximum number of signals"),
    severity: Optional[str] = Query(None, description="Filter by severity (high, medium)")
):
    """Get anomaly signals for the signal feed."""
    df = get_processed_data()
    df = detect_anomalies(df)
    signals = get_anomaly_signals(df, limit=limit * 2)
    
    if severity:
        signals = [s for s in signals if s['severity'] == severity]
    
    return signals[:limit]


@router.get("/anomalies")
async def get_anomalies(
    days: int = Query(7, description="Look back period in days"),
    limit: int = Query(50, description="Maximum number of anomalies")
):
    """Get list of recent anomalies."""
    df = get_processed_data()
    df = detect_anomalies(df)
    
    return get_recent_anomalies(df, days=days, limit=limit)


@router.get("/heatmap")
async def get_heatmap_data():
    """Get data for the fund heatmap visualization."""
    funds = get_fund_list()
    
    # Group by category for heatmap
    heatmap_data = []
    for fund in funds:
        heatmap_data.append({
            'scheme_code': fund['scheme_code'],
            'name': fund['fund_name'],
            'category': fund['category'],
            'value': fund['daily_return'],
            'nav': fund['latest_nav'],
            'anomaly': fund['anomaly_flag'],
            'zscore': fund['zscore'],
            'color': _get_heatmap_color(fund['daily_return'], fund['anomaly_flag']),
        })
    
    return {
        'data': heatmap_data,
        'categories': list(set(f['category'] for f in funds)),
    }


@router.get("/categories")
async def get_categories():
    """Get list of fund categories with stats."""
    overview = get_overview()
    return overview['category_stats']


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "fund-anomaly-api",
        "version": "1.0.0"
    }


def _get_heatmap_color(daily_return: float, is_anomaly: bool) -> str:
    """Determine heatmap cell color based on return and anomaly status."""
    if is_anomaly:
        return 'anomaly'
    elif daily_return > 2:
        return 'strong-positive'
    elif daily_return > 0.5:
        return 'positive'
    elif daily_return > -0.5:
        return 'neutral'
    elif daily_return > -2:
        return 'negative'
    else:
        return 'strong-negative'


@router.post("/upload")
async def upload_nav_file(file: UploadFile = File(...)):
    """
    Upload a NAV file (CSV or Parquet) and return a preview.
    The file is saved for use by the dashboard.
    """
    import pandas as pd
    import io
    
    if not file.filename.endswith(('.csv', '.parquet')):
        raise HTTPException(status_code=400, detail="Only CSV and Parquet files are supported")
    
    try:
        contents = await file.read()
        
        # Parse the file
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents))
        else:
            df = pd.read_parquet(io.BytesIO(contents))
        
        # Reset index if scheme_code is stored as index
        if df.index.name and 'scheme' in df.index.name.lower():
            df = df.reset_index()
        
        # Normalize column names
        df.columns = [str(c).lower().strip().replace(' ', '_') for c in df.columns]
        
        # Find scheme code column
        scheme_col = None
        for col in df.columns:
            if 'scheme' in col or 'code' in col or 'fund' in col:
                scheme_col = col
                break
        
        unique_funds = df[scheme_col].nunique() if scheme_col else 0
        
        # Prepare preview (first 15 rows)
        preview_df = df.head(15)
        preview_records = preview_df.to_dict(orient='records')
        
        # Save uploaded file to data directory for dashboard use
        dest_path = DATA_DIR / "mutual_fund_nav_history.parquet"
        
        # Convert to parquet and save
        df.to_parquet(dest_path, index=False)
        
        # Clear data cache so dashboard loads new file
        _clear_cache()
        
        return {
            "success": True,
            "filename": file.filename,
            "total_rows": len(df),
            "unique_funds": unique_funds,
            "columns": list(df.columns),
            "preview": preview_records
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process file: {str(e)}")
