"""
Configuration settings for the GST Reconciliation System
"""

# Application settings
APP_NAME = "GST Reconciliation System"
APP_VERSION = "1.0.0"

# Default directories
DEFAULT_INPUT_DIR = "./input_files"
DEFAULT_OUTPUT_DIR = "./output_files"
DEFAULT_TEMPLATE_DIR = "./resources/templates"

# Column mappings for each reconciliation type
# These mappings define the columns to compare between different sources

# 1. GSTR-1 vs Books (Sales Register)
GSTR1_BOOKS_MAPPING = {
    "GSTIN/UIN of Recipient": "Customer GSTIN",
    "Receiver Name": "Customer Name",
    "Invoice Number": "Invoice No.",
    "Invoice Date": "Invoice Date",
    "Invoice Value": "Invoice Value",
    "Place of Supply": "State/Code",
    "Reverse Charge": "RCM Applicable",
    "Applicable % of Tax Rate": "Tax Rate",
    "Taxable Value": "Taxable Value",
    "Integrated Tax": "IGST",
    "Central Tax": "CGST",
    "State/UT Tax": "SGST/UTGST",
    "Cess": "Cess",
    "E-Commerce GSTIN": "E-Commerce GSTIN",
    "Rate": "Rate",
    "Supply Type": "Supply Type"
}

# 2. GSTR-2A/2B vs Books (Purchase Register)
GSTR2_BOOKS_MAPPING = {
    "GSTIN of Supplier": "Vendor GSTIN",
    "Trade/Legal Name": "Vendor Name",
    "Invoice Number": "Purchase Invoice No.",
    "Invoice Date": "Invoice Date",
    "Invoice Value": "Invoice Value",
    "Place of Supply": "State/Code",
    "Reverse Charge": "RCM Applicable",
    "Invoice Type": "Invoice Type",
    "Rate": "Rate",
    "Taxable Value": "Taxable Value",
    "Integrated Tax": "IGST",
    "Central Tax": "CGST",
    "State/UT Tax": "SGST/UTGST",
    "Cess": "Cess",
    "ITC Availability": "ITC Eligible",
    "Reason": "Ineligibility Reason"
}

# 3. GSTR-3B vs GSTR-1
GSTR3B_GSTR1_MAPPING = {
    "Table 3.1(a)": ["Table 4", "Table 5", "Table 6", "Table 7", "Table 8", "Table 9", "Table 10", "Table 11", "Table 12"],
    "Table 3.1(b)": ["Table 6: Zero rated supplies"],
    "Table 3.1(c)": ["Nil rated, exempted supplies"],
    "Table 3.1(d)": [],  # Not in GSTR-1
    "Table 3.1(e)": []   # Not in GSTR-1
}

# 4. GSTR-3B vs Books (Output Tax)
GSTR3B_BOOKS_MAPPING = {
    "Table 3.1": "Output Tax Ledger",
    "Table 3.1(a)": "Regular Supplies Output Tax",
    "Table 3.1(b)": "Zero-Rated Supplies",
    "Table 3.1(c)": "Exempt Supplies",
    "Table 3.1(d)": "RCM Output Tax",
    "Table 3.1(e)": "Non-GST Supplies",
    "Integrated Tax Amount": "IGST Output",
    "Central Tax Amount": "CGST Output",
    "State/UT Tax Amount": "SGST/UTGST Output",
    "Cess Amount": "Cess Output"
}

# 5. ITC in GSTR-3B vs GSTR-2B
ITC_GSTR3B_GSTR2B_MAPPING = {
    "Table 4(A)(1)": [],  # Not directly in GSTR-2B
    "Table 4(A)(2)": [],  # Not directly in GSTR-2B
    "Table 4(A)(3)": "ITC Available - Reverse Charge",
    "Table 4(A)(4)": "ITC From ISD",
    "Table 4(A)(5)": "ITC Available",
    "Table 4(B)(1)": [],  # Not in GSTR-2B
    "Table 4(B)(2)": [],  # Not in GSTR-2B
    "Table 4(C)": "Net ITC Available",
    "Table 4(D)": "Ineligible ITC"
}

# 6. ITC in Books vs Eligible ITC (Section 16 & 17)
ITC_BOOKS_ELIGIBILITY_MAPPING = {
    "Total ITC": "Gross ITC",
    "Eligible ITC": "Eligible ITC as per Sec 16",
    "Ineligible ITC": "Ineligible ITC as per Sec 17",
    "ITC Reversed": "ITC Reversal",
    "Net ITC": "Net Eligible ITC",
    "ITC on Capital Goods": "ITC - Capital Goods",
    "ITC on Input Services": "ITC - Input Services",
    "ITC on Inputs": "ITC - Inputs"
}

# 7. GSTR-1 vs E-Way Bills
GSTR1_EWAY_MAPPING = {
    "Invoice Number": "Document No.",
    "Invoice Date": "Document Date",
    "Invoice Value": "Total Invoice Value",
    "GSTIN/UIN of Recipient": "Recipient GSTIN",
    "Receiver Name": "Recipient Name",
    "Place of Supply": "Place of Delivery",
    "HSN Code": "HSN Code",
    "Taxable Value": "Taxable Amount",
    "Tax Rate": "Tax Rate",
    "E-Way Bill Number": "E-Way Bill No.",
    "E-Way Bill Date": "E-Way Bill Date"
}

# 8. GSTR-2A/2B vs E-Way Bills
GSTR2_EWAY_MAPPING = {
    "GSTIN of Supplier": "Supplier GSTIN",
    "Trade/Legal Name": "Supplier Name",
    "Invoice Number": "Document No.",
    "Invoice Date": "Document Date",
    "Invoice Value": "Total Invoice Value",
    "Place of Supply": "Place of Delivery",
    "HSN Code": "HSN Code",
    "Taxable Value": "Taxable Amount",
    "Tax Rate": "Tax Rate",
    "E-Way Bill Number": "E-Way Bill No.",
    "E-Way Bill Date": "E-Way Bill Date"
}

# 9. GSTR-1 vs E-invoice
GSTR1_EINVOICE_MAPPING = {
    "Invoice Number": "Document No.",
    "Invoice Date": "Document Date",
    "Invoice Value": "Total Invoice Value",
    "GSTIN/UIN of Recipient": "Recipient GSTIN",
    "Receiver Name": "Recipient Legal Name",
    "Place of Supply": "Place of Supply",
    "HSN Code": "HSN Code",
    "Taxable Value": "Taxable Value",
    "Tax Rate": "Rate",
    "Integrated Tax": "IGST Amount",
    "Central Tax": "CGST Amount",
    "State/UT Tax": "SGST/UTGST Amount",
    "IRN Number": "IRN",
    "IRN Date": "IRN Date",
    "Acknowledgement Number": "Ack No.",
    "Acknowledgement Date": "Ack Date"
}

# 10. Turnover as per Books vs GST Returns vs Financial Statements
TURNOVER_MAPPING = {
    "Total Sales": ["Annual Aggregate Turnover", "Revenue from Operations"],
    "Taxable Turnover": ["Taxable Turnover", "Taxable Revenue"],
    "Exempt Turnover": ["Exempt Turnover", "Exempt Revenue"],
    "Export Turnover": ["Zero-rated Turnover", "Export Revenue"],
    "Non-GST Turnover": ["Non-GST Turnover", "Non-GST Revenue"],
    "Sales Returns": ["Credit Notes", "Sales Returns/Adjustments"],
    "Advances Received": ["Advances for which GST is paid", "Advances from Customers"],
    "Other Income": [None, "Other Income"]
}

# Threshold limits for highlighting discrepancies
AMOUNT_THRESHOLD = 1.0  # Rs. 1 difference is allowed
PERCENTAGE_THRESHOLD = 0.01  # 1% difference is allowed