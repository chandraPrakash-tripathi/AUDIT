"""
GSTR-2A/2B vs Books (Purchase Register) Reconciliation Module
"""
import pandas as pd
import numpy as np
from config import GSTR2_BOOKS_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def standardize_columns(df):
    """
    Standardize dataframe column names by stripping whitespace and converting to title case.
    """
    df.columns = [col.strip().title() for col in df.columns]
    return df

def format_date_columns(df, date_columns):
    """
    Convert columns in date_columns to datetime format.
    """
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def clean_numeric_data(df, numeric_cols):
    """
    Clean numeric columns by converting them to numeric dtype.
    """
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

class GSTR2BooksReconciliation:
    """Class to handle reconciliation between GSTR-2A/2B and Books (Purchase Register)"""
    
    def __init__(self):
        """Initialize the reconciliation module"""
        self.mapping = GSTR2_BOOKS_MAPPING
        self.amount_threshold = AMOUNT_THRESHOLD
        self.percentage_threshold = PERCENTAGE_THRESHOLD
        
    def load_data(self, gstr2_file, books_file, gstr_type="2B"):
        """
        Load GSTR-2A/2B and Books data from files
        
        Args:
            gstr2_file (str): Path to GSTR-2A/2B data file
            books_file (str): Path to Books (Purchase Register) data file
            gstr_type (str): Type of GSTR-2 file ('2A' or '2B')
            
        Returns:
            tuple: Dataframes containing GSTR-2A/2B and Books data
        """
        try:
            # Load GSTR-2A/2B data
            gstr2_df = pd.read_excel(gstr2_file)
            
            # Load Books (Purchase Register) data
            books_df = pd.read_excel(books_file)
            
            # Standardize column names
            gstr2_df = standardize_columns(gstr2_df)
            books_df = standardize_columns(books_df)
            
            # Format date columns
            gstr2_df = format_date_columns(gstr2_df, ["Invoice Date"])
            books_df = format_date_columns(books_df, ["Invoice Date"])
            
            # Clean numeric data
            numeric_cols = ["Invoice Value", "Taxable Value", "Integrated Tax", 
                           "Central Tax", "State/UT Tax", "Cess", "Rate"]
            gstr2_df = clean_numeric_data(gstr2_df, numeric_cols)
            books_df = clean_numeric_data(books_df, numeric_cols)
            
            # Add GSTR type column for reference
            gstr2_df['GSTR_Type'] = gstr_type
            
            return gstr2_df, books_df
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def map_columns(self, gstr2_df, books_df):
        """
        Map columns from GSTR-2A/2B and Books data based on defined mappings
        
        Args:
            gstr2_df (DataFrame): GSTR-2A/2B data
            books_df (DataFrame): Books data
            
        Returns:
            tuple: Dataframes with mapped columns
        """
        # Create mapping dictionaries
        gstr2_cols = list(self.mapping.keys())
        books_cols = list(self.mapping.values())
        
        # Filter and rename columns
        try:
            # Select required columns from GSTR-2A/2B data (if they exist)
            gstr2_available_cols = [col for col in gstr2_cols if col in gstr2_df.columns]
            # Add GSTR_Type column if it exists
            if 'GSTR_Type' in gstr2_df.columns:
                gstr2_available_cols.append('GSTR_Type')
            gstr2_mapped_df = gstr2_df[gstr2_available_cols].copy()
            
            # Select required columns from Books data (if they exist)
            books_available_cols = [col for col in books_cols if col in books_df.columns]
            books_mapped_df = books_df[books_available_cols].copy()
            
            # Create reverse mapping for renaming Books columns to match GSTR-2A/2B
            reverse_mapping = {v: k for k, v in self.mapping.items()}
            books_mapped_df = books_mapped_df.rename(columns=reverse_mapping)
            
            return gstr2_mapped_df, books_mapped_df
            
        except Exception as e:
            raise Exception(f"Error mapping columns: {str(e)}")
    
    def reconcile(self, gstr2_df, books_df):
        """
        Reconcile GSTR-2A/2B data with Books data
        
        Args:
            gstr2_df (DataFrame): GSTR-2A/2B data with mapped columns
            books_df (DataFrame): Books data with mapped columns
            
        Returns:
            dict: Reconciliation results with matches, mismatches, missing entries
        """
        try:
            # Identify key columns for matching
            key_columns = ["Invoice Number", "Invoice Date", "GSTIN of Supplier"]
            value_columns = ["Invoice Value", "Taxable Value", "Integrated Tax", 
                            "Central Tax", "State/UT Tax", "Cess"]
            
            # Create key for matching
            gstr2_df['match_key'] = gstr2_df.apply(
                lambda x: f"{x['Invoice Number']}_{x['Invoice Date'].strftime('%Y-%m-%d')}_{x['GSTIN of Supplier']}", 
                axis=1
            )
            
            books_df['match_key'] = books_df.apply(
                lambda x: f"{x['Invoice Number']}_{x['Invoice Date'].strftime('%Y-%m-%d')}_{x['GSTIN of Supplier']}", 
                axis=1
            )
            
            # Identify matching and non-matching records
            gstr2_keys = set(gstr2_df['match_key'])
            books_keys = set(books_df['match_key'])
            
            common_keys = gstr2_keys.intersection(books_keys)
            only_in_gstr2 = gstr2_keys - books_keys
            only_in_books = books_keys - gstr2_keys
            
            # Records found in both sources
            matches = []
            mismatches = []
            
            for key in common_keys:
                gstr2_record = gstr2_df[gstr2_df['match_key'] == key].iloc[0]
                books_record = books_df[books_df['match_key'] == key].iloc[0]
                
                # Check for value differences
                differences = {}
                has_differences = False
                
                for col in value_columns:
                    if col in gstr2_record and col in books_record:
                        gstr2_value = gstr2_record[col] if not pd.isna(gstr2_record[col]) else 0
                        books_value = books_record[col] if not pd.isna(books_record[col]) else 0
                        
                        abs_diff = abs(gstr2_value - books_value)
                        if abs_diff > self.amount_threshold:
                            percent_diff = abs_diff / max(abs(gstr2_value), abs(books_value), 1) * 100 if max(abs(gstr2_value), abs(books_value)) > 0 else 0
                            
                            if percent_diff > self.percentage_threshold * 100:
                                has_differences = True
                                differences[col] = {
                                    'gstr2': gstr2_value,
                                    'books': books_value,
                                    'difference': gstr2_value - books_value,
                                    'percentage': percent_diff
                                }
                
                if has_differences:
                    mismatch = {
                        'invoice_number': gstr2_record['Invoice Number'],
                        'invoice_date': gstr2_record['Invoice Date'],
                        'gstin': gstr2_record['GSTIN of Supplier'],
                        'supplier_name': gstr2_record['Trade/Legal Name'] if 'Trade/Legal Name' in gstr2_record else '',
                        'differences': differences,
                        'gstr_type': gstr2_record['GSTR_Type'] if 'GSTR_Type' in gstr2_record else '2B'
                    }
                    mismatches.append(mismatch)
                else:
                    match = {
                        'invoice_number': gstr2_record['Invoice Number'],
                        'invoice_date': gstr2_record['Invoice Date'],
                        'gstin': gstr2_record['GSTIN of Supplier'],
                        'supplier_name': gstr2_record['Trade/Legal Name'] if 'Trade/Legal Name' in gstr2_record else '',
                        'value': gstr2_record['Invoice Value'] if 'Invoice Value' in gstr2_record else None,
                        'gstr_type': gstr2_record['GSTR_Type'] if 'GSTR_Type' in gstr2_record else '2B'
                    }
                    matches.append(match)
            
            # Records only in GSTR-2A/2B
            missing_in_books = []
            for key in only_in_gstr2:
                record = gstr2_df[gstr2_df['match_key'] == key].iloc[0]
                missing = {
                    'invoice_number': record['Invoice Number'],
                    'invoice_date': record['Invoice Date'],
                    'gstin': record['GSTIN of Supplier'],
                    'supplier_name': record['Trade/Legal Name'] if 'Trade/Legal Name' in record else '',
                    'value': record['Invoice Value'] if 'Invoice Value' in record else None,
                    'gstr_type': record['GSTR_Type'] if 'GSTR_Type' in record else '2B'
                }
                missing_in_books.append(missing)
                
            # Records only in Books
            missing_in_gstr2 = []
            for key in only_in_books:
                record = books_df[books_df['match_key'] == key].iloc[0]
                missing = {
                    'invoice_number': record['Invoice Number'],
                    'invoice_date': record['Invoice Date'],
                    'gstin': record['GSTIN of Supplier'],
                    'supplier_name': record['Trade/Legal Name'] if 'Trade/Legal Name' in record else '',
                    'value': record['Invoice Value'] if 'Invoice Value' in record else None
                }
                missing_in_gstr2.append(missing)
            
            # Summary metrics
            total_gstr2_records = len(gstr2_df)
            total_books_records = len(books_df)
            match_count = len(matches)
            mismatch_count = len(mismatches)
            missing_in_books_count = len(missing_in_books)
            missing_in_gstr2_count = len(missing_in_gstr2)
            
            # Tax summary
            gstr2_tax_total = {
                'taxable_value': gstr2_df['Taxable Value'].sum() if 'Taxable Value' in gstr2_df else 0,
                'igst': gstr2_df['Integrated Tax'].sum() if 'Integrated Tax' in gstr2_df else 0,
                'cgst': gstr2_df['Central Tax'].sum() if 'Central Tax' in gstr2_df else 0,
                'sgst': gstr2_df['State/UT Tax'].sum() if 'State/UT Tax' in gstr2_df else 0,
                'cess': gstr2_df['Cess'].sum() if 'Cess' in gstr2_df else 0
            }
            
            books_tax_total = {
                'taxable_value': books_df['Taxable Value'].sum() if 'Taxable Value' in books_df else 0,
                'igst': books_df['Integrated Tax'].sum() if 'Integrated Tax' in books_df else 0,
                'cgst': books_df['Central Tax'].sum() if 'Central Tax' in books_df else 0,
                'sgst': books_df['State/UT Tax'].sum() if 'State/UT Tax' in books_df else 0,
                'cess': books_df['Cess'].sum() if 'Cess' in books_df else 0
            }
            
            tax_difference = {
                'taxable_value': gstr2_tax_total['taxable_value'] - books_tax_total['taxable_value'],
                'igst': gstr2_tax_total['igst'] - books_tax_total['igst'],
                'cgst': gstr2_tax_total['cgst'] - books_tax_total['cgst'],
                'sgst': gstr2_tax_total['sgst'] - books_tax_total['sgst'],
                'cess': gstr2_tax_total['cess'] - books_tax_total['cess']
            }
            
            # Check ITC eligibility
            itc_status = {
                'total_eligible_in_gstr2': 0,
                'total_eligible_in_books': 0,
                'difference': 0
            }
            
            if 'ITC Availability' in gstr2_df.columns:
                itc_status['total_eligible_in_gstr2'] = gstr2_df.loc[
                    gstr2_df['ITC Availability'].str.lower().str.contains('eligible', na=False), 
                    ['Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess']
                ].sum().sum()
            
            if 'ITC Eligible' in books_df.columns:
                itc_status['total_eligible_in_books'] = books_df.loc[
                    books_df['ITC Eligible'] == True, 
                    ['Integrated Tax', 'Central Tax', 'State/UT Tax', 'Cess']
                ].sum().sum()
            
            itc_status['difference'] = itc_status['total_eligible_in_gstr2'] - itc_status['total_eligible_in_books']
            
            # Results
            results = {
                'summary': {
                    'total_gstr2_records': total_gstr2_records,
                    'total_books_records': total_books_records,
                    'match_count': match_count,
                    'mismatch_count': mismatch_count,
                    'missing_in_books_count': missing_in_books_count,
                    'missing_in_gstr2_count': missing_in_gstr2_count
                },
                'tax_summary': {
                    'gstr2': gstr2_tax_total,
                    'books': books_tax_total,
                    'difference': tax_difference
                },
                'itc_status': itc_status,
                'matches': matches,
                'mismatches': mismatches,
                'missing_in_books': missing_in_books,
                'missing_in_gstr2': missing_in_gstr2
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error during reconciliation: {str(e)}")
    
    def process(self, gstr2_file, books_file, gstr_type="2B"):
        """
        Process GSTR-2A/2B and Books data for reconciliation
        
        Args:
            gstr2_file (str): Path to GSTR-2A/2B data file
            books_file (str): Path to Books (Purchase Register) data file
            gstr_type (str): Type of GSTR-2 file ('2A' or '2B')
            
        Returns:
            dict: Reconciliation results
        """
        # Load data from files
        gstr2_df, books_df = self.load_data(gstr2_file, books_file, gstr_type)
        
        # Map columns based on defined mappings
        gstr2_mapped_df, books_mapped_df = self.map_columns(gstr2_df, books_df)
        
        # Perform reconciliation
        results = self.reconcile(gstr2_mapped_df, books_mapped_df)
        
        return results