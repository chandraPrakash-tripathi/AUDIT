"""
Module to reconcile GSTR-3B data with books (output tax).
"""

import pandas as pd
import numpy as np
from config import GSTR3B_BOOKS_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_gstr3b_books(gstr3b_data, books_data):
    """
    Reconciles GSTR-3B data with books (output tax) to identify discrepancies.
    
    Args:
        gstr3b_data (pd.DataFrame): DataFrame containing GSTR-3B data
        books_data (pd.DataFrame): DataFrame containing books output tax data
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Ensure we're working with numeric data
    for col in gstr3b_data.columns:
        if col in ["Integrated Tax Amount", "Central Tax Amount", "State/UT Tax Amount", "Cess Amount"]:
            gstr3b_data[col] = pd.to_numeric(gstr3b_data[col], errors='coerce').fillna(0)
    
    for col in books_data.columns:
        if col in ["IGST Output", "CGST Output", "SGST/UTGST Output", "Cess Output"]:
            books_data[col] = pd.to_numeric(books_data[col], errors='coerce').fillna(0)
    
    # Prepare results dictionary
    results = {
        "summary_comparison": [],
        "discrepancies": [],
        "tax_category_comparison": [],
        "summary": {
            "total_discrepancies": 0,
            "max_discrepancy_percentage": 0,
            "total_discrepancy_amount": 0
        }
    }
    
    # Map GSTR-3B columns to Books columns for tax amounts
    tax_mapping = {
        "Integrated Tax Amount": "IGST Output",
        "Central Tax Amount": "CGST Output",
        "State/UT Tax Amount": "SGST/UTGST Output",
        "Cess Amount": "Cess Output"
    }
    
    # Compare total tax amounts for each tax type
    for gstr3b_col, books_col in tax_mapping.items():
        gstr3b_total = gstr3b_data[gstr3b_col].sum() if gstr3b_col in gstr3b_data.columns else 0
        books_total = books_data[books_col].sum() if books_col in books_data.columns else 0
        
        diff = gstr3b_total - books_total
        diff_percent = (diff / books_total * 100) if books_total != 0 else np.inf
        
        comparison = {
            "tax_type": gstr3b_col.replace(" Amount", ""),
            "gstr3b_value": float(gstr3b_total),
            "books_value": float(books_total),
            "difference": float(diff),
            "difference_percent": float(diff_percent)
        }
        
        results["summary_comparison"].append(comparison)
        
        # Record as discrepancy if beyond threshold
        if abs(diff) > AMOUNT_THRESHOLD and abs(diff_percent) > PERCENTAGE_THRESHOLD:
            results["discrepancies"].append({
                "type": "Tax Amount Mismatch",
                "tax_type": gstr3b_col.replace(" Amount", ""),
                "gstr3b_value": float(gstr3b_total),
                "books_value": float(books_total),
                "difference": float(diff),
                "difference_percent": float(diff_percent)
            })
    
    # Compare tax categories (Table 3.1 sections)
    category_mapping = {
        "Table 3.1(a)": "Regular Supplies Output Tax",
        "Table 3.1(b)": "Zero-Rated Supplies",
        "Table 3.1(c)": "Exempt Supplies",
        "Table 3.1(d)": "RCM Output Tax",
        "Table 3.1(e)": "Non-GST Supplies"
    }
    
    # Extract category data if available
    category_data = []
    
    for gstr3b_category, books_category in category_mapping.items():
        gstr3b_value = 0
        books_value = 0
        
        # Extract category values - this will depend on how data is structured
        # Simplified example assuming values are in columns with category names
        if gstr3b_category in gstr3b_data.columns:
            gstr3b_value = gstr3b_data[gstr3b_category].sum()
        
        if books_category in books_data.columns:
            books_value = books_data[books_category].sum()
        
        diff = gstr3b_value - books_value
        diff_percent = (diff / books_value * 100) if books_value != 0 else np.inf
        
        comparison = {
            "category": gstr3b_category,
            "books_category": books_category,
            "gstr3b_value": float(gstr3b_value),
            "books_value": float(books_value),
            "difference": float(diff),
            "difference_percent": float(diff_percent)
        }
        
        category_data.append(comparison)
        
        # Record as discrepancy if beyond threshold
        if abs(diff) > AMOUNT_THRESHOLD and abs(diff_percent) > PERCENTAGE_THRESHOLD:
            results["discrepancies"].append({
                "type": "Category Mismatch",
                "category": gstr3b_category,
                "books_category": books_category,
                "gstr3b_value": float(gstr3b_value),
                "books_value": float(books_value),
                "difference": float(diff),
                "difference_percent": float(diff_percent)
            })
    
    results["tax_category_comparison"] = category_data
    
    # Calculate summary statistics
    results["summary"]["total_discrepancies"] = len(results["discrepancies"])
    
    if results["discrepancies"]:
        results["summary"]["max_discrepancy_percentage"] = max(
            abs(d["difference_percent"]) for d in results["discrepancies"]
        )
        results["summary"]["total_discrepancy_amount"] = sum(
            abs(d["difference"]) for d in results["discrepancies"]
        )
    
    return results