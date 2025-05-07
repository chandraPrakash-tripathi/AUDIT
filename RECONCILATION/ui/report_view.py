"""
Report view for GST Reconciliation System
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
from utils.report_generator import generate_consolidated_report

class ReportView(ttk.Frame):
    """View for generating and displaying consolidated reports"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # Initialize instance variables
        self.recon_files = []
        self.report_df = None
        self.report_generated = False
        
        # Create UI components
        self.create_widgets()
    
    def create_widgets(self):
        """Create view widgets"""
        # Header
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=20, padx=20, fill=tk.X)
        
        title_label = ttk.Label(header_frame, 
                              text="GST Reconciliation Reports",
                              font=("Arial", 16, "bold"))
        title_label.pack(anchor="w")
        
        subheader_label = ttk.Label(header_frame, 
                                  text="Generate consolidated reports from reconciliation results",
                                  font=("Arial", 12))
        subheader_label.pack(anchor="w", pady=5)
        
        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # File selection section
        file_frame = ttk.LabelFrame(self, text="Select Reconciliation Files")
        file_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Files list with scrollbar
        list_frame = ttk.Frame(file_frame)
        list_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.file_listbox = tk.Listbox(list_frame, height=6, width=80)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # Buttons for file operations
        file_btn_frame = ttk.Frame(file_frame)
        file_btn_frame.pack(padx=10, pady=5, fill=tk.X)
        
        add_btn = ttk.Button(file_btn_frame, text="Add Files", command=self.add_files)
        add_btn.pack(side=tk.LEFT, padx=5)
        
        remove_btn = ttk.Button(file_btn_frame, text="Remove Selected", command=self.remove_selected)
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        clear_btn = ttk.Button(file_btn_frame, text="Clear All", command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Report options section
        options_frame = ttk.LabelFrame(self, text="Report Options")
        options_frame.pack(padx=20, pady=10, fill=tk.X)
        
        # Report type selection
        type_frame = ttk.Frame(options_frame)
        type_frame.pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Label(type_frame, text="Report Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.report_type = tk.StringVar(value="summary")
        report_options = [
            ("Summary Report", "summary"),
            ("Detailed Report", "detailed"),
            ("Variance Analysis", "variance"),
        ]
        
        for i, (text, value) in enumerate(report_options):
            ttk.Radiobutton(type_frame, text=text, value=value, variable=self.report_type).grid(
                row=0, column=i+1, padx=10, pady=5, sticky=tk.W
            )
        
        # Date range selection
        date_frame = ttk.Frame(options_frame)
        date_frame.pack(padx=10, pady=10, fill=tk.X)
        
        ttk.Label(date_frame, text="Period:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        # Month selection
        self.month_var = tk.StringVar()
        months = ["January", "February", "March", "April", "May", "June", 
                 "July", "August", "September", "October", "November", "December"]
        month_combo = ttk.Combobox(date_frame, textvariable=self.month_var, values=months, width=12)
        month_combo.grid(row=0, column=1, padx=5, pady=5)
        month_combo.current(datetime.now().month - 1)
        
        # Year selection
        self.year_var = tk.StringVar()
        current_year = datetime.now().year
        years = [str(current_year - i) for i in range(5)]
        year_combo = ttk.Combobox(date_frame, textvariable=self.year_var, values=years, width=8)
        year_combo.grid(row=0, column=2, padx=5, pady=5)
        year_combo.current(0)
        
        # Additional options
        options_inner_frame = ttk.Frame(options_frame)
        options_inner_frame.pack(padx=10, pady=10, fill=tk.X)
        
        self.include_charts = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner_frame, text="Include Charts", variable=self.include_charts).pack(side=tk.LEFT, padx=5)
        
        self.include_summary = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner_frame, text="Include Executive Summary", variable=self.include_summary).pack(side=tk.LEFT, padx=5)
        
        self.include_recommendations = tk.BooleanVar(value=True)
        ttk.Checkbutton(options_inner_frame, text="Include Recommendations", variable=self.include_recommendations).pack(side=tk.LEFT, padx=5)
        
        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # Generate report button
        action_frame = ttk.Frame(self)
        action_frame.pack(pady=10, padx=20, fill=tk.X)
        
        generate_btn = ttk.Button(action_frame, text="Generate Report", command=self.generate_report)
        generate_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = ttk.Button(action_frame, text="Save Report", command=self.save_report)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        preview_btn = ttk.Button(action_frame, text="Preview Report", command=self.preview_report)
        preview_btn.pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=5)
    
    def add_files(self):
        """Add reconciliation files to the list"""
        filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(filetypes=filetypes, 
                                          title="Select Reconciliation Files")
        
        if files:
            for file in files:
                if file not in self.recon_files:
                    self.recon_files.append(file)
                    self.file_listbox.insert(tk.END, os.path.basename(file))
            
            self.status_var.set(f"{len(files)} file(s) added")
            self.report_generated = False
    
    def remove_selected(self):
        """Remove selected files from the list"""
        selected_indices = self.file_listbox.curselection()
        
        if not selected_indices:
            messagebox.showinfo("No Selection", "Please select a file to remove")
            return
        
        # Remove from the end to avoid index issues
        for index in sorted(selected_indices, reverse=True):
            self.recon_files.pop(index)
            self.file_listbox.delete(index)
        
        self.status_var.set(f"{len(selected_indices)} file(s) removed")
        self.report_generated = False
    
    def clear_all(self):
        """Clear all files from the list"""
        if self.recon_files:
            self.recon_files = []
            self.file_listbox.delete(0, tk.END)
            self.status_var.set("All files cleared")
            self.report_generated = False
    
    def generate_report(self):
        """Generate consolidated report"""
        if not self.recon_files:
            messagebox.showwarning("No Files", "Please add reconciliation files first")
            return
        
        try:
            # Set status to processing
            self.status_var.set("Generating report, please wait...")
            self.update_idletasks()
            
            # Get selected options
            report_type = self.report_type.get()
            period = f"{self.month_var.get()} {self.year_var.get()}"
            options = {
                "include_charts": self.include_charts.get(),
                "include_summary": self.include_summary.get(),
                "include_recommendations": self.include_recommendations.get()
            }
            
            # Generate report
            self.report_df = generate_consolidated_report(
                self.recon_files, 
                report_type=report_type,
                period=period,
                options=options
            )
            
            self.report_generated = True
            self.status_var.set("Report generated successfully")
            
            # Show preview dialog
            self.preview_report()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error generating report: {str(e)}")
            self.status_var.set("Error generating report")
    
    def save_report(self):
        """Save generated report to file"""
        if not self.report_generated:
            messagebox.showinfo("No Report", "Please generate a report first")
            return
        
        filetypes = [("Excel files", "*.xlsx")]
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=filetypes,
            title="Save Report As",
            initialfile=f"GST_Reconciliation_Report_{self.month_var.get()}_{self.year_var.get()}.xlsx"
        )
        
        if filename:
            try:
                save_excel_file(self.report_df, filename)
                self.status_var.set(f"Report saved to {filename}")
                messagebox.showinfo("Success", f"Report saved successfully to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving report: {str(e)}")
                self.status_var.set("Error saving report")
    
    def preview_report(self):
        """Preview the generated report"""
        if not self.report_generated:
            messagebox.showinfo("No Report", "Please generate a report first")
            return
        
        # Create a preview window
        preview_window = tk.Toplevel(self.master)
        preview_window.title("Report Preview")
        preview_window.geometry("800x600")
        
        # Create a frame with scrollbars
        frame = ttk.Frame(preview_window)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a Treeview to display the report data
        columns = list(self.report_df.columns)
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        
        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # Add data rows
        for _, row in self.report_df.iterrows():
            values = [row[col] for col in columns]
            tree.insert("", tk.END, values=values)
        
        # Add scrollbars
        y_scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        x_scrollbar = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)
        
        # Pack everything
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add a close button
        ttk.Button(preview_window, text="Close", command=preview_window.destroy).pack(pady=10)