"""
Module to reconcile ITC in GSTR-3B vs GSTR-2B.
"""

import pandas as pd
import numpy as np
from config import ITC_GSTR3B_GSTR2B_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_itc_gstr3b_gstr2b(gstr3b_data, gstr2b_data):
    """
    Reconciles ITC data from GSTR-3B with GSTR-2B to identify discrepancies.
    
    Args:
        gstr3b_data (pd.DataFrame): DataFrame containing GSTR-3B ITC data
        gstr2b_data (pd.DataFrame): DataFrame containing GSTR-2B data
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Ensure we're working with numeric data
    for df in [gstr3b_data, gstr2b_data]:
        for col in df.columns:
            if "Amount" in col or "Tax" in col or "ITC" in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Prepare results dictionary
    results = {
        "itc_comparison": [],
        "discrepancies": [],
        "summary": {
            "total_gstr3b_itc": 0,
            "total_gstr2b_itc": 0,
            "difference": 0,
            "difference_percent": 0,
            "total_discrepancies": 0
        }
    }
    
    # Compare ITC elements between GSTR-3B and GSTR-2B
    for gstr3b_field, gstr2b_field in ITC_GSTR3B_GSTR2B_MAPPING.items():
        # Skip if mapping is empty (not directly in GSTR-2B)
        if not gstr2b_field:
            continue
        
        gstr3b_value = gstr3b_data[gstr3b_field].sum() if gstr3b_field in gstr3b_data.columns else 0
        gstr2b_value = gstr2b_data[gstr2b_field].sum() if gstr2b_field in gstr2b_data.columns else 0
        
        diff = gstr3b_value - gstr2b_value
        diff_percent = (diff / gstr2b_value * 100) if gstr2b_value != 0 else np.inf
        
        comparison = {
            "itc_type": gstr3b_field,
            "gstr3b_value": float(gstr3b_value),
            "gstr2b_field": gstr2b_field,
            "gstr2b_value": float(gstr2b_value),
            "difference": float(diff),
            "difference_percent": float(diff_percent)
        }
        
        results["itc_comparison"].append(comparison)
        
        # Record as discrepancy if beyond threshold
        if abs(diff) > AMOUNT_THRESHOLD and abs(diff_percent) > PERCENTAGE_THRESHOLD:
            results["discrepancies"].append({
                "type": "ITC Mismatch",
                "itc_type": gstr3b_field,
                "gstr3b_value": float(gstr3b_value),
                "gstr2b_field": gstr2b_field,
                "gstr2b_value": float(gstr2b_value),
                "difference": float(diff),
                "difference_percent": float(diff_percent)
            })
    
    # Calculate Net ITC comparison
    if "Table 4(C)" in gstr3b_data.columns and "Net ITC Available" in gstr2b_data.columns:
        net_gstr3b_itc = gstr3b_data["Table 4(C)"].sum()
        net_gstr2b_itc = gstr2b_data["Net ITC Available"].sum()
        
        net_diff = net_gstr3b_itc - net_gstr2b_itc
        net_diff_percent = (net_diff / net_gstr2b_itc * 100) if net_gstr2b_itc != 0 else np.inf
        
        results["summary"]["total_gstr3b_itc"] = float(net_gstr3b_itc)
        results["summary"]["total_gstr2b_itc"] = float(net_gstr2b_itc)
        results["summary"]["difference"] = float(net_diff)
        results["summary"]["difference_percent"] = float(net_diff_percent)
        
        # Add as discrepancy if beyond threshold
        if abs(net_diff) > AMOUNT_THRESHOLD and abs(net_diff_percent) > PERCENTAGE_THRESHOLD:
            results["discrepancies"].append({
                "type": "Net ITC Mismatch",
                "itc_type": "Net ITC",
                "gstr3b_value": float(net_gstr3b_itc),
                "gstr2b_value": float(net_gstr2b_itc),
                "difference": float(net_diff),
                "difference_percent": float(net_diff_percent)
            })
    
    # Calculate summary statistics
    results["summary"]["total_discrepancies"] = len(results["discrepancies"])
    
    # Check for additional ITC taken in GSTR-3B not in GSTR-2B
    additional_itc = {}
    
    # Fields in GSTR-3B that don't have direct mapping in GSTR-2B
    unmapped_fields = [field for field, mapped in ITC_GSTR3B_GSTR2B_MAPPING.items() if not mapped]
    
    for field in unmapped_fields:
        if field in gstr3b_data.columns:
            value = gstr3b_data[field].sum()
            if value > 0:
                additional_itc[field] = float(value)
    
    if additional_itc:
        results["additional_itc_in_gstr3b"] = additional_itc
    
    return results