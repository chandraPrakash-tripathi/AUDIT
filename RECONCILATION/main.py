"""
GST Reconciliation System - Main Entry Point
"""
import tkinter as tk
from ui.app import ReconciliationApp

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    root.title("GST Reconciliation System")
    root.geometry("1200x700")
    
    # Create and run the application
    app = ReconciliationApp(root)
    app.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    main()