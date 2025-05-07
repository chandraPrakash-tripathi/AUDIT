#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
GSTR-3B vs GSTR-1 Reconciliation Module

This module provides functionality to reconcile data between GSTR-3B and GSTR-1 returns.
It compares the outward supplies reported in GSTR-3B with the corresponding sections in GSTR-1.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
import logging

from utils.excel_handler import read_excel_file, write_excel_file

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_dataframe(df):
    # Placeholder function for cleaning dataframe; implement as needed
    return df

def format_date_columns(df):
    # Placeholder function for formatting date columns; implement as needed
    return df

class GSTR3BGSTR1Reconciliation:
    """
    Class to handle reconciliation between GSTR-3B and GSTR-1 returns.
    """
    
    def __init__(self, gstr3b_file=None, gstr1_file=None, output_dir=None):
        """
        Initialize reconciliation with file paths.
        
        Args:
            gstr3b_file (str): Path to GSTR-3B Excel file
            gstr1_file (str): Path to GSTR-1 Excel file
            output_dir (str): Directory to save output files
        """
        from config import DEFAULT_OUTPUT_DIR, GSTR3B_GSTR1_MAPPING, AMOUNT_THRESHOLD, PERCENTAGE_THRESHOLD
        
        self.gstr3b_file = gstr3b_file
        self.gstr1_file = gstr1_file
        self.output_dir = output_dir or DEFAULT_OUTPUT_DIR
        self.mapping = GSTR3B_GSTR1_MAPPING
        self.amount_threshold = AMOUNT_THRESHOLD
        self.percentage_threshold = PERCENTAGE_THRESHOLD
        
        # Data structures to hold the reconciliation results
        self.gstr3b_data = None
        self.gstr1_data = None
        self.summary_data = None
        self.detailed_comparison = None
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
    def load_data(self):
        """
        Load data from GSTR-3B and GSTR-1 files.
        """
        if not self.gstr3b_file or not self.gstr1_file:
            raise ValueError("Both GSTR-3B and GSTR-1 file paths must be provided.")
            
        try:
            logger.info(f"Reading GSTR-3B data from {self.gstr3b_file}")
            self.gstr3b_data = read_excel_file(self.gstr3b_file)
            
            logger.info(f"Reading GSTR-1 data from {self.gstr1_file}")
            self.gstr1_data = read_excel_file(self.gstr1_file)
            
            # Clean and standardize data
            self.gstr3b_data = clean_dataframe(self.gstr3b_data)
            self.gstr1_data = clean_dataframe(self.gstr1_data)
            
            # Format date columns if any
            self.gstr3b_data = format_date_columns(self.gstr3b_data)
            self.gstr1_data = format_date_columns(self.gstr1_data)
            
            logger.info("Data loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
            
    def extract_gstr3b_table_values(self):
        """
        Extract values from GSTR-3B for comparison.
        
        Returns:
            dict: Dictionary with GSTR-3B table values
        """
        gstr3b_values = {
            "Table 3.1(a)": self._extract_value_from_gstr3b("Table 3.1(a)"),
            "Table 3.1(b)": self._extract_value_from_gstr3b("Table 3.1(b)"),
            "Table 3.1(c)": self._extract_value_from_gstr3b("Table 3.1(c)"),
            "Table 3.1(d)": self._extract_value_from_gstr3b("Table 3.1(d)"),
            "Table 3.1(e)": self._extract_value_from_gstr3b("Table 3.1(e)"),
            "Table 3.2": self._extract_value_from_gstr3b("Table 3.2")
        }
        
        # Add tax amount fields
        tax_fields = ["Integrated Tax Amount", "Central Tax Amount", "State/UT Tax Amount", "Cess Amount"]
        for field in tax_fields:
            gstr3b_values[field] = self._extract_value_from_gstr3b(field)
            
        return gstr3b_values
        
    def _extract_value_from_gstr3b(self, field_name):
        """
        Helper method to extract values from GSTR-3B dataframe.
        
        Args:
            field_name (str): Field name to extract
            
        Returns:
            float: Extracted value or 0.0 if not found
        """
        try:
            # This implementation depends on the actual structure of the GSTR-3B data
            # For demonstration, we assume a structure where field_name is in one column
            # and its value in another
            if 'Field' in self.gstr3b_data.columns and 'Value' in self.gstr3b_data.columns:
                matched_row = self.gstr3b_data[self.gstr3b_data['Field'] == field_name]
                if not matched_row.empty:
                    return float(matched_row['Value'].iloc[0])
            
            # Alternative approach if the above doesn't match the data structure
            if field_name in self.gstr3b_data.columns:
                return float(self.gstr3b_data[field_name].sum())
                
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting {field_name} from GSTR-3B: {str(e)}")
            return 0.0
            
    def extract_gstr1_table_values(self):
        """
        Extract values from GSTR-1 sections for comparison.
        
        Returns:
            dict: Dictionary with GSTR-1 table values
        """
        gstr1_values = {}
        
        # Process each mapping to aggregate values from GSTR-1
        for gstr3b_table, gstr1_tables in self.mapping.items():
            if not gstr1_tables:  # Skip if no mapping exists
                continue
                
            total_value = 0.0
            for gstr1_table in gstr1_tables:
                value = self._extract_value_from_gstr1(gstr1_table)
                total_value += value
                
            gstr1_values[gstr3b_table] = total_value
            
        return gstr1_values
    
    def _extract_value_from_gstr1(self, table_name):
        """
        Helper method to extract values from GSTR-1 dataframe.
        
        Args:
            table_name (str): Table name to extract from GSTR-1
            
        Returns:
            float: Extracted value or 0.0 if not found
        """
        try:
            # This implementation depends on the actual structure of the GSTR-1 data
            # For demonstration, we assume a structure with sheet names or columns
            # corresponding to the table names
            
            # Case 1: If the table_name is a sheet in the Excel file
            if table_name in self.gstr1_data:
                sheet_data = self.gstr1_data[table_name]
                # Assuming taxable value column exists
                if 'Taxable Value' in sheet_data.columns:
                    return float(sheet_data['Taxable Value'].sum())
                    
            # Case 2: If table_name is a column indicating the section
            if 'Section' in self.gstr1_data.columns and 'Taxable Value' in self.gstr1_data.columns:
                matched_rows = self.gstr1_data[self.gstr1_data['Section'] == table_name]
                if not matched_rows.empty:
                    return float(matched_rows['Taxable Value'].sum())
                    
            # Case 3: If there's a column with the specific table name
            if table_name in self.gstr1_data.columns:
                return float(self.gstr1_data[table_name].sum())
                
            # If it's a description like "Nil rated, exempted supplies"
            if 'Description' in self.gstr1_data.columns and 'Value' in self.gstr1_data.columns:
                matched_rows = self.gstr1_data[self.gstr1_data['Description'].str.contains(table_name, na=False)]
                if not matched_rows.empty:
                    return float(matched_rows['Value'].sum())
                    
            return 0.0
        except Exception as e:
            logger.warning(f"Error extracting {table_name} from GSTR-1: {str(e)}")
            return 0.0
    
    def compare_returns(self):
        """
        Compare GSTR-3B and GSTR-1 values and identify discrepancies.
        
        Returns:
            pandas.DataFrame: DataFrame containing comparison results
        """
        gstr3b_values = self.extract_gstr3b_table_values()
        gstr1_values = self.extract_gstr1_table_values()
        
        comparison_data = []
        
        # Prepare the mapping for comparison
        comparison_mapping = {
            "Table 3.1(a)": "Table 3.1(a) - Taxable supplies",
            "Table 3.1(b)": "Table 3.1(b) - Zero-rated supplies",
            "Table 3.1(c)": "Table 3.1(c) - Nil rated, exempted supplies",
            "Table 3.1(d)": "Table 3.1(d) - Inward supplies (RCM)",
            "Table 3.1(e)": "Table 3.1(e) - Non-GST outward supplies",
            "Table 3.2": "Table 3.2 - Tax rates"
        }
        
        # Compare each table/section
        for gstr3b_key, description in comparison_mapping.items():
            gstr3b_value = gstr3b_values.get(gstr3b_key, 0.0)
            gstr1_value = gstr1_values.get(gstr3b_key, 0.0)
            
            # Calculate difference
            diff = gstr3b_value - gstr1_value
            
            # Calculate percentage difference to avoid division by zero
            if gstr3b_value != 0 or gstr1_value != 0:
                base_value = max(abs(gstr3b_value), abs(gstr1_value))
                percentage_diff = (diff / base_value) * 100 if base_value > 0 else 0.0
            else:
                percentage_diff = 0.0
                
            # Check if the difference is significant based on thresholds
            is_significant = (abs(diff) > self.amount_threshold and 
                             abs(percentage_diff) > (self.percentage_threshold * 100))
            
            comparison_data.append({
                "GSTR-3B Table/Field": gstr3b_key,
                "Description": description,
                "GSTR-3B Value": gstr3b_value,
                "GSTR-1 Value": gstr1_value,
                "Difference": diff,
                "% Difference": percentage_diff,
                "Is Significant": is_significant,
                "Remarks": "Discrepancy needs attention" if is_significant else "Within acceptable limits"
            })
        
        # Create a DataFrame from the comparison data
        self.detailed_comparison = pd.DataFrame(comparison_data)
        
        # Create a summary
        self.create_summary()
        
        return self.detailed_comparison
        
    def create_summary(self):
        """
        Create a summary of the reconciliation results.
        
        Returns:
            pandas.DataFrame: Summary DataFrame
        """
        if self.detailed_comparison is None:
            logger.warning("Cannot create summary without comparison data")
            return None
            
        total_gstr3b = self.detailed_comparison["GSTR-3B Value"].sum()
        total_gstr1 = self.detailed_comparison["GSTR-1 Value"].sum()
        total_diff = total_gstr3b - total_gstr1
        
        if total_gstr3b != 0 or total_gstr1 != 0:
            base_value = max(abs(total_gstr3b), abs(total_gstr1))
            total_percentage_diff = (total_diff / base_value) * 100 if base_value > 0 else 0.0
        else:
            total_percentage_diff = 0.0
            
        significant_issues = len(self.detailed_comparison[self.detailed_comparison["Is Significant"] == True])
        
        self.summary_data = pd.DataFrame([{
            "Total GSTR-3B Value": total_gstr3b,
            "Total GSTR-1 Value": total_gstr1,
            "Total Difference": total_diff,
            "Total % Difference": total_percentage_diff,
            "Number of Significant Discrepancies": significant_issues,
            "Reconciliation Status": "Needs Review" if significant_issues > 0 else "Reconciled"
        }])
        
        return self.summary_data
        
    def generate_report(self, report_name=None):
        """
        Generate reconciliation report and save to Excel.
        
        Args:
            report_name (str, optional): Name for the report file. If None, a default name is used.
            
        Returns:
            str: Path to the generated report
        """
        if self.detailed_comparison is None:
            logger.error("No comparison data available for report generation")
            return None
            
        if report_name is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"GSTR3B_GSTR1_Reconciliation_{timestamp}.xlsx"
            
        report_path = os.path.join(self.output_dir, report_name)
        
        try:
            # Create a writer object
            with pd.ExcelWriter(report_path, engine='xlsxwriter') as writer:
                # Write summary to the first sheet
                if self.summary_data is not None:
                    self.summary_data.to_excel(writer, sheet_name="Summary", index=False)
                    
                    # Format the summary sheet
                    workbook = writer.book
                    summary_sheet = writer.sheets["Summary"]
                    
                    # Add formats
                    header_format = workbook.add_format({
                        'bold': True, 
                        'text_wrap': True, 
                        'valign': 'top',
                        'fg_color': '#D7E4BC', 
                        'border': 1
                    })
                    
                    # Apply formats to the header row
                    for col_num, value in enumerate(self.summary_data.columns.values):
                        summary_sheet.write(0, col_num, value, header_format)
                    
                    # Adjust column widths
                    for i, col in enumerate(self.summary_data.columns):
                        max_len = max(
                            self.summary_data[col].astype(str).map(len).max(),
                            len(str(col))
                        ) + 2
                        summary_sheet.set_column(i, i, max_len)
                
                # Write detailed comparison to the second sheet
                self.detailed_comparison.to_excel(writer, sheet_name="Detailed Comparison", index=False)
                
                # Format the detailed comparison sheet
                detailed_sheet = writer.sheets["Detailed Comparison"]
                
                # Add formats
                header_format = workbook.add_format({
                    'bold': True, 
                    'text_wrap': True, 
                    'valign': 'top',
                    'fg_color': '#D7E4BC', 
                    'border': 1
                })
                
                significant_format = workbook.add_format({
                    'bg_color': '#FFC7CE',
                    'font_color': '#9C0006'
                })
                
                # Apply formats to the header row
                for col_num, value in enumerate(self.detailed_comparison.columns.values):
                    detailed_sheet.write(0, col_num, value, header_format)
                
                # Highlight significant discrepancies
                for row_num in range(1, len(self.detailed_comparison) + 1):
                    if self.detailed_comparison.iloc[row_num-1]["Is Significant"]:
                        detailed_sheet.set_row(row_num, None, significant_format)
                
                # Adjust column widths
                for i, col in enumerate(self.detailed_comparison.columns):
                    max_len = max(
                        self.detailed_comparison[col].astype(str).map(len).max(),
                        len(str(col))
                    ) + 2
                    detailed_sheet.set_column(i, i, max_len)
            
            logger.info(f"Report generated successfully at {report_path}")
            return report_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return None
    
    def reconcile(self):
        """
        Execute the full reconciliation process.
        
        Returns:
            tuple: (success status, path to report if successful)
        """
        try:
            # Load data
            if not self.load_data():
                return False, "Failed to load data"
                
            # Compare returns
            self.compare_returns()
            
            # Generate report
            report_path = self.generate_report()
            
            if report_path:
                return True, report_path
            else:
                return False, "Failed to generate report"
                
        except Exception as e:
            logger.error(f"Reconciliation failed: {str(e)}")
            return False, str(e)


def run_reconciliation(gstr3b_file, gstr1_file, output_dir=None):
    """
    Run the GSTR-3B vs GSTR-1 reconciliation process.
    
    Args:
        gstr3b_file (str): Path to GSTR-3B file
        gstr1_file (str): Path to GSTR-1 file
        output_dir (str, optional): Output directory for reports
        
    Returns:
        tuple: (success status, message or report path)
    """
    reconciler = GSTR3BGSTR1Reconciliation(gstr3b_file, gstr1_file, output_dir)
    return reconciler.reconcile()


if __name__ == "__main__":
    # Example usage when run directly
    import argparse
    
    parser = argparse.ArgumentParser(description="Reconcile GSTR-3B and GSTR-1 returns.")
    parser.add_argument("--gstr3b", required=True, help="Path to GSTR-3B Excel file")
    parser.add_argument("--gstr1", required=True, help="Path to GSTR-1 Excel file")
    parser.add_argument("--output", help="Directory to save output files")
    
    args = parser.parse_args()
    
    success, result = run_reconciliation(args.gstr3b, args.gstr1, args.output)
    
    if success:
        print(f"Reconciliation completed successfully. Report saved at: {result}")
    else:
        print(f"Reconciliation failed: {result}")