"""
Report generation utilities for GST Reconciliation System
"""
import pandas as pd
import numpy as np
import os
from datetime import datetime

def generate_reconciliation_report(recon_type, result_df):
    """
    Generate comprehensive reconciliation report
    
    Parameters:
    -----------
    recon_type : str
        Type of reconciliation that was performed
    result_df : DataFrame
        Reconciliation results dataframe
    
    Returns:
    --------
    dict of DataFrames
        Dictionary of dataframes for different report sheets
    """
    # Create a copy of the results to avoid modifying original
    df = result_df.copy()
    
    # Create report dictionary to hold multiple sheets
    report = {
        'Detail': df.copy()  # Detailed results
    }
    
    # Generate summary sheet
    summary_df = generate_summary(recon_type, df)
    report['Summary'] = summary_df
    
    # Generate reconciliation analysis based on type
    if recon_type == 'gstr1_books':
        report.update(generate_gstr1_books_analysis(df))
    elif recon_type == 'gstr2_books':
        report.update(generate_gstr2_books_analysis(df))
    elif recon_type == 'gstr3b_gstr1':
        report.update(generate_gstr3b_gstr1_analysis(df))
    elif recon_type == 'gstr3b_books':
        report.update(generate_gstr3b_books_analysis(df))
    elif recon_type == 'itc_gstr3b_gstr2b':
        report.update(generate_itc_analysis(df))
    elif recon_type == 'itc_eligibility':
        report.update(generate_itc_eligibility_analysis(df))
    elif recon_type == 'turnover_recon':
        report.update(generate_turnover_analysis(df))
    
    # Generate mismatch analysis
    report['Mismatches'] = generate_mismatch_analysis(df)
    
    return report

def generate_summary(recon_type, df):
    """Generate summary sheet for reconciliation report"""
    # Create an empty dataframe for summary
    summary_df = pd.DataFrame(columns=['Metric', 'Value'])
    
    # Add reconciliation type and date
    summary_data = [
        {'Metric': 'Reconciliation Type', 'Value': format_recon_type(recon_type)},
        {'Metric': 'Report Date', 'Value': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    ]
    
    # Add record counts
    total_records = len(df)
    matched_records = len(df[df['Status'] == 'Matched']) if 'Status' in df.columns else 0
    mismatched_records = len(df[df['Status'] == 'Mismatched']) if 'Status' in df.columns else 0
    only_source1 = len(df[df['Status'] == 'Only in Source 1']) if 'Status' in df.columns else 0
    only_source2 = len(df[df['Status'] == 'Only in Source 2']) if 'Status' in df.columns else 0
    
    summary_data.extend([
        {'Metric': 'Total Records', 'Value': total_records},
        {'Metric': 'Matched Records', 'Value': matched_records},
        {'Metric': 'Mismatched Records', 'Value': mismatched_records},
        {'Metric': 'Only in Source 1', 'Value': only_source1},
        {'Metric': 'Only in Source 2', 'Value': only_source2}
    ])
    
    # Add total differences
    if 'Difference' in df.columns:
        total_diff = df['Difference'].sum() if pd.api.types.is_numeric_dtype(df['Difference']) else 0
        abs_total_diff = df['Difference'].abs().sum() if pd.api.types.is_numeric_dtype(df['Difference']) else 0
        
        summary_data.extend([
            {'Metric': 'Net Difference', 'Value': total_diff},
            {'Metric': 'Absolute Difference', 'Value': abs_total_diff}
        ])
    
    # Add match percentage
    if total_records > 0:
        match_percentage = (matched_records / total_records) * 100
        summary_data.append({'Metric': 'Match Percentage', 'Value': f"{match_percentage:.2f}%"})
    
    # Assign to dataframe
    summary_df = pd.DataFrame(summary_data)
    
    return summary_df

def generate_mismatch_analysis(df):
    """Generate analysis of mismatches"""
    # Filter only mismatched records
    if 'Status' in df.columns:
        mismatches_df = df[df['Status'] == 'Mismatched'].copy()
    else:
        # If no status column, use difference threshold
        mismatches_df = df[df['Difference'].abs() > 0].copy()
    
    # Sort by absolute difference
    if 'Difference' in mismatches_df.columns:
        mismatches_df = mismatches_df.sort_values(by='Difference', key=abs, ascending=False)
    
    return mismatches_df

def generate_gstr1_books_analysis(df):
    """Generate analysis for GSTR-1 vs Books reconciliation"""
    report = {}
    
    # Add tax type analysis if available
    if 'TaxType' in df.columns or 'Tax_Type' in df.columns:
        tax_col = 'TaxType' if 'TaxType' in df.columns else 'Tax_Type'
        
        # Group by tax type
        tax_analysis = df.groupby(tax_col).agg({
            'Source1_Value': 'sum',
            'Source2_Value': 'sum',
            'Difference': 'sum'
        }).reset_index()
        
        tax_analysis['Match_Percentage'] = 100 - (
            (tax_analysis['Difference'].abs() / 
             tax_analysis[['Source1_Value', 'Source2_Value']].abs().max(axis=1)) * 100
        )
        
        report['Tax_Analysis'] = tax_analysis
    
    # Invoice level analysis
    if 'InvoiceNo' in df.columns or 'Invoice_No' in df.columns:
        inv_col = 'InvoiceNo' if 'InvoiceNo' in df.columns else 'Invoice_No'
        
        # Top mismatches by invoice
        top_inv_mismatches = df[df['Status'] == 'Mismatched'].sort_values(
            by='Difference', key=abs, ascending=False
        ).head(20)
        
        report['Top_Invoice_Mismatches'] = top_inv_mismatches
    
    return report

def generate_gstr2_books_analysis(df):
    """Generate analysis for GSTR-2A/2B vs Books reconciliation"""
    report = {}
    
    # Add supplier analysis if available
    if 'SupplierGSTIN' in df.columns or 'Supplier_GSTIN' in df.columns:
        supplier_col = 'SupplierGSTIN' if 'SupplierGSTIN' in df.columns else 'Supplier_GSTIN'
        
        # Group by supplier
        supplier_analysis = df.groupby(supplier_col).agg({
            'Source1_Value': 'sum',
            'Source2_Value': 'sum',
            'Difference': 'sum',
            'Status': lambda x: (x == 'Matched').sum()
        }).reset_index()
        
        supplier_analysis.rename(columns={'Status': 'Matched_Count'}, inplace=True)
        supplier_analysis['Total_Count'] = df.groupby(supplier_col).size().values
        supplier_analysis['Match_Percentage'] = (supplier_analysis['Matched_Count'] / 
                                              supplier_analysis['Total_Count']) * 100
        
        report['Supplier_Analysis'] = supplier_analysis
    
    return report

def generate_gstr3b_gstr1_analysis(df):
    """Generate analysis for GSTR-3B vs GSTR-1 reconciliation"""
    report = {}
    
    # Tax rate analysis
    if 'TaxRate' in df.columns or 'Tax_Rate' in df.columns:
        rate_col = 'TaxRate' if 'TaxRate' in df.columns else 'Tax_Rate'
        
        # Group by tax rate
        rate_analysis = df.groupby(rate_col).agg({
            'Source1_Value': 'sum',  # GSTR-3B
            'Source2_Value': 'sum',  # GSTR-1
            'Difference': 'sum'
        }).reset_index()
        
        rate_analysis['Variance_Percentage'] = (
            rate_analysis['Difference'] / rate_analysis['Source2_Value'] * 100
        ).fillna(0)
        
        report['Rate_Analysis'] = rate_analysis
    
    return report

def generate_gstr3b_books_analysis(df):
    """Generate analysis for GSTR-3B vs Books reconciliation"""
    # Similar to GSTR-3B vs GSTR-1 analysis
    return generate_gstr3b_gstr1_analysis(df)

def generate_itc_analysis(df):
    """Generate analysis for ITC reconciliation"""
    report = {}
    
    # ITC eligibility analysis
    if 'ITCType' in df.columns or 'ITC_Type' in df.columns:
        itc_col = 'ITCType' if 'ITCType' in df.columns else 'ITC_Type'
        
        # Group by ITC type
        itc_analysis = df.groupby(itc_col).agg({
            'Source1_Value': 'sum',
            'Source2_Value': 'sum',
            'Difference': 'sum'
        }).reset_index()
        
        report['ITC_Analysis'] = itc_analysis
    
    return report

def generate_itc_eligibility_analysis(df):
    """Generate analysis for ITC eligibility reconciliation"""
    # Similar to ITC analysis
    return generate_itc_analysis(df)

def generate_turnover_analysis(df):
    """Generate analysis for turnover reconciliation"""
    report = {}
    
    # If we have all three sources
    if all(col in df.columns for col in ['Books_Value', 'GST_Value', 'FS_Value']):
        # Calculate total values
        total_books = df['Books_Value'].sum()
        total_gst = df['GST_Value'].sum()
        total_fs = df['FS_Value'].sum()
        
        # Create summary
        turnover_summary = pd.DataFrame([
            {'Source': 'Books', 'Value': total_books},
            {'Source': 'GST Returns', 'Value': total_gst},
            {'Source': 'Financial Statements', 'Value': total_fs}
        ])
        
        # Calculate differences
        diff_data = [
            {'Comparison': 'Books vs GST', 'Difference': total_books - total_gst},
            {'Comparison': 'Books vs FS', 'Difference': total_books - total_fs},
            {'Comparison': 'GST vs FS', 'Difference': total_gst - total_fs}
        ]
        diff_df = pd.DataFrame(diff_data)
        
        report['Turnover_Summary'] = turnover_summary
        report['Turnover_Differences'] = diff_df
    
    return report

def format_recon_type(recon_type):
    """Format reconciliation type for display"""
    type_mapping = {
        'gstr1_books': 'GSTR-1 vs Books (Sales Register)',
        'gstr2_books': 'GSTR-2A/2B vs Books (Purchase Register)',
        'gstr3b_gstr1': 'GSTR-3B vs GSTR-1',
        'gstr3b_books': 'GSTR-3B vs Books (Output Tax)',
        'itc_gstr3b_gstr2b': 'ITC in GSTR-3B vs GSTR-2B',
        'itc_eligibility': 'ITC in Books vs Eligible ITC',
        'gstr1_eway': 'GSTR-1 vs E-Way Bills',
        'gstr2_eway': 'GSTR-2A/2B vs E-Way Bills',
        'gstr1_einvoice': 'GSTR-1 vs E-invoice',
        'turnover_recon': 'Turnover Reconciliation'
    }
    
    return type_mapping.get(recon_type, recon_type)

def generate_consolidated_report(recon_results, output_dir, company_name, period):
    """
    Generate consolidated reconciliation report combining multiple reconciliation results
    
    Parameters:
    -----------
    recon_results : dict
        Dictionary with reconciliation type as key and result DataFrame as value
    output_dir : str
        Directory to save the consolidated report
    company_name : str
        Name of the company for which report is being generated
    period : str
        Period for which reconciliation is performed (e.g., 'FY 2024-25 Q1')
    
    Returns:
    --------
    str
        Path to the generated report file
    """
    # Create file path for the consolidated report
    report_filename = f"{company_name} - GST Reconciliation Report - {period}.xlsx"
    report_path = os.path.join(output_dir, report_filename)
    
    # Create Excel writer
    with pd.ExcelWriter(report_path, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Create title sheet
        summary_sheet = workbook.add_worksheet('Summary')
        
        # Add report title and metadata
        title_format = workbook.add_format({
            'bold': True, 'font_size': 16, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'font_size': 12, 'align': 'left', 'valign': 'vcenter'
        })
        value_format = workbook.add_format({
            'font_size': 12, 'align': 'left', 'valign': 'vcenter'
        })
        
        # Title
        summary_sheet.merge_range('A1:F1', 'GST RECONCILIATION REPORT', title_format)
        summary_sheet.merge_range('A2:F2', company_name, title_format)
        summary_sheet.merge_range('A3:F3', period, title_format)
        
        # Add space
        row = 5
        
        # Add summary table
        summary_sheet.write(row, 0, 'Reconciliation Type', header_format)
        summary_sheet.write(row, 1, 'Total Records', header_format)
        summary_sheet.write(row, 2, 'Matched', header_format)
        summary_sheet.write(row, 3, 'Mismatched', header_format)
        summary_sheet.write(row, 4, 'Match %', header_format)
        summary_sheet.write(row, 5, 'Total Difference', header_format)
        
        row += 1
        
        # Add data for each reconciliation
        for recon_type, result_df in recon_results.items():
            # Calculate metrics
            total_records = len(result_df)
            matched_records = len(result_df[result_df['Status'] == 'Matched']) if 'Status' in result_df.columns else 0
            mismatched_records = total_records - matched_records
            match_percent = (matched_records / total_records * 100) if total_records > 0 else 0
            total_diff = result_df['Difference'].sum() if 'Difference' in result_df.columns else 0
            
            # Write to summary sheet
            summary_sheet.write(row, 0, format_recon_type(recon_type), value_format)
            summary_sheet.write(row, 1, total_records, value_format)
            summary_sheet.write(row, 2, matched_records, value_format)
            summary_sheet.write(row, 3, mismatched_records, value_format)
            summary_sheet.write(row, 4, f"{match_percent:.2f}%", value_format)
            summary_sheet.write(row, 5, total_diff, value_format)
            
            row += 1
            
            # Create detailed sheets for each reconciliation
            sheet_name = recon_type[:15]  # Limit sheet name length
            
            # Generate detailed report for this reconciliation
            detailed_report = generate_reconciliation_report(recon_type, result_df)
            
            # Write each report sheet
            for sheet_key, sheet_df in detailed_report.items():
                full_sheet_name = f"{sheet_name}_{sheet_key[:10]}"  # Create unique sheet name
                
                # Convert to DataFrame if it's not already
                if not isinstance(sheet_df, pd.DataFrame):
                    sheet_df = pd.DataFrame(sheet_df)
                
                # Write to Excel
                sheet_df.to_excel(writer, sheet_name=full_sheet_name, index=False)
                
                # Format the sheet
                worksheet = writer.sheets[full_sheet_name]
                
                # Format headers
                for col_num, value in enumerate(sheet_df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
                
                # Add conditional formatting for Status column if present
                if 'Status' in sheet_df.columns:
                    status_col = sheet_df.columns.get_loc('Status')
                    worksheet.conditional_format(1, status_col, len(sheet_df) + 1, status_col, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'Matched',
                        'format': workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
                    })
                    worksheet.conditional_format(1, status_col, len(sheet_df) + 1, status_col, {
                        'type': 'text',
                        'criteria': 'containing',
                        'value': 'Mismatched',
                        'format': workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
                    })
        
        # Set column widths for summary sheet
        summary_sheet.set_column('A:A', 30)
        summary_sheet.set_column('B:F', 15)
    
    return report_path