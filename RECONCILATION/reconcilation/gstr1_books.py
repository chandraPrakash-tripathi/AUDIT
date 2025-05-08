"""
GSTR-1 vs Books (Sales Register) Reconciliation Module
"""
import pandas as pd
import numpy as np
from config import GSTR1_BOOKS_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD

def standardize_columns(df):
    df.columns = df.columns.str.strip()
    return df

def format_date_columns(df, columns):
    for col in columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    return df

def clean_numeric_data(df, numeric_cols):
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

class GSTR1BooksReconciliation:
    """Class to handle reconciliation between GSTR-1 and Books (Sales Register)"""
    
    def __init__(self):
        """Initialize the reconciliation module"""
        self.mapping = GSTR1_BOOKS_MAPPING
        self.amount_threshold = AMOUNT_THRESHOLD
        self.percentage_threshold = PERCENTAGE_THRESHOLD
        
    def load_data(self, gstr1_file, books_file):
        """
        Load GSTR-1 and Books data from files
        
        Args:
            gstr1_file (str): Path to GSTR-1 data file
            books_file (str): Path to Books (Sales Register) data file
            
        Returns:
            tuple: Dataframes containing GSTR-1 and Books data
        """
        try:
            # Load GSTR-1 data
            gstr1_df = pd.read_excel(gstr1_file)
            
            # Load Books (Sales Register) data
            books_df = pd.read_excel(books_file)
            
            # Standardize column names
            gstr1_df = standardize_columns(gstr1_df)
            books_df = standardize_columns(books_df)
            
            # Format date columns
            gstr1_df = format_date_columns(gstr1_df, ["Invoice Date"])
            books_df = format_date_columns(books_df, ["Invoice Date"])
            
            # Clean numeric data
            numeric_cols = ["Invoice Value", "Taxable Value", "Integrated Tax", 
                           "Central Tax", "State/UT Tax", "Cess", "Rate"]
            gstr1_df = clean_numeric_data(gstr1_df, numeric_cols)
            books_df = clean_numeric_data(books_df, numeric_cols)
            
            return gstr1_df, books_df
            
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")
    
    def map_columns(self, gstr1_df, books_df):
        """
        Map columns from GSTR-1 and Books data based on defined mappings
        
        Args:
            gstr1_df (DataFrame): GSTR-1 data
            books_df (DataFrame): Books data
            
        Returns:
            tuple: Dataframes with mapped columns
        """
        # Create mapping dictionaries
        gstr1_cols = list(self.mapping.keys())
        books_cols = list(self.mapping.values())
        
        # Filter and rename columns
        try:
            # Select required columns from GSTR-1 data (if they exist)
            gstr1_available_cols = [col for col in gstr1_cols if col in gstr1_df.columns]
            gstr1_mapped_df = gstr1_df[gstr1_available_cols].copy()
            
            # Select required columns from Books data (if they exist)
            books_available_cols = [col for col in books_cols if col in books_df.columns]
            books_mapped_df = books_df[books_available_cols].copy()
            
            # Create reverse mapping for renaming Books columns to match GSTR-1
            reverse_mapping = {v: k for k, v in self.mapping.items()}
            books_mapped_df = books_mapped_df.rename(columns=reverse_mapping)
            
            return gstr1_mapped_df, books_mapped_df
            
        except Exception as e:
            raise Exception(f"Error mapping columns: {str(e)}")
    
    def reconcile(self, gstr1_df, books_df):
        """
        Reconcile GSTR-1 data with Books data
        
        Args:
            gstr1_df (DataFrame): GSTR-1 data with mapped columns
            books_df (DataFrame): Books data with mapped columns
            
        Returns:
            dict: Reconciliation results with matches, mismatches, missing entries
        """
        try:
            # Identify key columns for matching
            key_columns = ["Invoice Number", "Invoice Date", "GSTIN/UIN of Recipient"]
            value_columns = ["Invoice Value", "Taxable Value", "Integrated Tax", 
                            "Central Tax", "State/UT Tax", "Cess"]
            
            # Create key for matching
            gstr1_df['match_key'] = gstr1_df.apply(
                lambda x: f"{x['Invoice Number']}_{x['Invoice Date'].strftime('%Y-%m-%d')}_{x['GSTIN/UIN of Recipient']}", 
                axis=1
            )
            
            books_df['match_key'] = books_df.apply(
                lambda x: f"{x['Invoice Number']}_{x['Invoice Date'].strftime('%Y-%m-%d')}_{x['GSTIN/UIN of Recipient']}", 
                axis=1
            )
            
            # Identify matching and non-matching records
            gstr1_keys = set(gstr1_df['match_key'])
            books_keys = set(books_df['match_key'])
            
            common_keys = gstr1_keys.intersection(books_keys)
            only_in_gstr1 = gstr1_keys - books_keys
            only_in_books = books_keys - gstr1_keys
            
            # Records found in both sources
            matches = []
            mismatches = []
            
            for key in common_keys:
                gstr1_record = gstr1_df[gstr1_df['match_key'] == key].iloc[0]
                books_record = books_df[books_df['match_key'] == key].iloc[0]
                
                # Check for value differences
                differences = {}
                has_differences = False
                
                for col in value_columns:
                    if col in gstr1_record and col in books_record:
                        gstr1_value = gstr1_record[col] if not pd.isna(gstr1_record[col]) else 0
                        books_value = books_record[col] if not pd.isna(books_record[col]) else 0
                        
                        abs_diff = abs(gstr1_value - books_value)
                        if abs_diff > self.amount_threshold:
                            percent_diff = abs_diff / max(abs(gstr1_value), abs(books_value), 1) * 100 if max(abs(gstr1_value), abs(books_value)) > 0 else 0
                            
                            if percent_diff > self.percentage_threshold * 100:
                                has_differences = True
                                differences[col] = {
                                    'gstr1': gstr1_value,
                                    'books': books_value,
                                    'difference': gstr1_value - books_value,
                                    'percentage': percent_diff
                                }
                
                if has_differences:
                    mismatch = {
                        'invoice_number': gstr1_record['Invoice Number'],
                        'invoice_date': gstr1_record['Invoice Date'],
                        'gstin': gstr1_record['GSTIN/UIN of Recipient'],
                        'differences': differences
                    }
                    mismatches.append(mismatch)
                else:
                    match = {
                        'invoice_number': gstr1_record['Invoice Number'],
                        'invoice_date': gstr1_record['Invoice Date'],
                        'gstin': gstr1_record['GSTIN/UIN of Recipient'],
                        'value': gstr1_record['Invoice Value'] if 'Invoice Value' in gstr1_record else None
                    }
                    matches.append(match)
            
            # Records only in GSTR-1
            missing_in_books = []
            for key in only_in_gstr1:
                record = gstr1_df[gstr1_df['match_key'] == key].iloc[0]
                missing = {
                    'invoice_number': record['Invoice Number'],
                    'invoice_date': record['Invoice Date'],
                    'gstin': record['GSTIN/UIN of Recipient'],
                    'value': record['Invoice Value'] if 'Invoice Value' in record else None
                }
                missing_in_books.append(missing)
                
            # Records only in Books
            missing_in_gstr1 = []
            for key in only_in_books:
                record = books_df[books_df['match_key'] == key].iloc[0]
                missing = {
                    'invoice_number': record['Invoice Number'],
                    'invoice_date': record['Invoice Date'],
                    'gstin': record['GSTIN/UIN of Recipient'],
                    'value': record['Invoice Value'] if 'Invoice Value' in record else None
                }
                missing_in_gstr1.append(missing)
            
            # Summary metrics
            total_gstr1_records = len(gstr1_df)
            total_books_records = len(books_df)
            match_count = len(matches)
            mismatch_count = len(mismatches)
            missing_in_books_count = len(missing_in_books)
            missing_in_gstr1_count = len(missing_in_gstr1)
            
            # Tax summary
            gstr1_tax_total = {
                'taxable_value': gstr1_df['Taxable Value'].sum() if 'Taxable Value' in gstr1_df else 0,
                'igst': gstr1_df['Integrated Tax'].sum() if 'Integrated Tax' in gstr1_df else 0,
                'cgst': gstr1_df['Central Tax'].sum() if 'Central Tax' in gstr1_df else 0,
                'sgst': gstr1_df['State/UT Tax'].sum() if 'State/UT Tax' in gstr1_df else 0,
                'cess': gstr1_df['Cess'].sum() if 'Cess' in gstr1_df else 0
            }
            
            books_tax_total = {
                'taxable_value': books_df['Taxable Value'].sum() if 'Taxable Value' in books_df else 0,
                'igst': books_df['Integrated Tax'].sum() if 'Integrated Tax' in books_df else 0,
                'cgst': books_df['Central Tax'].sum() if 'Central Tax' in books_df else 0,
                'sgst': books_df['State/UT Tax'].sum() if 'State/UT Tax' in books_df else 0,
                'cess': books_df['Cess'].sum() if 'Cess' in books_df else 0
            }
            
            tax_difference = {
                'taxable_value': gstr1_tax_total['taxable_value'] - books_tax_total['taxable_value'],
                'igst': gstr1_tax_total['igst'] - books_tax_total['igst'],
                'cgst': gstr1_tax_total['cgst'] - books_tax_total['cgst'],
                'sgst': gstr1_tax_total['sgst'] - books_tax_total['sgst'],
                'cess': gstr1_tax_total['cess'] - books_tax_total['cess']
            }
            
            # Results
            results = {
                'summary': {
                    'total_gstr1_records': total_gstr1_records,
                    'total_books_records': total_books_records,
                    'match_count': match_count,
                    'mismatch_count': mismatch_count,
                    'missing_in_books_count': missing_in_books_count,
                    'missing_in_gstr1_count': missing_in_gstr1_count
                },
                'tax_summary': {
                    'gstr1': gstr1_tax_total,
                    'books': books_tax_total,
                    'difference': tax_difference
                },
                'matches': matches,
                'mismatches': mismatches,
                'missing_in_books': missing_in_books,
                'missing_in_gstr1': missing_in_gstr1
            }
            
            return results
            
        except Exception as e:
            raise Exception(f"Error during reconciliation: {str(e)}")
    
    def process(self, gstr1_file, books_file):
        """
        Process GSTR-1 and Books data for reconciliation
        
        Args:
            gstr1_file (str): Path to GSTR-1 data file
            books_file (str): Path to Books (Sales Register) data file
            
        Returns:
            dict: Reconciliation results
        """
        # Load data from files
        gstr1_df, books_df = self.load_data(gstr1_file, books_file)
        
        # Map columns based on defined mappings
        gstr1_mapped_df, books_mapped_df = self.map_columns(gstr1_df, books_df)
        
        # Perform reconciliation
        results = self.reconcile(gstr1_mapped_df, books_mapped_df)
        
        return results