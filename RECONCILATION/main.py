import pandas as pd
import json
import streamlit as st
import re
import numpy as np
from datetime import datetime

# --- Streamlit UI ---
st.set_page_config(page_title="GSTR-2B vs Purchase Register Reconciliation", layout="wide")
st.title("📊 GSTR-2B vs Purchase Register Reconciliation Tool")

# --- File Upload ---
gstr2b_file = st.file_uploader("Upload GSTR-2B JSON file", type="json")
purchase_file = st.file_uploader("Upload Purchase Register (CSV) file", type="csv")

if gstr2b_file and purchase_file:
    # --- Load GSTR-2B JSON ---
    gstr2b_data = json.load(gstr2b_file)
    gstr2b_records = []
    
    # Display JSON structure for debugging
    st.subheader("GSTR-2B Structure")
    sample_json = {}
    if "data" in gstr2b_data and "docdata" in gstr2b_data["data"]:
        if "b2b" in gstr2b_data["data"]["docdata"] and len(gstr2b_data["data"]["docdata"]["b2b"]) > 0:
            sample_party = gstr2b_data["data"]["docdata"]["b2b"][0]
            if "inv" in sample_party and len(sample_party["inv"]) > 0:
                sample_json = {
                    "structure": "party -> inv -> details",
                    "sample_invoice": sample_party["inv"][0]
                }
    st.json(sample_json)
    
    # Check if b2b data exists
    if "data" in gstr2b_data and "docdata" in gstr2b_data["data"] and "b2b" in gstr2b_data["data"]["docdata"]:
        for party in gstr2b_data["data"]["docdata"]["b2b"]:
            gstin = party["ctin"]
            for inv in party["inv"]:
                # Initialize variables
                txval = 0
                rt = 0
                inv_num = inv.get("inum", "UNKNOWN").strip().upper()
                inv_date = inv.get("dt", "")
                pos = inv.get("pos", "")
                
                # Extract tax values
                igst_amt = float(inv.get("igst", 0))
                cgst_amt = float(inv.get("cgst", 0))
                sgst_amt = float(inv.get("sgst", 0))
                
                # Handle the case where 'items' might be present
                if "items" in inv and len(inv["items"]) > 0:
                    # Use item level data
                    item = inv["items"][0]  # assuming first item per invoice
                    txval = float(item.get("txval", 0))
                    rt = item.get("rt", 0)
                else:
                    # Try to use invoice level data
                    if "txval" in inv:
                        txval = float(inv["txval"])
                    
                    # Determine rate from tax amounts if not directly available
                    if rt == 0:
                        # Calculate total tax
                        total_tax = igst_amt + cgst_amt + sgst_amt
                        
                        # If there's a taxable value and tax amount, derive rate
                        if txval > 0 and total_tax > 0:
                            if igst_amt > 0:
                                rt = round((igst_amt / txval) * 100)
                            elif cgst_amt > 0 and sgst_amt > 0:
                                rt = round(((cgst_amt + sgst_amt) / txval) * 100)
                
                # Determine supply type from tax composition rather than POS
                supply_type = "INTER" if igst_amt > 0 else "INTRA"
                
                # Only add records with some taxable value
                if txval > 0:
                    gstr2b_records.append({
                        "gstin": gstin.upper(),
                        "inv_num": inv_num,
                        "date": inv_date,
                        "taxable_value": round(txval, 2),
                        "rate": rt,
                        "supply_type": supply_type
                    })
    else:
        # Try to handle other possible structures
        st.warning("Standard GSTR-2B structure not found. Attempting to parse alternative formats...")
        
        # Add debug info
        st.json({"keys_in_data": list(gstr2b_data.keys())})
        
        # Try alternate parsing based on common structures
        if "b2b" in gstr2b_data:
            # Direct b2b array at root level
            for party in gstr2b_data["b2b"]:
                gstin = party.get("ctin", "")
                if "inv" in party:
                    for inv in party["inv"]:
                        # Extract data using similar logic as above
                        txval = 0
                        rt = 0
                        igst_amt = float(inv.get("igst", 0))
                        cgst_amt = float(inv.get("cgst", 0))
                        sgst_amt = float(inv.get("sgst", 0))
                        
                        if "items" in inv and len(inv["items"]) > 0:
                            item = inv["items"][0]
                            txval = float(item.get("txval", 0))
                            rt = item.get("rt", 0)
                        else:
                            txval = float(inv.get("txval", 0))
                            
                            # Determine rate from tax amounts if not available
                            if rt == 0 and txval > 0:
                                total_tax = igst_amt + cgst_amt + sgst_amt
                                if total_tax > 0:
                                    if igst_amt > 0:
                                        rt = round((igst_amt / txval) * 100)
                                    elif cgst_amt > 0 and sgst_amt > 0:
                                        rt = round(((cgst_amt + sgst_amt) / txval) * 100)
                        
                        # Determine supply type from tax composition
                        supply_type = "INTER" if igst_amt > 0 else "INTRA"
                        
                        if txval > 0:
                            gstr2b_records.append({
                                "gstin": gstin.upper(),
                                "inv_num": inv.get("inum", "").strip().upper(),
                                "date": inv.get("dt", ""),
                                "taxable_value": round(txval, 2),
                                "rate": rt,
                                "supply_type": supply_type
                            })
        
        if not gstr2b_records:
            st.error("❌ Could not parse the GSTR-2B file structure. Please check the format.")

    if not gstr2b_records:
        st.error("❌ No valid invoice records found in the GSTR-2B data.")
    else:
        df_2b = pd.DataFrame(gstr2b_records)

        # --- Load Purchase Register CSV ---
        try:
            df_csv = pd.read_csv(purchase_file)
        except Exception as e:
            st.error(f"❌ Error reading CSV file: {e}")
            st.stop()
        
        # Display the first few rows to understand the structure
        st.subheader("CSV Preview")
        st.dataframe(df_csv.head(5))
        
        # Display actual CSV columns for debugging
        st.subheader("CSV File Columns")
        st.write(df_csv.columns.tolist())
        
        # Convert numeric columns to float, handling non-numeric values
        for col in df_csv.columns:
            if col in ["Gross Total", "CGST", "SGST", "IGST", "Purchase Local @18%", 
                       "Purchase Interstate @18%", "Vechile Repair & Maintance Exp. (Local @18%)",
                       "Vechile Repair & Miantance Exp. (Local @28%)", "VECHILE REPAIR & MAINTANCE EXP. (INTERSTATE @28%)"]:
                df_csv[col] = pd.to_numeric(df_csv[col], errors='coerce').fillna(0)
        
        # Map the specific columns from your CSV to required fields
        column_rename_map = {
            "Voucher No.": "inv_num",
            "Date": "date",
            "GSTIN/UIN": "gstin"
        }
        
        # Create a derive taxable value and rate function
        def derive_tax_info(row):
            taxable_val = 0
            applicable_rate = 0
            supply_type = "INTRA"  # Default
            
            # Check each local tax rate column
            local_rate_columns = {
                "Purchase Local @18%": 18,
                "Vechile Repair & Maintance Exp. (Local @18%)": 18,
                "Vechile Repair & Miantance Exp. (Local @28%)": 28
            }
            
            interstate_rate_columns = {
                "Purchase Interstate @18%": 18,
                "VECHILE REPAIR & MAINTANCE EXP. (INTERSTATE @28%)": 28
            }
            
            # Check local rate columns
            for col, rate in local_rate_columns.items():
                if col in row and pd.notna(row[col]) and row[col] > 0:
                    taxable_val += row[col]
                    applicable_rate = rate
                    supply_type = "INTRA"
            
            # Check interstate rate columns
            for col, rate in interstate_rate_columns.items():
                if col in row and pd.notna(row[col]) and row[col] > 0:
                    taxable_val += row[col]
                    applicable_rate = rate
                    supply_type = "INTER"
            
            # If no taxable value found, use Gross Total and determine type from taxes
            if taxable_val == 0 and "Gross Total" in row and pd.notna(row["Gross Total"]) and row["Gross Total"] > 0:
                # Determine if INTRA or INTER based on tax columns
                if "IGST" in row and pd.notna(row["IGST"]) and row["IGST"] > 0:
                    supply_type = "INTER"
                    total_tax = row["IGST"]
                    if total_tax > 0:
                        taxable_val = row["Gross Total"] - total_tax
                        applicable_rate = round((total_tax / taxable_val) * 100) if taxable_val > 0 else 0
                    else:
                        taxable_val = row["Gross Total"]
                elif "CGST" in row and "SGST" in row and pd.notna(row["CGST"]) and pd.notna(row["SGST"]) and row["CGST"] > 0 and row["SGST"] > 0:
                    supply_type = "INTRA"
                    total_tax = row["CGST"] + row["SGST"]
                    if total_tax > 0:
                        taxable_val = row["Gross Total"] - total_tax
                        applicable_rate = round((total_tax / taxable_val) * 100) if taxable_val > 0 else 0
                    else:
                        taxable_val = row["Gross Total"]
                else:
                    # If we can't determine, use Gross Total
                    taxable_val = row["Gross Total"]
                    # Try to infer rate from common rates
                    if "Particulars" in row and isinstance(row["Particulars"], str):
                        if "18%" in row["Particulars"]:
                            applicable_rate = 18
                        elif "28%" in row["Particulars"]:
                            applicable_rate = 28
                        elif "12%" in row["Particulars"]:
                            applicable_rate = 12
                        elif "5%" in row["Particulars"]:
                            applicable_rate = 5
                        else:
                            applicable_rate = 18  # Default most common rate
            
            return pd.Series([taxable_val, applicable_rate, supply_type])
        
        # Apply the function to each row
        df_csv[["taxable_value", "rate", "supply_type"]] = df_csv.apply(derive_tax_info, axis=1)
        
        # Now rename columns
        df_csv.rename(columns=column_rename_map, inplace=True)
        
        required_cols = {"gstin", "inv_num", "date", "taxable_value", "rate", "supply_type"}
        if not required_cols.issubset(df_csv.columns):
            st.error(f"❌ The CSV file is missing required columns: {required_cols - set(df_csv.columns)}")
        else:
            # Standardize data - handle potential non-string columns
            df_csv["gstin"] = df_csv["gstin"].astype(str).str.upper().str.strip()
            df_csv["inv_num"] = df_csv["inv_num"].astype(str).str.upper().str.strip()
            
            # Handle date conversion with flexible formats
            def convert_date_format(date_str):
                try:
                    if isinstance(date_str, str):
                        # Try different date formats
                        for fmt in ('%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%d %b %Y'):
                            try:
                                return datetime.strptime(date_str, fmt).strftime('%d-%m-%Y')
                            except:
                                continue
                    return date_str
                except:
                    return date_str
            
            df_csv["date"] = df_csv["date"].apply(convert_date_format)
            df_2b["date"] = df_2b["date"].apply(convert_date_format)

            # --- Create enhanced invoice number normalization ---
            def normalize_invoice_num(inv_num):
                if not isinstance(inv_num, str):
                    return ""
                
                # Convert to uppercase
                inv_num = inv_num.upper()
                
                # Remove all non-alphanumeric characters
                clean_inv = re.sub(r'[^A-Z0-9]', '', inv_num)
                
                # Remove common prefixes
                prefixes = ['INV', 'INVOICE', 'BILL', 'SI', 'TAX']
                for prefix in prefixes:
                    if clean_inv.startswith(prefix):
                        clean_inv = clean_inv[len(prefix):]
                
                # Try to extract only the numeric part if it exists
                num_only = re.sub(r'[^0-9]', '', clean_inv)
                
                # Return both versions for more matching options
                return clean_inv, num_only
            
            # Create normalized invoice columns
            df_2b["norm_inv_num"], df_2b["num_only"] = zip(*df_2b["inv_num"].apply(normalize_invoice_num))
            df_csv["norm_inv_num"], df_csv["num_only"] = zip(*df_csv["inv_num"].apply(normalize_invoice_num))
            
            # --- Reconciliation ---
            matched = []
            mismatched = []
            missing_in_csv = []
            missing_in_json = []

            # Match by GSTIN + Invoice Number with multiple matching strategies
            for _, row in df_2b.iterrows():
                # Flag to track if a match was found
                match_found = False
                
                # Strategy 1: Exact match on GSTIN + Invoice Number
                match = df_csv[(df_csv["gstin"] == row["gstin"]) & (df_csv["inv_num"] == row["inv_num"])]
                
                # Strategy 2: Match on GSTIN + normalized invoice number
                if match.empty:
                    match = df_csv[(df_csv["gstin"] == row["gstin"]) & (df_csv["norm_inv_num"] == row["norm_inv_num"])]
                
                # Strategy 3: Match on GSTIN + numeric-only invoice number
                if match.empty and row["num_only"]:
                    match = df_csv[(df_csv["gstin"] == row["gstin"]) & (df_csv["num_only"] == row["num_only"])]
                
                # Strategy 4: Try fuzzy match on amount (if GSTIN matches but invoice doesn't)
                if match.empty:
                    # Find potential matches by GSTIN only
                    gstin_matches = df_csv[df_csv["gstin"] == row["gstin"]]
                    if not gstin_matches.empty:
                        # Look for close match on amount (within 1% or ₹10)
                        for _, csv_row in gstin_matches.iterrows():
                            diff = abs(csv_row["taxable_value"] - row["taxable_value"])
                            percent_diff = (diff / row["taxable_value"]) * 100 if row["taxable_value"] > 0 else 100
                            
                            if percent_diff < 1 or diff < 10:
                                match = pd.DataFrame([csv_row])
                                st.info(f"Found fuzzy match for invoice {row['inv_num']} based on amount similarity")
                                break
                
                if match.empty:
                    missing_in_csv.append(row.to_dict())
                else:
                    match_row = match.iloc[0]
                    # Use a percentage threshold for amount matching
                    value_diff = abs(match_row["taxable_value"] - row["taxable_value"])
                    value_percent_diff = (value_diff / row["taxable_value"]) * 100 if row["taxable_value"] > 0 else 100
                    
                    # More flexible matching criteria
                    # Consider matched if within 10% or within 100 rupees absolute difference
                    value_matched = value_percent_diff < 10 or value_diff < 100
                    
                    # Rate can be 0 in some cases when we couldn't determine it
                    rate_matched = match_row["rate"] == row["rate"] or row["rate"] == 0 or match_row["rate"] == 0
                    
                    if value_matched and rate_matched:
                        matched.append({
                            **row.to_dict(),
                            "csv_inv_num": match_row["inv_num"],
                            "csv_taxable_value": match_row["taxable_value"],
                            "exact_match": row["inv_num"] == match_row["inv_num"]
                        })
                        # Mark as processed to avoid duplicate matches
                        df_csv = df_csv.drop(match.index)
                    else:
                        mismatched.append({
                            **row.to_dict(),
                            "csv_inv_num": match_row["inv_num"],
                            "csv_taxable_value": match_row["taxable_value"],
                            "csv_rate": match_row["rate"],
                            "diff_value": round(match_row["taxable_value"] - row["taxable_value"], 2),
                            "diff_percent": round(value_percent_diff, 2)
                        })
                        # Mark as processed to avoid duplicate matches
                        df_csv = df_csv.drop(match.index)

            # Now check for records in CSV not in GSTR-2B
            for _, row in df_csv.iterrows():
                missing_in_json.append(row.to_dict())

            total_invoices = len(df_2b) + len(df_csv.index.tolist())
            
            # Create summary statistics
            summary = {
                "total_invoices": total_invoices,
                "matched_count": len(matched),
                "mismatched_count": len(mismatched),
                "missing_in_csv_count": len(missing_in_csv),
                "missing_in_json_count": len(missing_in_json),
                "match_percentage": round((len(matched) / total_invoices) * 100, 2) if total_invoices > 0 else 0
            }

            st.success("✅ Reconciliation completed.")
            
            # Display summary in a more visual way
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Total Invoices", summary["total_invoices"])
            with col2:
                st.metric("Matched", summary["matched_count"], f"{summary['match_percentage']}%")
            with col3:
                st.metric("Mismatched", summary["mismatched_count"])
            with col4:
                st.metric("Missing in CSV", summary["missing_in_csv_count"])
            with col5:
                st.metric("Missing in GSTR-2B", summary["missing_in_json_count"])

            st.write("---")
            
            # Add download buttons for each dataframe
            if matched:
                st.write("### ✅ Matched Invoices")
                matched_df = pd.DataFrame(matched)
                st.dataframe(matched_df)
                csv = matched_df.to_csv(index=False)
                st.download_button(
                    label="Download matched invoices as CSV",
                    data=csv,
                    file_name="matched_invoices.csv",
                    mime="text/csv",
                )

            if mismatched:
                st.write("### ⚠️ Mismatched Invoices")
                mismatched_df = pd.DataFrame(mismatched)
                st.dataframe(mismatched_df)
                csv = mismatched_df.to_csv(index=False)
                st.download_button(
                    label="Download mismatched invoices as CSV",
                    data=csv,
                    file_name="mismatched_invoices.csv",
                    mime="text/csv",
                )

            if missing_in_csv:
                st.write("### ❌ Missing in Purchase Register (CSV)")
                missing_csv_df = pd.DataFrame(missing_in_csv)
                st.dataframe(missing_csv_df)
                csv = missing_csv_df.to_csv(index=False)
                st.download_button(
                    label="Download missing in CSV invoices",
                    data=csv,
                    file_name="missing_in_csv.csv",
                    mime="text/csv",
                )

            if missing_in_json:
                st.write("### ❌ Missing in GSTR-2B (JSON)")
                missing_json_df = pd.DataFrame(missing_in_json)
                st.dataframe(missing_json_df)
                csv = missing_json_df.to_csv(index=False)
                st.download_button(
                    label="Download missing in GSTR-2B invoices",
                    data=csv,
                    file_name="missing_in_json.csv",
                    mime="text/csv",
                )