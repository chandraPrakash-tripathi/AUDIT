"""
Module to reconcile ITC in Books vs Eligible ITC (Section 16 & 17).
"""

import pandas as pd
import numpy as np
from config import ITC_BOOKS_ELIGIBILITY_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_itc_eligibility(books_data, eligibility_data):
    """
    Reconciles ITC in Books with Eligible ITC as per Section 16 & 17 to identify discrepancies.
    
    Args:
        books_data (pd.DataFrame): DataFrame containing ITC data from books
        eligibility_data (pd.DataFrame): DataFrame containing eligible ITC data
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Ensure we're working with numeric data
    for df in [books_data, eligibility_data]:
        for col in df.columns:
            if col in ITC_BOOKS_ELIGIBILITY_MAPPING.keys() or col in ITC_BOOKS_ELIGIBILITY_MAPPING.values():
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Prepare results dictionary
    results = {
        "itc_comparison": [],
        "discrepancies": [],
        "summary": {
            "total_books_itc": 0,
            "total_eligible_itc": 0,
            "difference": 0,
            "difference_percent": 0,
            "total_discrepancies": 0
        }
    }
    
    # Map books columns to eligibility fields
    for books_col, eligibility_field in ITC_BOOKS_ELIGIBILITY_MAPPING.items():
        books_value = books_data[books_col].sum() if books_col in books_data.columns else 0
        eligibility_value = eligibility_data[eligibility_field].sum() if eligibility_field in eligibility_data.columns else 0
        
        diff = books_value - eligibility_value
        diff_percent = (diff / eligibility_value * 100) if eligibility_value != 0 else np.inf
        
        comparison = {
            "itc_type": books_col,
            "eligibility_field": eligibility_field,
            "books_value": float(books_value),
            "eligibility_value": float(eligibility_value),
            "difference": float(diff),
            "difference_percent": float(diff_percent)
        }
        
        results["itc_comparison"].append(comparison)
        
        # Record as discrepancy if beyond threshold
        if abs(diff) > AMOUNT_THRESHOLD and abs(diff_percent) > PERCENTAGE_THRESHOLD:
            results["discrepancies"].append({
                "type": "ITC Mismatch",
                "itc_type": books_col,
                "eligibility_field": eligibility_field,
                "books_value": float(books_value),
                "eligibility_value": float(eligibility_value),
                "difference": float(diff),
                "difference_percent": float(diff_percent)
            })
    
    # Calculate Net ITC comparison
    if "Net ITC" in books_data.columns and "Net Eligible ITC" in eligibility_data.columns:
        net_books_itc = books_data["Net ITC"].sum()
        net_eligible_itc = eligibility_data["Net Eligible ITC"].sum()
        
        net_diff = net_books_itc - net_eligible_itc
        net_diff_percent = (net_diff / net_eligible_itc * 100) if net_eligible_itc != 0 else np.inf
        
        results["summary"]["total_books_itc"] = float(net_books_itc)
        results["summary"]["total_eligible_itc"] = float(net_eligible_itc)
        results["summary"]["difference"] = float(net_diff)
        results["summary"]["difference_percent"] = float(net_diff_percent)
    
    # Calculate summary statistics
    results["summary"]["total_discrepancies"] = len(results["discrepancies"])
    
    # Check for specific ineligible ITCs as per Section 17
    section17_analysis = {}
    
    # Common ineligible ITC categories (these would be identified in eligibility_data)
    ineligible_categories = [
        "Motor Vehicle Expenses",
        "Food and Beverages",
        "Health Services",
        "Club Membership",
        "Rent-a-cab Services",
        "Works Contract Services",
        "Construction Expenses"
    ]
    
    # Extract data for ineligible categories if available
    for category in ineligible_categories:
        if category in eligibility_data.columns:
            section17_analysis[category] = float(eligibility_data[category].sum())
    
    if section17_analysis:
        results["section17_analysis"] = section17_analysis
    
    return results