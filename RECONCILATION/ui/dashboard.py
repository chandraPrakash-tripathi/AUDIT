"""
Dashboard view for GST Reconciliation System
"""
import tkinter as tk
from tkinter import ttk
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Dashboard(ttk.Frame):
    """Dashboard view showing reconciliation options and summary"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # Create UI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create dashboard widgets"""
        # Welcome header
        header_frame = ttk.Frame(self)
        header_frame.pack(pady=20, padx=20, fill=tk.X)
        
        welcome_label = ttk.Label(header_frame, 
                                text="GST Reconciliation Dashboard",
                                font=("Arial", 16, "bold"))
        welcome_label.pack(anchor="w")
        
        subheader_label = ttk.Label(header_frame, 
                                  text="Select a reconciliation type to get started",
                                  font=("Arial", 12))
        subheader_label.pack(anchor="w", pady=5)
        
        # Separator
        ttk.Separator(self, orient="horizontal").pack(fill=tk.X, padx=20, pady=10)
        
        # Reconciliation types grid
        recon_frame = ttk.Frame(self)
        recon_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        
        # Configure grid
        recon_frame.columnconfigure(0, weight=1)
        recon_frame.columnconfigure(1, weight=1)
        recon_frame.columnconfigure(2, weight=1)
        
        # Reconciliation option cards
        self.create_recon_card(recon_frame, 0, 0, 
                              "GSTR-1 vs Books",
                              "Reconcile sales data between GSTR-1 and books of accounts",
                              "gstr1_books")
        
        self.create_recon_card(recon_frame, 0, 1, 
                              "GSTR-2A/2B vs Books",
                              "Reconcile purchase data between GSTR-2A/2B and books",
                              "gstr2_books")
        
        self.create_recon_card(recon_frame, 0, 2, 
                              "GSTR-3B vs GSTR-1",
                              "Reconcile liability reporting between GSTR-3B and GSTR-1",
                              "gstr3b_gstr1")
        
        self.create_recon_card(recon_frame, 1, 0, 
                              "GSTR-3B vs Books",
                              "Reconcile output tax between GSTR-3B and books",
                              "gstr3b_books")
        
        self.create_recon_card(recon_frame, 1, 1, 
                              "ITC Reconciliation",
                              "Reconcile ITC between GSTR-3B and GSTR-2B",
                              "itc_gstr3b_gstr2b")
        
        self.create_recon_card(recon_frame, 1, 2, 
                              "ITC Eligibility",
                              "Reconcile ITC in books vs eligible ITC",
                              "itc_eligibility")
        
        self.create_recon_card(recon_frame, 2, 0, 
                              "GSTR-1 vs E-Way Bills",
                              "Reconcile GSTR-1 with E-Way bills",
                              "gstr1_eway")
        
        self.create_recon_card(recon_frame, 2, 1, 
                              "GSTR-2A/2B vs E-Way Bills",
                              "Reconcile GSTR-2A/2B with E-Way bills",
                              "gstr2_eway")
        
        self.create_recon_card(recon_frame, 2, 2, 
                              "GSTR-1 vs E-invoice",
                              "Reconcile GSTR-1 with E-invoices",
                              "gstr1_einvoice")
        
        self.create_recon_card(recon_frame, 3, 0, 
                              "Turnover Reconciliation",
                              "Reconcile turnover across books, GST returns, and financial statements",
                              "turnover_recon")
        
        # Status section
        status_frame = ttk.Frame(self)
        status_frame.pack(padx=20, pady=20, fill=tk.X)
        
        status_label = ttk.Label(status_frame, 
                               text="System Status: Ready",
                               font=("Arial", 10))
        status_label.pack(side=tk.LEFT)
        
        version_label = ttk.Label(status_frame, 
                                text="v1.0.0",
                                font=("Arial", 10))
        version_label.pack(side=tk.RIGHT)
    
    def create_recon_card(self, parent, row, col, title, description, recon_type):
        """Create a reconciliation option card"""
        card_frame = ttk.Frame(parent, relief=tk.RAISED, borderwidth=1)
        card_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Card content
        title_label = ttk.Label(card_frame, 
                              text=title,
                              font=("Arial", 12, "bold"))
        title_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        desc_label = ttk.Label(card_frame, 
                             text=description,
                             wraplength=200)
        desc_label.pack(anchor="w", padx=10, pady=5)
        
        # Open button
        btn_open = ttk.Button(card_frame, 
                            text="Open",
                            command=lambda rt=recon_type: self.open_reconciliation(rt))
        btn_open.pack(anchor="e", padx=10, pady=10)
    
    def open_reconciliation(self, recon_type):
        """Open the selected reconciliation view"""
        # Get the parent application reference
        app = self.master.master
        
        # Call the show_reconciliation_view method if it exists
        if hasattr(app, 'show_reconciliation_view'):
            app.show_reconciliation_view(recon_type)
        else:
            print(f"Cannot open reconciliation view: {recon_type}")