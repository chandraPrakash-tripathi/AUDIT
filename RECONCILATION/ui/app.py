"""
Main application window for GST Reconciliation System
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.dashboard import Dashboard
from ui.reconcilation_view import ReconciliationView
from ui.report_view import ReportView
import config

class ReconciliationApp(ttk.Frame):
    """Main application class for GST Reconciliation System"""
    
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        
        # Initialize instance variables
        self.current_view = None
        self.input_files = {}
        
        # Setup UI components
        self.setup_styles()
        self.create_menu()
        self.create_sidebar()
        self.create_main_content()
        
        # Show dashboard by default
        self.show_dashboard()
    
    def setup_styles(self):
        """Setup ttk styles for the application"""
        self.style = ttk.Style()
        
        # Configure styles
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("Sidebar.TFrame", background="#2c3e50")
        self.style.configure("Content.TFrame", background="#ffffff")
        
        self.style.configure("Sidebar.TButton", 
                            font=("Arial", 10),
                            background="#2c3e50", 
                            foreground="#ffffff",
                            width=20,
                            anchor="w")
        
        self.style.configure("TLabel", 
                            font=("Arial", 10),
                            background="#ffffff")
        
        self.style.configure("Header.TLabel", 
                            font=("Arial", 12, "bold"),
                            background="#ffffff")
        
    def create_menu(self):
        """Create application menu"""
        self.menu_bar = tk.Menu(self.master)
        
        # File menu
        file_menu = tk.Menu(self.menu_bar, tearoff=0)
        file_menu.add_command(label="Open Files", command=self.open_files)
        file_menu.add_command(label="Save Report", command=self.save_report)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.master.quit)
        self.menu_bar.add_cascade(label="File", menu=file_menu)
        
        # Reconciliation menu
        recon_menu = tk.Menu(self.menu_bar, tearoff=0)
        recon_menu.add_command(label="GSTR-1 vs Books", 
                              command=lambda: self.show_reconciliation_view("gstr1_books"))
        recon_menu.add_command(label="GSTR-2A/2B vs Books", 
                              command=lambda: self.show_reconciliation_view("gstr2_books"))
        recon_menu.add_command(label="GSTR-3B vs GSTR-1", 
                              command=lambda: self.show_reconciliation_view("gstr3b_gstr1"))
        recon_menu.add_command(label="GSTR-3B vs Books", 
                              command=lambda: self.show_reconciliation_view("gstr3b_books"))
        recon_menu.add_command(label="ITC in GSTR-3B vs GSTR-2B", 
                              command=lambda: self.show_reconciliation_view("itc_gstr3b_gstr2b"))
        recon_menu.add_command(label="ITC in Books vs Eligible ITC", 
                              command=lambda: self.show_reconciliation_view("itc_eligibility"))
        recon_menu.add_command(label="GSTR-1 vs E-Way Bills", 
                              command=lambda: self.show_reconciliation_view("gstr1_eway"))
        recon_menu.add_command(label="GSTR-2A/2B vs E-Way Bills", 
                              command=lambda: self.show_reconciliation_view("gstr2_eway"))
        recon_menu.add_command(label="GSTR-1 vs E-invoice", 
                              command=lambda: self.show_reconciliation_view("gstr1_einvoice"))
        recon_menu.add_command(label="Turnover Reconciliation", 
                              command=lambda: self.show_reconciliation_view("turnover_recon"))
        self.menu_bar.add_cascade(label="Reconciliation", menu=recon_menu)
        
        # Help menu
        help_menu = tk.Menu(self.menu_bar, tearoff=0)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        self.menu_bar.add_cascade(label="Help", menu=help_menu)
        
        # Set menu
        self.master.config(menu=self.menu_bar)
    
    def create_sidebar(self):
        """Create sidebar with navigation buttons"""
        self.sidebar = ttk.Frame(self, style="Sidebar.TFrame", width=200)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # App title
        title_label = ttk.Label(self.sidebar, text="GST Reconciliation", 
                              font=("Arial", 14, "bold"),
                              foreground="#ffffff",
                              background="#2c3e50")
        title_label.pack(pady=20, padx=10)
        
        # Navigation buttons
        btn_dashboard = ttk.Button(self.sidebar, text="Dashboard", 
                                 style="Sidebar.TButton",
                                 command=self.show_dashboard)
        btn_dashboard.pack(pady=5, padx=10, fill=tk.X)
        
        # Reconciliation buttons
        recon_label = ttk.Label(self.sidebar, text="Reconciliations:",
                              font=("Arial", 10, "bold"),
                              foreground="#ffffff",
                              background="#2c3e50")
        recon_label.pack(pady=(10, 5), padx=10, anchor="w")
        
        recon_types = [
            ("GSTR-1 vs Books", "gstr1_books"),
            ("GSTR-2A/2B vs Books", "gstr2_books"),
            ("GSTR-3B vs GSTR-1", "gstr3b_gstr1"),
            ("GSTR-3B vs Books", "gstr3b_books"),
            ("ITC: GSTR-3B vs GSTR-2B", "itc_gstr3b_gstr2b"),
            ("ITC: Books vs Eligible", "itc_eligibility"),
            ("GSTR-1 vs E-Way Bills", "gstr1_eway"),
            ("GSTR-2A/2B vs E-Way Bills", "gstr2_eway"),
            ("GSTR-1 vs E-invoice", "gstr1_einvoice"),
            ("Turnover Reconciliation", "turnover_recon")
        ]
        
        for text, recon_type in recon_types:
            btn = ttk.Button(self.sidebar, text=text, 
                           style="Sidebar.TButton",
                           command=lambda rt=recon_type: self.show_reconciliation_view(rt))
            btn.pack(pady=2, padx=10, fill=tk.X)
        
        # Reports button
        btn_reports = ttk.Button(self.sidebar, text="Reports", 
                               style="Sidebar.TButton",
                               command=self.show_reports)
        btn_reports.pack(pady=(15, 5), padx=10, fill=tk.X)
        
        # Settings button
        btn_settings = ttk.Button(self.sidebar, text="Settings", 
                                style="Sidebar.TButton",
                                command=self.show_settings)
        btn_settings.pack(pady=5, padx=10, fill=tk.X)
        
    def create_main_content(self):
        """Create main content area"""
        self.content_frame = ttk.Frame(self, style="Content.TFrame")
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
    
    def show_dashboard(self):
        """Show dashboard view"""
        self.clear_content()
        self.current_view = Dashboard(self.content_frame)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    def show_reconciliation_view(self, recon_type):
        """Show reconciliation view for specific type"""
        self.clear_content()
        self.current_view = ReconciliationView(self.content_frame, recon_type)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    def show_reports(self):
        """Show reports view"""
        self.clear_content()
        self.current_view = ReportView(self.content_frame)
        self.current_view.pack(fill=tk.BOTH, expand=True)
    
    def show_settings(self):
        """Show settings view"""
        messagebox.showinfo("Settings", "Settings will be implemented in future versions.")
    
    def clear_content(self):
        """Clear content area"""
        if self.current_view:
            self.current_view.destroy()
            self.current_view = None
        
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def open_files(self):
        """Open file dialog to select input files"""
        filetypes = (("Excel files", "*.xlsx *.xls"), ("All files", "*.*"))
        files = filedialog.askopenfilenames(
            title="Select input files",
            filetypes=filetypes,
            initialdir=config.DEFAULT_INPUT_DIR
        )
        
        if files:
            # Process selected files
            for file in files:
                file_name = os.path.basename(file)
                self.input_files[file_name] = file
            
            messagebox.showinfo("Files Selected", f"{len(files)} files have been selected.")
            
            # Update dashboard if it's currently shown
            if isinstance(self.current_view, Dashboard):
                self.show_dashboard()
    
    def save_report(self):
        """Save generated report"""
        if not hasattr(self.current_view, 'save_report'):
            messagebox.showinfo("Save Report", "No report available to save.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Report",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialdir=config.DEFAULT_OUTPUT_DIR
        )
        
        if file_path:
            self.current_view.save_report(file_path)
            messagebox.showinfo("Report Saved", f"Report has been saved to {file_path}")
    
    def show_documentation(self):
        """Show documentation"""
        messagebox.showinfo("Documentation", 
                          "Documentation for GST Reconciliation System\n\n"
                          "Please refer to the user manual for detailed instructions.")
    
    def show_about(self):
        """Show about dialog"""
        messagebox.showinfo("About", 
                          f"{config.APP_NAME} v{config.APP_VERSION}\n\n"
                          "A comprehensive GST reconciliation tool to help businesses "
                          "reconcile their GST data across various sources.")