"""
PCB Trace Cross-Section Visualizer with ATLC Integration
A GUI application for generating BMP images of various PCB trace geometries
and calculating transmission line parameters using ATLC
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Rectangle, Polygon
import numpy as np
from pathlib import Path
from PIL import Image
import io
import subprocess


class PCBTraceVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("PCB Trace Visualizer with ATLC")
        self.root.geometry("1000x850")
        
        # Configure style
        style = ttk.Style()
        style.theme_use('clam')
        
        # Color scheme
        self.colors = {
            'copper': '#00FF00',  # Green for ground planes
            'substrate': '#C8A870',  # Yellowish-brown for dielectric
            'solder_mask': '#1B4332',
            'air': '#FFFFFF',  # White for air
            'background': '#FFFFFF',  # White background
            'signal': '#FF0000',  # Red for single-ended signal
            'signal_pos': '#FF0000',  # Red for positive differential
            'signal_neg': '#0000FF'  # Blue for negative differential
        }
        
        # Configure custom styles
        style.configure('Title.TLabel', font=('Segoe UI', 16, 'bold'), foreground='#2C3E50')
        style.configure('Section.TLabel', font=('Segoe UI', 11, 'bold'), foreground='#34495E')
        style.configure('Input.TLabel', font=('Segoe UI', 9), foreground='#555555')
        style.configure('Custom.TButton', font=('Segoe UI', 10))
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=3)  # Give more weight to visualization row
        main_frame.rowconfigure(2, weight=1)  # Output panel row
        
        # Title
        title_label = ttk.Label(main_frame, text="PCB Trace Visualizer with ATLC", 
                                style='Title.TLabel')
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky=tk.W)
        
        # Left panel - Controls
        self.setup_control_panel(main_frame)
        
        # Right panel - Visualization
        self.setup_visualization_panel(main_frame)
        
        # Bottom panel - ATLC Output
        self.setup_output_panel(main_frame)
        
    def setup_control_panel(self, parent):
        """Set up the control panel with inputs"""
        control_frame = ttk.Frame(parent, padding="10", relief=tk.GROOVE, borderwidth=2)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Trace type selection
        ttk.Label(control_frame, text="Trace Type", style='Section.TLabel').grid(
            row=0, column=0, columnspan=2, pady=(0, 10), sticky=tk.W)
        
        self.trace_type = tk.StringVar(value="microstrip")
        trace_types = [
            ("Microstrip", "microstrip"),
            ("Stripline", "stripline"),
            ("Differential Pair", "differential_pair"),
            ("Coplanar Differential", "coplanar_differential"),
            ("Coplanar Waveguide", "coplanar_waveguide")
        ]
        
        for i, (text, value) in enumerate(trace_types, start=1):
            ttk.Radiobutton(control_frame, text=text, variable=self.trace_type, 
                           value=value, command=self.update_input_fields).grid(
                row=i, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Input fields frame
        self.input_frame = ttk.Frame(control_frame)
        self.input_frame.grid(row=len(trace_types)+1, column=0, columnspan=2, 
                             pady=(15, 0), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Store entry widgets
        self.entries = {}
        
        # Initialize with microstrip fields
        self.update_input_fields()
        
        # Buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.grid(row=len(trace_types)+2, column=0, columnspan=2, pady=(15, 0))
        
        ttk.Button(button_frame, text="Generate", command=self.generate_visualization,
                  style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save BMP and Calculate Zo", command=self.save_bmp,
                  style='Custom.TButton').pack(side=tk.LEFT, padx=5)
        
    def setup_visualization_panel(self, parent):
        """Set up the visualization panel"""
        viz_frame = ttk.Frame(parent, relief=tk.GROOVE, borderwidth=2)
        viz_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Create matplotlib figure with white background
        self.fig, self.ax = plt.subplots(figsize=(6, 5), facecolor='white')
        self.ax.set_aspect('equal')
        self.ax.set_facecolor(self.colors['air'])
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=viz_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initial message
        self.ax.text(0.5, 0.5, 'Click "Generate" to visualize',
                    ha='center', va='center', fontsize=14, color='#7F8C8D',
                    transform=self.ax.transAxes)
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis('off')
        self.canvas.draw()
        
    def setup_output_panel(self, parent):
        """Set up the ATLC output panel"""
        output_frame = ttk.Frame(parent, relief=tk.GROOVE, borderwidth=2, padding="10")
        output_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Label
        ttk.Label(output_frame, text="ATLC Output:", style='Section.TLabel').pack(anchor=tk.W, pady=(0, 5))
        
        # Text widget with scrollbar
        text_frame = ttk.Frame(output_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.output_text = tk.Text(text_frame, height=8, wrap=tk.WORD, 
                                   yscrollcommand=scrollbar.set,
                                   font=('Courier', 9),
                                   bg='#F8F9FA', fg='#2C3E50')
        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.output_text.yview)
        
        # Initial message
        self.output_text.insert('1.0', 'ATLC output will appear here after saving and calculating...')
        self.output_text.config(state=tk.DISABLED)
        
    def update_input_fields(self):
        """Update input fields based on selected trace type"""
        # Clear existing fields
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        self.entries.clear()
        
        # Define fields for each trace type
        field_definitions = {
            'microstrip': [
                ('Trace Width (mm)', 'width', '0.5'),
                ('Trace Thickness (mm)', 'thickness', '0.035'),
                ('Substrate Height (mm)', 'substrate_h', '1.6'),
                ('Solder Mask Thickness (mm)', 'mask_thickness', '0.025'),
                ('Dielectric Constant (Er)', 'dielectric_er', '4.4')
            ],
            'stripline': [
                ('Trace Width (mm)', 'width', '0.5'),
                ('Trace Thickness (mm)', 'thickness', '0.035'),
                ('Substrate Height (mm)', 'substrate_h', '1.6'),
                ('Top Dielectric (mm)', 'top_dielectric', '0.8'),
                ('Dielectric Constant (Er)', 'dielectric_er', '4.4')
            ],
            'differential_pair': [
                ('Trace Width (mm)', 'width', '0.4'),
                ('Trace Thickness (mm)', 'thickness', '0.035'),
                ('Trace Spacing (mm)', 'spacing', '0.3'),
                ('Substrate Height (mm)', 'substrate_h', '1.6'),
                ('Solder Mask Thickness (mm)', 'mask_thickness', '0.025'),
                ('Dielectric Constant (Er)', 'dielectric_er', '4.4')
            ],
            'coplanar_differential': [
                ('Trace Width (mm)', 'width', '0.4'),
                ('Trace Thickness (mm)', 'thickness', '0.035'),
                ('Trace Spacing (mm)', 'spacing', '0.3'),
                ('Ground Gap (mm)', 'ground_gap', '0.2'),
                ('Ground Width (mm)', 'ground_width', '1.0'),
                ('Substrate Height (mm)', 'substrate_h', '1.6'),
                ('Dielectric Constant (Er)', 'dielectric_er', '4.4')
            ],
            'coplanar_waveguide': [
                ('Trace Width (mm)', 'width', '0.5'),
                ('Trace Thickness (mm)', 'thickness', '0.035'),
                ('Ground Gap (mm)', 'ground_gap', '0.2'),
                ('Ground Width (mm)', 'ground_width', '1.5'),
                ('Substrate Height (mm)', 'substrate_h', '1.6'),
                ('Dielectric Constant (Er)', 'dielectric_er', '4.4')
            ]
        }
        
        fields = field_definitions[self.trace_type.get()]
        
        # Create input fields
        for i, (label, key, default) in enumerate(fields):
            ttk.Label(self.input_frame, text=label, style='Input.TLabel').grid(
                row=i, column=0, sticky=tk.W, pady=5, padx=(0, 10))
            
            entry = ttk.Entry(self.input_frame, width=15)
            entry.insert(0, default)
            entry.grid(row=i, column=1, sticky=(tk.W, tk.E), pady=5)
            self.entries[key] = entry
            
    def get_dimensions(self):
        """Get dimensions from entry fields"""
        dims = {}
        for key, entry in self.entries.items():
            try:
                dims[key] = float(entry.get())
                if dims[key] <= 0:
                    raise ValueError(f"{key} must be positive")
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Error in {key}: {str(e)}")
                return None
        return dims
    
    def generate_visualization(self):
        """Generate the trace cross-section visualization"""
        dims = self.get_dimensions()
        if dims is None:
            return
        
        # Clear previous plot
        self.ax.clear()
        self.ax.set_aspect('equal')
        self.ax.set_facecolor(self.colors['air'])
        
        trace_type = self.trace_type.get()
        
        # Generate appropriate trace
        if trace_type == 'microstrip':
            self.draw_microstrip(dims)
        elif trace_type == 'stripline':
            self.draw_stripline(dims)
        elif trace_type == 'differential_pair':
            self.draw_differential_pair(dims)
        elif trace_type == 'coplanar_differential':
            self.draw_coplanar_differential(dims)
        elif trace_type == 'coplanar_waveguide':
            self.draw_coplanar_waveguide(dims)
        
        # Clean visualization - no decorations
        self.ax.axis('off')
        
        self.canvas.draw()
        
    def draw_microstrip(self, dims):
        """Draw microstrip cross-section"""
        w = dims['width']
        t = dims['thickness']
        h = dims['substrate_h']
        m = dims['mask_thickness']
        
        # Calculate total width for centering
        total_w = max(w * 3, 5.0)
        
        # Substrate
        substrate = Rectangle((-total_w/2, -h), total_w, h, 
                             facecolor=self.colors['substrate'], 
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(substrate)
        
        # Trace (red for signal)
        trace = Rectangle((-w/2, 0), w, t,
                         facecolor=self.colors['signal'],
                         edgecolor='none', linewidth=0)
        self.ax.add_patch(trace)
        
        # Ground plane (green copper)
        ground = Rectangle((-total_w/2, -h), total_w, 0.035,
                          facecolor=self.colors['copper'],
                          edgecolor='none', linewidth=0)
        self.ax.add_patch(ground)
        
        self.ax.set_xlim(-total_w/2, total_w/2)
        self.ax.set_ylim(-h, t + m)
        
    def draw_stripline(self, dims):
        """Draw stripline cross-section"""
        w = dims['width']
        t = dims['thickness']
        h = dims['substrate_h']
        top_d = dims['top_dielectric']
        
        total_w = max(w * 3, 5.0)
        
        # Bottom substrate
        bottom_sub = Rectangle((-total_w/2, -h + top_d), total_w, h - top_d,
                              facecolor=self.colors['substrate'],
                              edgecolor='none', linewidth=0)
        self.ax.add_patch(bottom_sub)
        
        # Top substrate
        top_sub = Rectangle((-total_w/2, t), total_w, top_d,
                           facecolor=self.colors['substrate'],
                           edgecolor='none', linewidth=0)
        self.ax.add_patch(top_sub)
        
        # Trace (red for signal)
        trace = Rectangle((-w/2, 0), w, t,
                         facecolor=self.colors['signal'],
                         edgecolor='none', linewidth=0)
        self.ax.add_patch(trace)
        
        # Ground planes (green copper)
        gnd_bottom = Rectangle((-total_w/2, -h + top_d - 0.035), total_w, 0.035,
                               facecolor=self.colors['copper'],
                               edgecolor='none', linewidth=0)
        gnd_top = Rectangle((-total_w/2, top_d + t), total_w, 0.035,
                           facecolor=self.colors['copper'],
                           edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_bottom)
        self.ax.add_patch(gnd_top)
        
        self.ax.set_xlim(-total_w/2, total_w/2)
        self.ax.set_ylim(-h + top_d - 0.5, top_d + t + 0.035)
        
    def draw_differential_pair(self, dims):
        """Draw differential pair cross-section"""
        w = dims['width']
        t = dims['thickness']
        s = dims['spacing']
        h = dims['substrate_h']
        m = dims['mask_thickness']
        
        total_w = max((w * 2 + s) * 2, 5.0)
        
        # Substrate
        substrate = Rectangle((-total_w/2, -h), total_w, h,
                             facecolor=self.colors['substrate'],
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(substrate)
        
        # Ground plane (green copper)
        ground = Rectangle((-total_w/2, -h), total_w, 0.035,
                          facecolor=self.colors['copper'],
                          edgecolor='none', linewidth=0)
        self.ax.add_patch(ground)
        
        # Left trace (red for positive)
        trace_left = Rectangle((-s/2 - w, 0), w, t,
                              facecolor=self.colors['signal_pos'],
                              edgecolor='none', linewidth=0)
        self.ax.add_patch(trace_left)
        
        # Right trace (blue for negative)
        trace_right = Rectangle((s/2, 0), w, t,
                               facecolor=self.colors['signal_neg'],
                               edgecolor='none', linewidth=0)
        self.ax.add_patch(trace_right)
        
        self.ax.set_xlim(-total_w/2, total_w/2)
        self.ax.set_ylim(-h, t + m)
        
    def draw_coplanar_differential(self, dims):
        """Draw coplanar differential pair cross-section"""
        w = dims['width']
        t = dims['thickness']
        s = dims['spacing']
        g = dims['ground_gap']
        gw = dims['ground_width']
        h = dims['substrate_h']
        
        total_w = 2 * (gw + g + w + s/2)
        
        # Substrate
        substrate = Rectangle((-total_w/2, -h), total_w, h,
                             facecolor=self.colors['substrate'],
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(substrate)
        
        # Bottom ground plane (green copper)
        gnd_bottom = Rectangle((-total_w/2, -h), total_w, 0.035,
                              facecolor=self.colors['copper'],
                              edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_bottom)
        
        # Left ground (green copper)
        gnd_left = Rectangle((-total_w/2, 0), gw, t,
                            facecolor=self.colors['copper'],
                            edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_left)
        
        # Right ground (green copper)
        gnd_right = Rectangle((total_w/2 - gw, 0), gw, t,
                             facecolor=self.colors['copper'],
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_right)
        
        # Left trace (red for positive)
        trace_left = Rectangle((-s/2 - w, 0), w, t,
                              facecolor=self.colors['signal_pos'],
                              edgecolor='none', linewidth=0)
        self.ax.add_patch(trace_left)
        
        # Right trace (blue for negative)
        trace_right = Rectangle((s/2, 0), w, t,
                               facecolor=self.colors['signal_neg'],
                               edgecolor='none', linewidth=0)
        self.ax.add_patch(trace_right)
        
        self.ax.set_xlim(-total_w/2, total_w/2)
        self.ax.set_ylim(-h, t)
        
    def draw_coplanar_waveguide(self, dims):
        """Draw coplanar waveguide cross-section"""
        w = dims['width']
        t = dims['thickness']
        g = dims['ground_gap']
        gw = dims['ground_width']
        h = dims['substrate_h']
        
        total_w = 2 * (gw + g) + w
        
        # Substrate
        substrate = Rectangle((-total_w/2, -h), total_w, h,
                             facecolor=self.colors['substrate'],
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(substrate)
        
        # Bottom ground plane (green copper)
        gnd_bottom = Rectangle((-total_w/2, -h), total_w, 0.035,
                              facecolor=self.colors['copper'],
                              edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_bottom)
        
        # Left ground (green copper)
        gnd_left = Rectangle((-total_w/2, 0), gw, t,
                            facecolor=self.colors['copper'],
                            edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_left)
        
        # Right ground (green copper)
        gnd_right = Rectangle((total_w/2 - gw, 0), gw, t,
                             facecolor=self.colors['copper'],
                             edgecolor='none', linewidth=0)
        self.ax.add_patch(gnd_right)
        
        # Signal trace (red)
        trace = Rectangle((-w/2, 0), w, t,
                         facecolor=self.colors['signal'],
                         edgecolor='none', linewidth=0)
        self.ax.add_patch(trace)
        
        self.ax.set_xlim(-total_w/2, total_w/2)
        self.ax.set_ylim(-h, t)
        
    def save_bmp(self):
        """Save the current visualization as a BMP file and run ATLC"""
        if not self.ax.patches:
            messagebox.showwarning("No Visualization", 
                                  "Please generate a visualization first!")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".bmp",
            filetypes=[("BMP files", "*.bmp"), ("All files", "*.*")],
            initialfile=f"pcb_{self.trace_type.get()}.bmp"
        )
        
        if filename:
            try:
                # Save to a buffer as PNG first with clean output
                buf = io.BytesIO()
                self.fig.savefig(buf, format='png', dpi=300, bbox_inches='tight',
                               facecolor=self.colors['background'], pad_inches=0)
                buf.seek(0)
                
                # Convert to BMP using PIL
                img = Image.open(buf).convert('RGB')
                img.save(filename, format='BMP')
                buf.close()
                
                # Clear previous output
                self.output_text.config(state=tk.NORMAL)
                self.output_text.delete('1.0', tk.END)
                
                # Get dielectric constant from input fields
                try:
                    dielectric_er = self.entries['dielectric_er'].get()
                    dielectric_rgb = self.colors['substrate'][1:]  # RGB value of the dielectric color
                    
                    # Write status to output
                    self.output_text.insert(tk.END, f"Image saved to: {filename}\n")
                    self.output_text.insert(tk.END, f"Running ATLC with Er={dielectric_er}...\n\n")
                    self.output_text.config(state=tk.DISABLED)
                    self.root.update()  # Update UI to show progress
                    
                    # Run atlc command
                    cmd = ['atlc', f'-d{dielectric_rgb}={dielectric_er}', filename]
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    
                    # Update output with results
                    self.output_text.config(state=tk.NORMAL)
                    if result.returncode == 0:
                        self.output_text.insert(tk.END, "ATLC calculation completed successfully!\n")
                        self.output_text.insert(tk.END, "=" * 60 + "\n")
                        self.output_text.insert(tk.END, result.stdout)
                        if result.stderr:
                            self.output_text.insert(tk.END, "\n" + "=" * 60 + "\n")
                            self.output_text.insert(tk.END, "Additional Info:\n")
                            self.output_text.insert(tk.END, result.stderr)
                        messagebox.showinfo("Success", f"Image saved and ATLC calculation completed!\nCheck the output panel for results.")
                    else:
                        self.output_text.insert(tk.END, "ATLC Error:\n")
                        self.output_text.insert(tk.END, "=" * 60 + "\n")
                        self.output_text.insert(tk.END, result.stderr if result.stderr else "Unknown error occurred")
                        messagebox.showwarning("ATLC Warning", "ATLC encountered an error. Check the output panel for details.")
                    
                    self.output_text.config(state=tk.DISABLED)
                    self.output_text.see(tk.END)  # Scroll to bottom
                        
                except subprocess.TimeoutExpired:
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, "\nATLC Error: Calculation timed out after 30 seconds\n")
                    self.output_text.config(state=tk.DISABLED)
                    messagebox.showwarning("ATLC Timeout", "ATLC timed out after 30 seconds")
                except FileNotFoundError:
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, "\nATLC Error: Command not found\n")
                    self.output_text.insert(tk.END, "Please ensure atlc is installed and in your PATH\n")
                    self.output_text.config(state=tk.DISABLED)
                    messagebox.showwarning("ATLC Not Found", "ATLC command not found. Please ensure atlc is installed.")
                except Exception as atlc_error:
                    self.output_text.config(state=tk.NORMAL)
                    self.output_text.insert(tk.END, f"\nATLC Error: {str(atlc_error)}\n")
                    self.output_text.config(state=tk.DISABLED)
                    messagebox.showwarning("ATLC Error", f"ATLC error: {str(atlc_error)}")
                    
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image:\n{str(e)}")


def main():
    root = tk.Tk()
    app = PCBTraceVisualizer(root)
    root.mainloop()


if __name__ == "__main__":
    main()