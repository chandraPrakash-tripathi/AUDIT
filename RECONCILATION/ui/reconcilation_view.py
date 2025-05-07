"""
Reconciliation view for GST Reconciliation System
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from utils.excel_handler import load_excel_file, save_excel_file
from utils.data_processor import process_reconciliation
from utils.report_generator import generate_reconciliation_report

class ReconciliationView(ttk.Frame):
    """View for performing and displaying reconciliation"""
    
    def __init__(self, master=None, recon_type=None):
        super().__init__(master)
        self.master = master
        self.recon_type = recon_type
        
        # Initialize instance variables
        self.source1_file = None
        self.source2_file = None
        self.source3_file = None  # Optional for some reconciliations
        self.result_df = None
        self.reconciliation_complete = False
        
        # Get reconciliation details
        self.recon_details = self.get_reconciliation_details()
        
        # Create UI components
        self.create_widgets()
    
    def get_reconciliation_details(self):
        """Get details for the selected reconciliation type"""
        details = {
            "gstr1_books": {
                "title": "GSTR-1 vs Books (Sales Register)",
                "source1_label": "GSTR-1 File:",
                "source2_label": "Sales Register:",
                "source3_required": False,
                "mapping": config.GSTR1_BOOKS_MAPPING
            },
            "gstr2_books": {
                "title": "GSTR-2A/2B vs Books (Purchase Register)",
                "source1_label": "GSTR-2A/2B File:",
                "source2_label": "Purchase Register:",
                "source3_required": False,
                "mapping": config.GSTR2_BOOKS_MAPPING
            },
            "gstr3b_gstr1": {
                "title": "GSTR-3B vs GSTR-1",
                "source1_label": "GSTR-3B File:",
                "source2_label": "GSTR-1 File:",
                "source3_required": False,
                "mapping": config.GSTR3B_GSTR1_MAPPING
            },
            "gstr3b_books": {
                "title": "GSTR-3B vs Books (Output Tax)",
                "source1_label": "GSTR-3B File:",
                "source2_label": "Output Tax Register:",
                "source3_required": False,
                "mapping": config.GSTR3B_BOOKS_MAPPING
            },
            "itc_gstr3b_gstr2b": {
                "title": "ITC in GSTR-3B vs GSTR-2B",
                "source1_label": "GSTR-3B File:",
                "source2_label": "GSTR-2B File:",
                "source3_required": False,
                "mapping": config.ITC_GSTR3B_GSTR2B_MAPPING
            },
            "itc_eligibility": {
                "title": "ITC in Books vs Eligible ITC",
                "source1_label": "Books ITC Register:",
                "source2_label": "ITC Eligibility Register:",
                "source3_required": False,
                "mapping": config.ITC_BOOKS_ELIGIBILITY_MAPPING
            },
            "gstr1_eway": {
                "title": "GSTR-1 vs E-Way Bills",
                "source1_label": "GSTR-1 File:",
                "source2_label": "E-Way Bills File:",
                "source3_required": False,
                "mapping": config.GSTR1_EWAY_MAPPING
            },
            "gstr2_eway": {
                "title": "GSTR-2A/2B vs E-Way Bills",
                "source1_label": "GSTR-2A/2B File:",
                "source2_label": "E-Way Bills File:",
                "source3_required": False,
                "mapping": config.GSTR2_EWAY_MAPPING
            },
            "gstr1_einvoice": {
                "title": "GSTR-1 vs E-invoice",
                "source1_label": "GSTR-1 File:",
                "source2_label": "E-invoice File:",
                "source3_required": False,
                "mapping": config.GSTR1_EINVOICE_MAPPING
            },
            "turnover_recon": {
                "title": "Turnover Reconciliation",
                "source1_label": "Books File:",
                "source2_label": "GST Returns File:",
                "source3_label": "Financial Statements File:",
                "source3_required": True,
                "mapping": config.TURNOVER_MAPPING
            }
        }
        
        return details.get(self.recon_type, {"title": "Unknown Reconciliation"})
    
    def create_widgets(self):
        """Create view widgets"""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=20, padx=20, fill=tk.X)
        
        title_label = ttk.Label(header_frame, 
                              text=self.recon_details.get("title", "Reconciliation"),
                              font=("Arial", 16, "bold"))
        title_label.pack(anchor="w")
        
        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # Input section
        input_frame = ttk.LabelFrame(self, text="Input Files")
        input_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Source 1 selection
        source1_frame = ttk.Frame(input_frame)
        source1_frame.pack(padx=10, pady=5, fill=tk.X)
        
        source1_label = ttk.Label(source1_frame, 
                                 text=self.recon_details.get("source1_label", "Source 1:"),
                                 width=20)
        source1_label.pack(side=tk.LEFT)
        
        self.source1_entry = ttk.Entry(source1_frame, width=50)
        self.source1_entry.pack(side=tk.LEFT, padx=5)
        
        source1_btn = ttk.Button(source1_frame, 
                                text="Browse",
                                command=lambda: self.browse_file("source1"))
        source1_btn.pack(side=tk.LEFT, padx=5)
        
        # Source 2 selection
        source2_frame = ttk.Frame(input_frame)
        source2_frame.pack(padx=10, pady=5, fill=tk.X)
        
        source2_label = ttk.Label(source2_frame, 
                                 text=self.recon_details.get("source2_label", "Source 2:"),
                                 width=20)
        source2_label.pack(side=tk.LEFT)
        
        self.source2_entry = ttk.Entry(source2_frame, width=50)
        self.source2_entry.pack(side=tk.LEFT, padx=5)
        
        source2_btn = ttk.Button(source2_frame, 
                                text="Browse",
                                command=lambda: self.browse_file("source2"))
        source2_btn.pack(side=tk.LEFT, padx=5)
        
        # Source 3 selection (if required)
        if self.recon_details.get("source3_required", False):
            source3_frame = ttk.Frame(input_frame)
            source3_frame.pack(padx=10, pady=5, fill=tk.X)
            
            source3_label = ttk.Label(source3_frame, 
                                     text=self.recon_details.get("source3_label", "Source 3:"),
                                     width=20)
            source3_label.pack(side=tk.LEFT)
            
            self.source3_entry = ttk.Entry(source3_frame, width=50)
            self.source3_entry.pack(side=tk.LEFT, padx=5)
            
            source3_btn = ttk.Button(source3_frame, 
                                    text="Browse",
                                    command=lambda: self.browse_file("source3"))
            source3_btn.pack(side=tk.LEFT, padx=5)
        
        # Parameters section
        params_frame = ttk.LabelFrame(self, text="Reconciliation Parameters")
        params_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Date range (optional)
        date_frame = ttk.Frame(params_frame)
        date_frame.pack(padx=10, pady=5, fill=tk.X)
        
        from_date_label = ttk.Label(date_frame, text="From Date:", width=10)
        from_date_label.pack(side=tk.LEFT)
        
        self.from_date_entry = ttk.Entry(date_frame, width=15)
        self.from_date_entry.pack(side=tk.LEFT, padx=5)
        self.from_date_entry.insert(0, "DD/MM/YYYY")
        
        to_date_label = ttk.Label(date_frame, text="To Date:", width=10)
        to_date_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.to_date_entry = ttk.Entry(date_frame, width=15)
        self.to_date_entry.pack(side=tk.LEFT, padx=5)
        self.to_date_entry.insert(0, "DD/MM/YYYY")
        
        # Threshold settings
        threshold_frame = ttk.Frame(params_frame)
        threshold_frame.pack(padx=10, pady=5, fill=tk.X)
        
        amount_threshold_label = ttk.Label(threshold_frame, text="Amount Threshold:", width=15)
        amount_threshold_label.pack(side=tk.LEFT)
        
        self.amount_threshold_entry = ttk.Entry(threshold_frame, width=10)
        self.amount_threshold_entry.pack(side=tk.LEFT, padx=5)
        self.amount_threshold_entry.insert(0, str(config.AMOUNT_THRESHOLD))
        
        percent_threshold_label = ttk.Label(threshold_frame, text="Percentage Threshold:", width=20)
        percent_threshold_label.pack(side=tk.LEFT, padx=(10, 0))
        
        self.percent_threshold_entry = ttk.Entry(threshold_frame, width=10)
        self.percent_threshold_entry.pack(side=tk.LEFT, padx=5)
        self.percent_threshold_entry.insert(0, str(config.PERCENTAGE_THRESHOLD * 100))
        percent_label = ttk.Label(threshold_frame, text="%")
        percent_label.pack(side=tk.LEFT)
        
        # Action buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(padx=20, pady=10, fill=tk.X)
        
        btn_reconcile = ttk.Button(button_frame, 
                                  text="Perform Reconciliation",
                                  command=self.perform_reconciliation)
        btn_reconcile.pack(side=tk.LEFT, padx=5)
        
        btn_save = ttk.Button(button_frame, 
                             text="Save Results",
                             command=self.save_results)
        btn_save.pack(side=tk.LEFT, padx=5)
        
        btn_reset = ttk.Button(button_frame, 
                              text="Reset",
                              command=self.reset_form)
        btn_reset.pack(side=tk.LEFT, padx=5)
        
        # Results section
        results_frame = ttk.LabelFrame(self, text="Reconciliation Results")
        results_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Results treeview with scrollbars
        self.tree_frame = ttk.Frame(results_frame)
        self.tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create treeview
        self.results_tree = ttk.Treeview(self.tree_frame)
        
        # Add scrollbars
        vsb = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.results_tree.yview)
        hsb = ttk.Scrollbar(self.tree_frame, orient="horizontal", command=self.results_tree.xview)
        self.results_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout for treeview and scrollbars
        self.results_tree.grid(column=0, row=0, sticky="nsew")
        vsb.grid(column=1, row=0, sticky="ns")
        hsb.grid(column=0, row=1, sticky="ew")
        
        # Configure grid weights
        self.tree_frame.columnconfigure(0, weight=1)
        self.tree_frame.rowconfigure(0, weight=1)
        
        # Summary section
        summary_frame = ttk.LabelFrame(self, text="Summary")
        summary_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Summary text widget
        self.summary_text = tk.Text(summary_frame, height=5, wrap=tk.WORD)
        self.summary_text.pack(fill=tk.X, padx=10, pady=10)
        self.summary_text.config(state=tk.DISABLED)
    
    def browse_file(self, source_type):
        """Open file dialog to select a file"""
        filetypes = (("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
        file_path = filedialog.askopenfilename(
            title=f"Select {source_type} file",
            filetypes=filetypes,
            initialdir=config.DEFAULT_INPUT_DIR
        )
        
        if file_path:
            if source_type == "source1":
                self.source1_file = file_path
                self.source1_entry.delete(0, tk.END)
                self.source1_entry.insert(0, file_path)
            elif source_type == "source2":
                self.source2_file = file_path
                self.source2_entry.delete(0, tk.END)
                self.source2_entry.insert(0, file_path)
            elif source_type == "source3":
                self.source3_file = file_path
                self.source3_entry.delete(0, tk.END)
                self.source3_entry.insert(0, file_path)
    
    def perform_reconciliation(self):
        """Perform reconciliation based on selected files and parameters"""
        # Validate inputs
        if not self.validate_inputs():
            return
        
        # Get parameters
        try:
            from_date = None
            to_date = None
            
            if self.from_date_entry.get() != "DD/MM/YYYY":
                from_date = datetime.strptime(self.from_date_entry.get(), "%d/%m/%Y")
            
            if self.to_date_entry.get() != "DD/MM/YYYY":
                to_date = datetime.strptime(self.to_date_entry.get(), "%d/%m/%Y")
            
            amount_threshold = float(self.amount_threshold_entry.get())
            percent_threshold = float(self.percent_threshold_entry.get()) / 100
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid date and threshold values.")
            return
        
        # Load Excel files
        try:
            source1_df = load_excel_file(self.source1_file)
            source2_df = load_excel_file(self.source2_file)
            source3_df = load_excel_file(self.source3_file) if self.source3_file else None
        except Exception as e:
            messagebox.showerror("File Error", f"Error loading files: {str(e)}")
            return
        
        # Perform reconciliation
        try:
            self.result_df = process_reconciliation(
                self.recon_type,
                source1_df,
                source2_df,
                source3_df,
                from_date,
                to_date,
                amount_threshold,
                percent_threshold
            )
            
            # Update results
            self.update_results_tree()
            self.update_summary()
            self.reconciliation_complete = True
            
            messagebox.showinfo("Success", "Reconciliation completed successfully!")
        except Exception as e:
            messagebox.showerror("Reconciliation Error", f"Error during reconciliation: {str(e)}")
    
    def update_results_tree(self):
        """Update the results treeview with reconciliation data"""
        # Clear existing data
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)
        
        # Configure columns
        columns = list(self.result_df.columns)
        
        # Set up treeview columns
        self.results_tree["columns"] = columns
        self.results_tree["show"] = "headings"
        
        # Set column headings and widths
        for col in columns:
            self.results_tree.heading(col, text=col)
            # Determine column width based on content
            max_width = max(len(str(col)), self.result_df[col].astype(str).str.len().max())
            self.results_tree.column(col, width=min(max_width * 10, 300))
        
        # Add data rows
        for _, row in self.result_df.iterrows():
            values = [row[col] for col in columns]
            self.results_tree.insert("", "end", values=values)
    
    def update_summary(self):
        """Update summary section with key metrics"""
        if self.result_df is None:
            return
        
        # Calculate summary statistics
        total_records = len(self.result_df)
        matched_records = self.result_df[self.result_df['Status'] == 'Matched'].shape[0] if 'Status' in self.result_df.columns else 0
        mismatched_records = total_records - matched_records
        
        # Enable text widget for editing
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        
        # Add summary content
        summary = f"Total Records: {total_records}\n"
        summary += f"Matched Records: {matched_records}\n"
        summary += f"Mismatched Records: {mismatched_records}\n"
        
        if 'Difference' in self.result_df.columns:
            total_difference = self.result_df['Difference'].sum() if pd.api.types.is_numeric_dtype(self.result_df['Difference']) else 0
            summary += f"Total Difference Amount: {total_difference:.2f}\n"
        
        self.summary_text.insert(tk.END, summary)
        
        # Disable editing
        self.summary_text.config(state=tk.DISABLED)
    
    def save_results(self):
        """Save reconciliation results to an Excel file"""
        if not self.reconciliation_complete or self.result_df is None:
            messagebox.showinfo("No Results", "Please perform reconciliation first.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Reconciliation Results",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=config.DEFAULT_OUTPUT_DIR
        )
        
        if file_path:
            try:
                # Generate comprehensive report
                report_df = generate_reconciliation_report(self.recon_type, self.result_df)
                
                # Save to Excel
                save_excel_file(report_df, file_path, self.recon_details.get("title", "Reconciliation"))
                
                messagebox.showinfo("Success", f"Results saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Save Error", f"Error saving results: {str(e)}")
    
    def reset_form(self):
        """Reset the form to its initial state"""
        # Clear file paths
        self.source1_file = None
        self.source2_file = None
        self.source3_file = None
        
        # Clear entry fields
        self.source1_entry.delete(0, tk.END)
        self.source2_entry.delete(0, tk.END)
        
        if hasattr(self, 'source3_entry'):
            self.source3_entry.delete(0, tk.END)
        
        # Reset date entries
        self.from_date_entry.delete(0, tk.END)
        self.from_date_entry.insert(0, "DD/MM/YYYY")
        
        self.to_date_entry.delete(0, tk.END)
        self.to_date_entry.insert(0, "DD/MM/YYYY")
        
        # Reset threshold entries
        self.amount_threshold_entry.delete(0, tk.END)
        self.amount_threshold_entry.insert(0, str(config.AMOUNT_THRESHOLD))
        
        self.percent_threshold_entry.delete(0, tk.END)
        self.percent_threshold_entry.insert(0, str(config.PERCENTAGE_THRESHOLD * 100))
        
        # Clear results
        for i in self.results_tree.get_children():
            self.results_tree.delete(i)
        
        # Clear summary
        self.summary_text.config(state=tk.NORMAL)
        self.summary_text.delete(1.0, tk.END)
        self.summary_text.config(state=tk.DISABLED)
        
        # Reset status
        self.result_df = None
        self.reconciliation_complete = False
    
    def validate_inputs(self):
        """Validate input files and parameters"""
        # Check source1 file
        if not self.source1_file or not os.path.exists(self.source1_file):
            messagebox.showerror("Input Error", f"Please select a valid file for {self.recon_details.get('source1_label', 'Source 1')}")
            return False
        
        # Check source2 file
        if not self.source2_file or not os.path.exists(self.source2_file):
            messagebox.showerror("Input Error", f"Please select a valid file for {self.recon_details.get('source2_label', 'Source 2')}")
            return False
        
        # Check source3 file if required
        if self.recon_details.get("source3_required", False):
            if not self.source3_file or not os.path.exists(self.source3_file):
                messagebox.showerror("Input Error", f"Please select a valid file for {self.recon_details.get('source3_label', 'Source 3')}")
                return False
        
        # Validate date format if provided
        if self.from_date_entry.get() != "DD/MM/YYYY":
            try:
                datetime.strptime(self.from_date_entry.get(), "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid From Date format. Use DD/MM/YYYY.")
                return False
        
        if self.to_date_entry.get() != "DD/MM/YYYY":
            try:
                datetime.strptime(self.to_date_entry.get(), "%d/%m/%Y")
            except ValueError:
                messagebox.showerror("Input Error", "Invalid To Date format. Use DD/MM/YYYY.")
                return False
        
        # Validate threshold values
        try:
            float(self.amount_threshold_entry.get())
            float(self.percent_threshold_entry.get())
        except ValueError:
            messagebox.showerror("Input Error", "Threshold values must be numeric.")
            return False
        
        return True
    
    def save_report(self, file_path):
        """Save a comprehensive report"""
        if not self.reconciliation_complete or self.result_df is None:
            messagebox.showinfo("No Results", "Please perform reconciliation first.")
            return False
        
        try:
            # Generate comprehensive report
            report_df = generate_reconciliation_report(self.recon_type, self.result_df)
            
            # Save to Excel
            save_excel_file(report_df, file_path, self.recon_details.get("title", "Reconciliation"))
            return True
        except Exception as e:
            messagebox.showerror("Save Error", f"Error saving report: {str(e)}")
            return False