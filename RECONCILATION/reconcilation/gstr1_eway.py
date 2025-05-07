"""
Module to reconcile GSTR-1 data with E-way Bill data.
"""

import pandas as pd
import numpy as np
from config import GSTR1_EWAY_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def reconcile_gstr1_eway(gstr1_data, eway_data):
    """
    Reconciles GSTR-1 data with E-way Bill data to identify discrepancies.
    
    Args:
        gstr1_data (pd.DataFrame): DataFrame containing GSTR-1 data
        eway_data (pd.DataFrame): DataFrame containing E-way Bill data
        
    Returns:
        dict: Dictionary containing reconciliation results
    """
    # Rename columns based on mapping for comparison
    gstr1_renamed = gstr1_data.rename(columns={v: k for k, v in GSTR1_EWAY_MAPPING.items()})
    eway_renamed = eway_data.rename(columns={v: k for k, v in GSTR1_EWAY_MAPPING.items()})
    
    # Common columns for matching records
    key_columns = ["Invoice Number", "Invoice Date", "GSTIN/UIN of Recipient"]
    
    # Ensure date columns are in datetime format
    for df in [gstr1_renamed, eway_renamed]:
        if "Invoice Date" in df.columns:
            df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], errors='coerce')
    
    # Prepare results dictionary
    results = {
        "matched_invoices": [],
        "mismatched_invoices": [],
        "missing_in_gstr1": [],
        "missing_in_eway": [],
        "eway_without_gstr1": [],
        "summary": {
            "total_gstr1_invoices": len(gstr1_renamed),
            "total_eway_bills": len(eway_renamed),
            "matched_count": 0,
            "mismatched_count": 0,
            "missing_in_gstr1_count": 0,
            "missing_in_eway_count": 0,
            "eway_without_gstr1_count": 0
        }
    }

    # Identify missing invoices
    eway_keys = set(eway_renamed[key_columns].dropna().apply(tuple, axis=1))
    gstr1_keys = set(gstr1_renamed[key_columns].dropna().apply(tuple, axis=1))
    
    missing_in_gstr1_keys = eway_keys - gstr1_keys
    missing_in_eway_keys = gstr1_keys - eway_keys
    
    # Find invoices missing in GSTR-1
    for key in missing_in_gstr1_keys:
        mask = (eway_renamed["Invoice Number"] == key[0]) & \
               (eway_renamed["Invoice Date"] == key[1]) & \
               (eway_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        missing_invoices = eway_renamed[mask].copy()
        results["missing_in_gstr1"].extend(missing_invoices.to_dict("records"))
    
    results["summary"]["missing_in_gstr1_count"] = len(results["missing_in_gstr1"])
    
    # Find invoices missing in E-way Bill
    for key in missing_in_eway_keys:
        mask = (gstr1_renamed["Invoice Number"] == key[0]) & \
               (gstr1_renamed["Invoice Date"] == key[1]) & \
               (gstr1_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        missing_invoices = gstr1_renamed[mask].copy()
        results["missing_in_eway"].extend(missing_invoices.to_dict("records"))
    
    results["summary"]["missing_in_eway_count"] = len(results["missing_in_eway"])
    
    # Compare matching invoices for discrepancies
    common_keys = gstr1_keys.intersection(eway_keys)
    
    for key in common_keys:
        gstr1_mask = (gstr1_renamed["Invoice Number"] == key[0]) & \
                     (gstr1_renamed["Invoice Date"] == key[1]) & \
                     (gstr1_renamed["GSTIN/UIN of Recipient"] == key[2])
                     
        eway_mask = (eway_renamed["Invoice Number"] == key[0]) & \
                    (eway_renamed["Invoice Date"] == key[1]) & \
                    (eway_renamed["GSTIN/UIN of Recipient"] == key[2])
        
        gstr1_row = gstr1_renamed[gstr1_mask].iloc[0]
        eway_row = eway_renamed[eway_mask].iloc[0]
        
        # Check for discrepancies in amount fields
        has_discrepancy = False
        discrepancies = []
        
        value_columns = ["Invoice Value", "Taxable Value", "HSN Code"]
        
        for col in value_columns:
            if col in gstr1_row and col in eway_row:
                # Handle numeric comparisons
                if col in ["Invoice Value", "Taxable Value"]:
                    gstr1_val = pd.to_numeric(gstr1_row[col], errors='coerce') or 0
                    eway_val = pd.to_numeric(eway_row[col], errors='coerce') or 0
                    
                    if not np.isclose(gstr1_val, eway_val, rtol=PERCENTAGE_THRESHOLD, atol=AMOUNT_THRESHOLD):
                        has_discrepancy = True
                        diff = float(gstr1_val) - float(eway_val)
                        diff_percent = (diff / float(eway_val) * 100) if eway_val != 0 else np.inf
                        
                        discrepancies.append({
                            "field": col,
                            "gstr1_value": float(gstr1_val),
                            "eway_value": float(eway_val),
                            "difference": diff,
                            "difference_percent": diff_percent
                        })
                # String comparison for non-numeric fields
                else:
                    gstr1_val = str(gstr1_row[col]) if pd.notna(gstr1_row[col]) else ""
                    eway_val = str(eway_row[col]) if pd.notna(eway_row[col]) else ""
                    
                    if gstr1_val != eway_val:
                        has_discrepancy = True
                        discrepancies.append({
                            "field": col,
                            "gstr1_value": gstr1_val,
                            "eway_value": eway_val
                        })
        
        # Check E-way Bill Number
        if "E-Way Bill Number" in gstr1_row and "E-Way Bill Number" in eway_row:
            gstr1_eway_no = str(gstr1_row["E-Way Bill Number"]) if pd.notna(gstr1_row["E-Way Bill Number"]) else ""
            eway_bill_no = str(eway_row["E-Way Bill Number"]) if pd.notna(eway_row["E-Way Bill Number"]) else ""
            
            if gstr1_eway_no != eway_bill_no:
                has_discrepancy = True
                discrepancies.append({
                    "field": "E-Way Bill Number",
                    "gstr1_value": gstr1_eway_no,
                    "eway_value": eway_bill_no
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
    
    # Look for E-way bills without invoice reference (potential issue)
    if "E-Way Bill Number" in eway_renamed.columns:
        eway_without_invoice = eway_renamed[eway_renamed["Invoice Number"].isna() | 
                                         (eway_renamed["Invoice Number"] == "")]
        
        results["eway_without_gstr1"] = eway_without_invoice.to_dict("records")
        results["summary"]["eway_without_gstr1_count"] = len(results["eway_without_gstr1"])
    
    return results