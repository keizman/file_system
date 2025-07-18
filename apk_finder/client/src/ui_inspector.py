"""
UI Inspector for APK Finder Client
Provides a way to inspect UI elements and their properties
"""

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                           QTreeWidgetItem, QTextEdit, QSplitter, QPushButton,
                           QLabel, QWidget, QFrame, QApplication)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QPalette, QColor, QCursor
import qtawesome as qta
from ui.styles import get_complete_style, get_theme_colors


class UIInspector(QDialog):
    """UI Inspector dialog for debugging UI elements"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("UI Inspector")
        self.setModal(False)
        self.resize(800, 600)
        
        # Apply theme
        self.apply_theme()
        
        # Inspector state
        self.inspection_mode = False
        self.highlighted_widget = None
        self.original_stylesheet = {}
        
        self.init_ui()
        
    def apply_theme(self):
        """Apply current theme to inspector"""
        from config import ClientConfig
        theme = ClientConfig.get_setting("theme", "Light")
        self.setStyleSheet(get_complete_style(theme))
        
    def init_ui(self):
        """Initialize the inspector UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("UI Inspector")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Inspect button
        self.inspect_btn = QPushButton("Start Inspection")
        self.inspect_btn.setIcon(qta.icon('mdi.target', color='white'))
        self.inspect_btn.clicked.connect(self.toggle_inspection)
        header_layout.addWidget(self.inspect_btn)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setIcon(qta.icon('mdi.refresh', color='white'))
        self.refresh_btn.clicked.connect(self.refresh_tree)
        header_layout.addWidget(self.refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Widget tree
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Widget Hierarchy")
        self.tree_widget.itemClicked.connect(self.on_item_clicked)
        self.tree_widget.setMinimumWidth(300)
        splitter.addWidget(self.tree_widget)
        
        # Properties panel
        props_widget = QWidget()
        props_layout = QVBoxLayout(props_widget)
        
        props_label = QLabel("Properties")
        props_label.setStyleSheet("font-size: 14px; font-weight: bold; margin: 5px;")
        props_layout.addWidget(props_label)
        
        self.props_text = QTextEdit()
        self.props_text.setReadOnly(True)
        self.props_text.setFont(self.font())
        props_layout.addWidget(self.props_text)
        
        splitter.addWidget(props_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 400])
        
        layout.addWidget(splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: rgba(0,0,0,0.1);")
        layout.addWidget(self.status_label)
        
        # Populate tree initially
        self.refresh_tree()
        
    def refresh_tree(self):
        """Refresh the widget tree"""
        self.tree_widget.clear()
        
        if self.parent():
            root_item = QTreeWidgetItem(self.tree_widget)
            root_item.setText(0, f"{self.parent().__class__.__name__}")
            root_item.setData(0, Qt.UserRole, self.parent())
            
            self.populate_tree(self.parent(), root_item)
            self.tree_widget.expandAll()
            
        self.status_label.setText("Tree refreshed")
        
    def populate_tree(self, widget, parent_item):
        """Recursively populate the widget tree"""
        children = widget.findChildren(QWidget)
        direct_children = [child for child in children if child.parent() == widget]
        
        for child in direct_children:
            item = QTreeWidgetItem(parent_item)
            
            # Widget info
            class_name = child.__class__.__name__
            object_name = child.objectName() or "unnamed"
            text = child.text() if hasattr(child, 'text') and child.text() else ""
            
            display_text = f"{class_name}"
            if object_name != "unnamed":
                display_text += f" ({object_name})"
            if text:
                display_text += f' "{text[:20]}..."' if len(text) > 20 else f' "{text}"'
                
            item.setText(0, display_text)
            item.setData(0, Qt.UserRole, child)
            
            # Recursively add children
            self.populate_tree(child, item)
            
    def on_item_clicked(self, item):
        """Handle tree item click"""
        widget = item.data(0, Qt.UserRole)
        if widget:
            self.show_widget_properties(widget)
            self.highlight_widget(widget)
            
    def show_widget_properties(self, widget):
        """Show properties of the selected widget"""
        props = []
        
        # Basic properties
        props.append(f"Class: {widget.__class__.__name__}")
        props.append(f"Object Name: {widget.objectName() or 'None'}")
        props.append(f"Visible: {widget.isVisible()}")
        props.append(f"Enabled: {widget.isEnabled()}")
        props.append(f"Geometry: {widget.geometry()}")
        props.append(f"Size: {widget.size()}")
        props.append(f"Minimum Size: {widget.minimumSize()}")
        props.append(f"Maximum Size: {widget.maximumSize()}")
        
        # Text properties
        if hasattr(widget, 'text'):
            props.append(f"Text: {widget.text()}")
        if hasattr(widget, 'placeholderText'):
            props.append(f"Placeholder: {widget.placeholderText()}")
            
        # Style properties
        props.append(f"StyleSheet: {widget.styleSheet()[:200]}..." if len(widget.styleSheet()) > 200 else f"StyleSheet: {widget.styleSheet()}")
        
        # Parent/children info
        props.append(f"Parent: {widget.parent().__class__.__name__ if widget.parent() else 'None'}")
        children = widget.findChildren(QWidget)
        direct_children = [child for child in children if child.parent() == widget]
        props.append(f"Direct Children: {len(direct_children)}")
        
        # Layout info
        if widget.layout():
            props.append(f"Layout: {widget.layout().__class__.__name__}")
            
        # Window flags
        if widget.isWindow():
            props.append(f"Window Flags: {widget.windowFlags()}")
            
        # Background color
        palette = widget.palette()
        bg_color = palette.color(QPalette.Window)
        props.append(f"Background Color: {bg_color.name()}")
        
        # Font info
        font = widget.font()
        props.append(f"Font: {font.family()}, {font.pointSize()}pt")
        
        self.props_text.setPlainText("\\n".join(props))
        
    def highlight_widget(self, widget):
        """Highlight the selected widget"""
        # Remove previous highlight
        if self.highlighted_widget:
            self.remove_highlight(self.highlighted_widget)
            
        # Add new highlight
        self.highlighted_widget = widget
        self.add_highlight(widget)
        
        # Auto-remove highlight after 3 seconds
        QTimer.singleShot(3000, lambda: self.remove_highlight(widget))
        
    def add_highlight(self, widget):
        """Add highlight to widget"""
        if widget not in self.original_stylesheet:
            self.original_stylesheet[widget] = widget.styleSheet()
            
        highlight_style = """
        border: 3px solid #FF0000 !important;
        background-color: rgba(255, 0, 0, 0.1) !important;
        """
        
        current_style = self.original_stylesheet[widget]
        widget.setStyleSheet(current_style + highlight_style)
        
    def remove_highlight(self, widget):
        """Remove highlight from widget"""
        if widget in self.original_stylesheet:
            widget.setStyleSheet(self.original_stylesheet[widget])
            del self.original_stylesheet[widget]
            
    def toggle_inspection(self):
        """Toggle inspection mode"""
        self.inspection_mode = not self.inspection_mode
        
        if self.inspection_mode:
            self.inspect_btn.setText("Stop Inspection")
            self.inspect_btn.setIcon(qta.icon('mdi.stop', color='white'))
            self.status_label.setText("Inspection mode ON - Click on any widget to inspect")
            
            # Install event filter on parent window
            if self.parent():
                self.parent().installEventFilter(self)
                
        else:
            self.inspect_btn.setText("Start Inspection")
            self.inspect_btn.setIcon(qta.icon('mdi.target', color='white'))
            self.status_label.setText("Inspection mode OFF")
            
            # Remove event filter
            if self.parent():
                self.parent().removeEventFilter(self)
                
    def eventFilter(self, obj, event):
        """Event filter for inspection mode"""
        if self.inspection_mode and event.type() == event.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                # Get widget under cursor
                pos = QCursor.pos()
                widget = QApplication.widgetAt(pos)
                
                if widget and widget != self:
                    # Find the widget in the tree and select it
                    self.find_and_select_widget(widget)
                    return True
                    
        return super().eventFilter(obj, event)
        
    def find_and_select_widget(self, target_widget):
        """Find and select a widget in the tree"""
        def search_item(item):
            widget = item.data(0, Qt.UserRole)
            if widget == target_widget:
                self.tree_widget.setCurrentItem(item)
                self.on_item_clicked(item)
                return True
                
            for i in range(item.childCount()):
                if search_item(item.child(i)):
                    return True
            return False
            
        root = self.tree_widget.invisibleRootItem()
        for i in range(root.childCount()):
            if search_item(root.child(i)):
                break
                
    def closeEvent(self, event):
        """Handle close event"""
        # Clean up highlights
        for widget in list(self.original_stylesheet.keys()):
            self.remove_highlight(widget)
            
        # Remove event filter
        if self.parent():
            self.parent().removeEventFilter(self)
            
        event.accept()