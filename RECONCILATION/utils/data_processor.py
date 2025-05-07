"""
Data processing utilities for GST Reconciliation System
"""
import pandas as pd
import numpy as np
from datetime import datetime
import config

def process_reconciliation(recon_type, source1_df, source2_df, source3_df=None, 
                          from_date=None, to_date=None, 
                          amount_threshold=None, percent_threshold=None):
    """
    Process reconciliation between two or more data sources
    
    Parameters:
    -----------
    recon_type : str
        Type of reconciliation to perform (e.g., 'gstr1_books', 'gstr2_books')
    source1_df : DataFrame
        First source dataframe
    source2_df : DataFrame
        Second source dataframe
    source3_df : DataFrame, optional
        Third source dataframe (used in specific reconciliations like turnover)
    from_date : datetime, optional
        Start date filter
    to_date : datetime, optional
        End date filter
    amount_threshold : float, optional
        Absolute amount threshold for reporting differences
    percent_threshold : float, optional
        Percentage threshold for reporting differences
    
    Returns:
    --------
    DataFrame
        Reconciliation results
    """
    # Set default thresholds if not provided
    if amount_threshold is None:
        amount_threshold = config.AMOUNT_THRESHOLD
    if percent_threshold is None:
        percent_threshold = config.PERCENTAGE_THRESHOLD
    
    # Get mapping configuration based on reconciliation type
    mapping_config = get_mapping_config(recon_type)
    if not mapping_config:
        raise ValueError(f"Invalid reconciliation type: {recon_type}")
    
    # Pre-process data
    source1_df = preprocess_data(source1_df, mapping_config.get('source1', {}), from_date, to_date)
    source2_df = preprocess_data(source2_df, mapping_config.get('source2', {}), from_date, to_date)
    
    if source3_df is not None and recon_type == 'turnover_recon':
        source3_df = preprocess_data(source3_df, mapping_config.get('source3', {}), from_date, to_date)
    
    # Select reconciliation method based on type
    if recon_type == 'gstr1_books':
        result_df = reconcile_gstr1_with_books(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr2_books':
        result_df = reconcile_gstr2_with_books(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr3b_gstr1':
        result_df = reconcile_gstr3b_with_gstr1(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr3b_books':
        result_df = reconcile_gstr3b_with_books(source1_df, source2_df, mapping_config)
    elif recon_type == 'itc_gstr3b_gstr2b':
        result_df = reconcile_itc_gstr3b_gstr2b(source1_df, source2_df, mapping_config)
    elif recon_type == 'itc_eligibility':
        result_df = reconcile_itc_eligibility(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr1_eway':
        result_df = reconcile_gstr1_with_eway(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr2_eway':
        result_df = reconcile_gstr2_with_eway(source1_df, source2_df, mapping_config)
    elif recon_type == 'gstr1_einvoice':
        result_df = reconcile_gstr1_with_einvoice(source1_df, source2_df, mapping_config)
    elif recon_type == 'turnover_recon':
        result_df = reconcile_turnover(source1_df, source2_df, source3_df, mapping_config)
    else:
        result_df = generic_reconciliation(source1_df, source2_df, mapping_config)
    
    # Apply thresholds and add status
    result_df = apply_thresholds(result_df, amount_threshold, percent_threshold)
    
    return result_df

def get_mapping_config(recon_type):
    """Get mapping configuration for the reconciliation type"""
    mapping_configs = {
        'gstr1_books': config.GSTR1_BOOKS_MAPPING,
        'gstr2_books': config.GSTR2_BOOKS_MAPPING,
        'gstr3b_gstr1': config.GSTR3B_GSTR1_MAPPING,
        'gstr3b_books': config.GSTR3B_BOOKS_MAPPING,
        'itc_gstr3b_gstr2b': config.ITC_GSTR3B_GSTR2B_MAPPING,
        'itc_eligibility': config.ITC_BOOKS_ELIGIBILITY_MAPPING,
        'gstr1_eway': config.GSTR1_EWAY_MAPPING,
        'gstr2_eway': config.GSTR2_EWAY_MAPPING,
        'gstr1_einvoice': config.GSTR1_EINVOICE_MAPPING,
        'turnover_recon': config.TURNOVER_MAPPING
    }
    return mapping_configs.get(recon_type, {})

def preprocess_data(df, mapping, from_date=None, to_date=None):
    """
    Preprocess data for reconciliation
    
    Parameters:
    -----------
    df : DataFrame
        Source dataframe
    mapping : dict
        Field mapping configuration
    from_date : datetime, optional
        Start date filter
    to_date : datetime, optional
        End date filter
    
    Returns:
    --------
    DataFrame
        Preprocessed dataframe
    """
    if df is None:
        return None
    
    # Handle column renames if defined
    if 'column_mapping' in mapping:
        df = df.rename(columns=mapping['column_mapping'])
    
    # Convert date columns
    date_column = mapping.get('date_column')
    if date_column and date_column in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df[date_column]):
            # Try to convert date strings to datetime
            try:
                df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
            except:
                # If conversion fails, leave as is
                pass
    
        # Apply date filters if provided
        if from_date is not None and date_column in df.columns:
            df = df[df[date_column] >= from_date]
        
        if to_date is not None and date_column in df.columns:
            df = df[df[date_column] <= to_date]
    
    # Handle numeric columns
    for col in mapping.get('numeric_columns', []):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Group data if needed
    if 'group_by' in mapping and 'aggregations' in mapping:
        df = df.groupby(mapping['group_by']).agg(mapping['aggregations']).reset_index()
    
    return df

def generic_reconciliation(df1, df2, mapping):
    """Generic reconciliation function for comparing two dataframes"""
    # Get key columns and value columns from mapping
    key_columns = mapping.get('key_columns', [])
    source1_value_column = mapping.get('source1', {}).get('value_column')
    source2_value_column = mapping.get('source2', {}).get('value_column')
    
    if not key_columns or not source1_value_column or not source2_value_column:
        raise ValueError("Missing key or value column mapping")
    
    # Create copies to avoid modifying original dataframes
    df1_copy = df1.copy()
    df2_copy = df2.copy()
    
    # Standardize column names for joined dataframe
    df1_copy = df1_copy.rename(columns={source1_value_column: 'Source1_Value'})
    df2_copy = df2_copy.rename(columns={source2_value_column: 'Source2_Value'})
    
    # Perform outer join on key columns
    result = pd.merge(
        df1_copy, 
        df2_copy, 
        on=key_columns, 
        how='outer', 
        suffixes=('_source1', '_source2')
    )
    
    # Fill missing values
    result['Source1_Value'] = result['Source1_Value'].fillna(0)
    result['Source2_Value'] = result['Source2_Value'].fillna(0)
    
    # Calculate difference
    result['Difference'] = result['Source1_Value'] - result['Source2_Value']
    
    # Calculate percentage difference
    result['Percent_Difference'] = 0.0
    mask = (result['Source1_Value'] != 0) | (result['Source2_Value'] != 0)
    
    if mask.any():
        # Calculate base for percentage
        base_values = result.loc[mask, ['Source1_Value', 'Source2_Value']].abs().max(axis=1)
        result.loc[mask, 'Percent_Difference'] = (
            result.loc[mask, 'Difference'].abs() / base_values
        ) * 100
    
    return result

def reconcile_gstr1_with_books(gstr1_df, books_df, mapping):
    """Reconcile GSTR-1 with Sales Register (Books)"""
    # This is a specific implementation for GSTR-1 vs Books
    return generic_reconciliation(gstr1_df, books_df, mapping)

def reconcile_gstr2_with_books(gstr2_df, books_df, mapping):
    """Reconcile GSTR-2A/2B with Purchase Register (Books)"""
    return generic_reconciliation(gstr2_df, books_df, mapping)

def reconcile_gstr3b_with_gstr1(gstr3b_df, gstr1_df, mapping):
    """Reconcile GSTR-3B with GSTR-1"""
    return generic_reconciliation(gstr3b_df, gstr1_df, mapping)

def reconcile_gstr3b_with_books(gstr3b_df, books_df, mapping):
    """Reconcile GSTR-3B with Books (Output Tax)"""
    return generic_reconciliation(gstr3b_df, books_df, mapping)

def reconcile_itc_gstr3b_gstr2b(gstr3b_df, gstr2b_df, mapping):
    """Reconcile ITC in GSTR-3B with GSTR-2B"""
    return generic_reconciliation(gstr3b_df, gstr2b_df, mapping)

def reconcile_itc_eligibility(books_itc_df, eligible_itc_df, mapping):
    """Reconcile ITC in Books with Eligible ITC"""
    return generic_reconciliation(books_itc_df, eligible_itc_df, mapping)

def reconcile_gstr1_with_eway(gstr1_df, eway_df, mapping):
    """Reconcile GSTR-1 with E-Way Bills"""
    return generic_reconciliation(gstr1_df, eway_df, mapping)

def reconcile_gstr2_with_eway(gstr2_df, eway_df, mapping):
    """Reconcile GSTR-2A/2B with E-Way Bills"""
    return generic_reconciliation(gstr2_df, eway_df, mapping)

def reconcile_gstr1_with_einvoice(gstr1_df, einvoice_df, mapping):
    """Reconcile GSTR-1 with E-invoice"""
    return generic_reconciliation(gstr1_df, einvoice_df, mapping)

def reconcile_turnover(books_df, gst_df, fs_df, mapping):
    """
    Perform turnover reconciliation among books, GST returns, and financial statements
    
    This is a more complex reconciliation involving three data sources
    """
    # First reconcile books with GST returns
    books_gst_result = generic_reconciliation(books_df, gst_df, {
        'key_columns': mapping.get('key_columns', []),
        'source1': mapping.get('source1', {}),
        'source2': mapping.get('source2', {})
    })
    
    # Then reconcile the result with financial statements
    if fs_df is not None:
        # Extract the necessary columns for second reconciliation
        intermediate_df = books_gst_result[mapping.get('key_columns', []) + ['Difference']].copy()
        intermediate_df.rename(columns={'Difference': 'Books_GST_Difference'}, inplace=True)
        
        # Set up mapping for second reconciliation
        fs_mapping = {
            'key_columns': mapping.get('key_columns', []),
            'source1': {'value_column': 'Books_GST_Difference'},
            'source2': mapping.get('source3', {})
        }
        
        # Perform second reconciliation
        final_result = generic_reconciliation(intermediate_df, fs_df, fs_mapping)
        
        # Add original source columns back 
        final_result = pd.merge(
            final_result,
            books_gst_result[['Source1_Value', 'Source2_Value'] + mapping.get('key_columns', [])],
            on=mapping.get('key_columns', []),
            how='inner'
        )
        
        # Rename for clarity
        final_result.rename(columns={
            'Source1_Value_x': 'FS_Value',
            'Source1_Value_y': 'Books_Value',
            'Source2_Value': 'GST_Value'
        }, inplace=True)
        
        return final_result
    else:
        # If no financial statements provided, return the books vs GST reconciliation
        return books_gst_result

def apply_thresholds(df, amount_threshold, percent_threshold):
    """
    Apply thresholds to reconciliation results and add status column
    
    Parameters:
    -----------
    df : DataFrame
        Reconciliation results dataframe
    amount_threshold : float
        Absolute amount threshold for reporting differences
    percent_threshold : float
        Percentage threshold for reporting differences
    
    Returns:
    --------
    DataFrame
        Results with status column added
    """
    # Add Status column
    df['Status'] = 'Matched'
    
    # Check for differences exceeding thresholds
    abs_diff_mask = df['Difference'].abs() > amount_threshold
    percent_diff_mask = df['Percent_Difference'] > (percent_threshold * 100)
    
    # Combine masks
    mismatch_mask = abs_diff_mask & percent_diff_mask
    
    # Apply status
    df.loc[mismatch_mask, 'Status'] = 'Mismatched'
    
    # Check for missing data
    if 'Source1_Value' in df.columns and 'Source2_Value' in df.columns:
        source1_null = df['Source1_Value'].isna() | (df['Source1_Value'] == 0)
        source2_null = df['Source2_Value'].isna() | (df['Source2_Value'] == 0)
        
        # Only in source 1
        df.loc[source2_null & ~source1_null, 'Status'] = 'Only in Source 1'
        
        # Only in source 2
        df.loc[source1_null & ~source2_null, 'Status'] = 'Only in Source 2'
    
    # Add color coding helper column for Excel exports
    df['_color_code'] = df['Status'].map({
        'Matched': 'green',
        'Mismatched': 'red',
        'Only in Source 1': 'orange',
        'Only in Source 2': 'yellow'
    })
    
    return df