"""
Module to reconcile GSTR-1 data with E-invoice data.
"""

import pandas as pd
import numpy as np
from config import GSTR1_EINVOICE_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_gstr1_einvoice(gstr1_data, einvoice_data):
    """
    Reconciles GSTR-1 data with E-invoice data to identify discrepancies.
    
    Args:
        gstr1_data (pd.DataFrame): DataFrame containing GSTR-1 data
        einvoice_data (pd.DataFrame): DataFrame containing E-invoice data
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Rename columns based on mapping for comparison
    gstr1_renamed = gstr1_data.rename(columns={v: k for k, v in GSTR1_EINVOICE_MAPPING.items()})
    einvoice_renamed = einvoice_data.rename(columns={v: k for k, v in GSTR1_EINVOICE_MAPPING.items()})
    
    # Common columns for matching records
    key_columns = ["Invoice Number", "Invoice Date", "GSTIN/UIN of Recipient"]
    
    # Ensure date columns are in datetime format
    for df in [gstr1_renamed, einvoice_renamed]:
        if "Invoice Date" in df.columns:
            df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
    
    # Prepare results dictionary
    results = {
        "matched_invoices": [],
        "mismatched_invoices": [],
        "missing_in_gstr1": [],
        "missing_in_einvoice": [],
        "summary": {
            "total_gstr1_invoices": len(gstr1_renamed),
            "total_einvoice_invoices": len(einvoice_renamed),
            "matched_count": 0,
            "mismatched_count": 0,
            "missing_in_gstr1_count": 0,
            "missing_in_einvoice_count": 0,
        }
    }

    # Identify missing invoices in GSTR-1
    einvoice_keys = set(einvoice_renamed[key_columns].dropna().apply(tuple, axis=1))
    gstr1_keys = set(gstr1_renamed[key_columns].dropna().apply(tuple, axis=1))
    
    missing_in_gstr1_keys = einvoice_keys - gstr1_keys
    missing_in_einvoice_keys = gstr1_keys - einvoice_keys
    
    # Find invoices missing in GSTR-1
    for key in missing_in_gstr1_keys:
        mask = (einvoice_renamed["Invoice Number"] == key[0]) & \
               (einvoice_renamed["Invoice Date"] == key[1]) & \
               (einvoice_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        missing_invoices = einvoice_renamed[mask].copy()
        results["missing_in_gstr1"].extend(missing_invoices.to_dict("records"))
    
    results["summary"]["missing_in_gstr1_count"] = len(results["missing_in_gstr1"])
    
    # Find invoices missing in E-invoice
    for key in missing_in_einvoice_keys:
        mask = (gstr1_renamed["Invoice Number"] == key[0]) & \
               (gstr1_renamed["Invoice Date"] == key[1]) & \
               (gstr1_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        missing_invoices = gstr1_renamed[mask].copy()
        results["missing_in_einvoice"].extend(missing_invoices.to_dict("records"))
    
    results["summary"]["missing_in_einvoice_count"] = len(results["missing_in_einvoice"])
    
    # Compare matching invoices for discrepancies
    common_keys = gstr1_keys.intersection(einvoice_keys)
    
    for key in common_keys:
        gstr1_mask = (gstr1_renamed["Invoice Number"] == key[0]) & \
                     (gstr1_renamed["Invoice Date"] == key[1]) & \
                     (gstr1_renamed["GSTIN/UIN of Recipient"] == key[2])
                     
        einvoice_mask = (einvoice_renamed["Invoice Number"] == key[0]) & \
                         (einvoice_renamed["Invoice Date"] == key[1]) & \
                         (einvoice_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        gstr1_row = gstr1_renamed[gstr1_mask].iloc[0]
        einvoice_row = einvoice_renamed[einvoice_mask].iloc[0]
        
        # Check for discrepancies in amount fields
        has_discrepancy = False
        discrepancies = []
        
        value_columns = [
            "Invoice Value", "Taxable Value", "Integrated Tax", 
            "Central Tax", "State/UT Tax", "Cess"
        ]
        
        for col in value_columns:
            if col in gstr1_row and col in einvoice_row:
                gstr1_val = pd.to_numeric(gstr1_row[col], errors='coerce') or 0
                einvoice_val = pd.to_numeric(einvoice_row[col], errors='coerce') or 0
                
                if not np.isclose(gstr1_val, einvoice_val, rtol=PERCENTAGE_THRESHOLD, atol=AMOUNT_THRESHOLD):
                    has_discrepancy = True
                    diff = float(gstr1_val) - float(einvoice_val)
                    diff_percent = (diff / float(einvoice_val) * 100) if einvoice_val != 0 else np.inf
                    
                    discrepancies.append({
                        "field": col,
                        "gstr1_value": float(gstr1_val),
                        "einvoice_value": float(einvoice_val),
                        "difference": diff,
                        "difference_percent": diff_percent
                    })
        
        # Add to appropriate result list
        combined_row = {**gstr1_row.to_dict(), **{"discrepancies": discrepancies}} if has_discrepancy else gstr1_row.to_dict()
        
        if has_discrepancy:
            results["mismatched_invoices"].append(combined_row)
        else:
            results["matched_invoices"].append(combined_row)
    
    # Update summary
    results["summary"]["matched_count"] = len(results["matched_invoices"])
    results["summary"]["mismatched_count"] = len(results["mismatched_invoices"])
    
    return results