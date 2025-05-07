"""
Module to reconcile turnover as per Books vs GST Returns vs Financial Statements.
"""

import pandas as pd
import numpy as np
from config import TURNOVER_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_turnover(books_data, gst_returns_data, financial_statements_data):
    """
    Reconciles turnover data from Books, GST Returns, and Financial Statements.
    
    Args:
        books_data (pd.DataFrame): DataFrame containing turnover data from books
        gst_returns_data (pd.DataFrame): DataFrame containing turnover data from GST returns
        financial_statements_data (pd.DataFrame): DataFrame containing turnover data from financial statements
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Ensure we're working with numeric data
    for df in [books_data, gst_returns_data, financial_statements_data]:
        for col in df.columns:
            if col in [item for sublist in TURNOVER_MAPPING.values() for item in sublist] or col in TURNOVER_MAPPING.keys():
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Prepare results dictionary
    results = {
        "turnover_comparison": [],
        "discrepancies": [],
        "summary": {
            "total_books_turnover": 0,
            "total_gst_turnover": 0,
            "total_fs_turnover": 0,
            "total_discrepancies": 0,
            "max_discrepancy": 0
        }
    }
    
    # Compare each turnover component
    for books_field, (gst_field, fs_field) in TURNOVER_MAPPING.items():
        books_value = books_data[books_field].sum() if books_field in books_data.columns else 0
        gst_value = gst_returns_data[gst_field].sum() if gst_field and gst_field in gst_returns_data.columns else 0
        fs_value = financial_statements_data[fs_field].sum() if fs_field and fs_field in financial_statements_data.columns else 0
        
        # Calculate differences
        books_gst_diff = books_value - gst_value
        books_fs_diff = books_value - fs_value
        gst_fs_diff = gst_value - fs_value
        
        # Calculate percentages
        books_gst_percent = (books_gst_diff / gst_value * 100) if gst_value != 0 else np.inf
        books_fs_percent = (books_fs_diff / fs_value * 100) if fs_value != 0 else np.inf
        gst_fs_percent = (gst_fs_diff / fs_value * 100) if fs_value != 0 else np.inf
        
        comparison = {
            "turnover_type": books_field,
            "books_value": float(books_value),
            "gst_field": gst_field,
            "gst_value": float(gst_value),
            "fs_field": fs_field,
            "fs_value": float(fs_value),
            "books_gst_diff": float(books_gst_diff),
            "books_fs_diff": float(books_fs_diff),
            "gst_fs_diff": float(gst_fs_diff),
            "books_gst_percent": float(books_gst_percent),
            "books_fs_percent": float(books_fs_percent),
            "gst_fs_percent": float(gst_fs_percent)
        }
        
        results["turnover_comparison"].append(comparison)
        
        # Record as discrepancy if beyond threshold
        discrepancy = {
            "turnover_type": books_field,
            "discrepancies": []
        }
        
        if abs(books_gst_diff) > AMOUNT_THRESHOLD and abs(books_gst_percent) > PERCENTAGE_THRESHOLD and gst_field:
            discrepancy["discrepancies"].append({
                "type": "Books vs GST Returns",
                "books_value": float(books_value),
                "gst_value": float(gst_value),
                "difference": float(books_gst_diff),
                "difference_percent": float(books_gst_percent)
            })
        
        if abs(books_fs_diff) > AMOUNT_THRESHOLD and abs(books_fs_percent) > PERCENTAGE_THRESHOLD and fs_field:
            discrepancy["discrepancies"].append({
                "type": "Books vs Financial Statements",
                "books_value": float(books_value),
                "fs_value": float(fs_value),
                "difference": float(books_fs_diff),
                "difference_percent": float(books_fs_percent)
            })
        
        if abs(gst_fs_diff) > AMOUNT_THRESHOLD and abs(gst_fs_percent) > PERCENTAGE_THRESHOLD and gst_field and fs_field:
            discrepancy["discrepancies"].append({
                "type": "GST Returns vs Financial Statements",
                "gst_value": float(gst_value),
                "fs_value": float(fs_value),
                "difference": float(gst_fs_diff),
                "difference_percent": float(gst_fs_percent)
            })
        
        if discrepancy["discrepancies"]:
            results["discrepancies"].append(discrepancy)
    
    # Calculate total turnover for each source
    if "Total Sales" in books_data.columns:
        results["summary"]["total_books_turnover"] = float(books_data["Total Sales"].sum())
    
    if "Annual Aggregate Turnover" in gst_returns_data.columns:
        results["summary"]["total_gst_turnover"] = float(gst_returns_data["Annual Aggregate Turnover"].sum())
    
    if "Revenue from Operations" in financial_statements_data.columns:
        results["summary"]["total_fs_turnover"] = float(financial_statements_data["Revenue from Operations"].sum())
    
    # Calculate summary statistics
    results["summary"]["total_discrepancies"] = sum(len(d["discrepancies"]) for d in results["discrepancies"])
    
    # Find maximum discrepancy
    all_discrepancies = []
    for discrepancy_group in results["discrepancies"]:
        for discrepancy in discrepancy_group["discrepancies"]:
            all_discrepancies.append(abs(discrepancy["difference"]))
    
    if all_discrepancies:
        results["summary"]["max_discrepancy"] = float(max(all_discrepancies))
    
    return results