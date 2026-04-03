"""
Centralized theme configuration for EntiLytics
"""


# COLOR PALETTE
COLORS = {
    # Primary Blues
    "primary": "#1C6EA4",
    "primary_dark": "#113F67",
    "primary_darker": "#0d2a47",
    "primary_light": "#578FCA",
    "primary_lighter": "#3674B5",
    
    # Secondary Yellow
    "secondary": "#FADA7A",
    
    # Text Colors
    "text_primary": "#444444",
    "text_secondary": "#666666",
    "text_light": "#777777",
    "text_muted": "#888888",
    "text_white": "#FFFFFF",
    
    # Backgrounds
    "bg_white": "#FFFFFF",
    "bg_light": "#fdfdfd",
    "bg_lighter": "#fbfbfb",
    "bg_pale": "#f9f9f9",
    "bg_deep": "#f0f0f0",
    "bg_workspace": "#FADA7A",
    "bg_overlay": "rgba(28, 110, 164, 0.4)",
    
    # Status Colors
    "success": "#4CAF50",
    "error": "#CD5656",
    "error_dark": "#AF3E3E",
    "error_light": "#d9534f",
    "warning": "#FFC107",
    
    # Borders & Shadows
    "border_light": "#DDDDDD",
    "border_default": "#EEEEEE",
    "border_dark": "#DDD",
    "shadow_light": "rgba(0,0,0,0.05)",
    "shadow_medium": "rgba(0,0,0,0.1)",
    "shadow_dark": "rgba(0,0,0,0.15)",
    "shadow_darker": "rgba(0,0,0,0.2)",
}

# SIZING SYSTEM WITH CLAMPS
# Clamp format: clamp(min, preferred, max)
SIZES = {
    # Hero/Display Sizes
    "display_lg": "clamp(2.25rem, 7vw + 1rem, 4.5rem)",
    "display_md": "clamp(2rem, 4vw + 1rem, 3.5rem)",
    "display_sm": "clamp(1.75rem, 3vw + 1rem, 3rem)",
    
    # Heading Sizes
    "heading_xl": "clamp(1.5rem, 3vw + 0.5rem, 2.5rem)",
    "heading_lg": "clamp(1.25rem, 2.5vw + 0.5rem, 2rem)",
    "heading_md": "clamp(1.125rem, 2vw + 0.5rem, 1.75rem)",
    "heading_sm": "clamp(1rem, 1.5vw + 0.5rem, 1.5rem)",
    
    # Body Sizes
    "body_lg": "clamp(1rem, 0.975rem + 0.125vw, 1.125rem)",
    "body_md": "clamp(0.875rem, 0.85rem + 0.125vw, 1rem)",
    "body_sm": "clamp(0.75rem, 0.725rem + 0.125vw, 0.875rem)",
    "body_xs": "clamp(0.6875rem, 0.675rem + 0.0625vw, 0.75rem)",

    # Button Sizes (responsive)
    "button_padding_v": "clamp(0.5rem, 1vw + 0.25rem, 0.75rem)",
    "button_padding_h": "clamp(0.75rem, 1.5vw + 0.5rem, 1.125rem)",
    "button_padding_sm": "clamp(0.4rem, 0.8vw + 0.2rem, 0.6rem)",
    "button_padding_sm_h": "clamp(0.5rem, 1vw + 0.3rem, 0.8rem)",
    
    # Specialized Sizes
    "label": "clamp(0.875rem, 0.47vw + 0.7rem, 1rem)",
    "button": "clamp(0.875rem, 0.47vw + 0.7rem, 1rem)",
    "button_sm": "clamp(0.75rem, 2vw + 0.4rem, 1rem)",
    "button_responsive": "clamp(0.75rem, 1.5vw + 0.5rem, 1.125rem)",
    "subtitle": "clamp(0.875rem, 3vw + 0.5rem, 1.125rem)",
    "terms": "clamp(0.65rem, 1.8vw + 0.4rem, 0.75rem)",
    "info_header": "clamp(1rem, 1.5vw, 1.1rem)",
    "info_body": "clamp(13px, 1.1vw, 14px)",
}

# TYPOGRAPHY
FONTS = {
    # Font Families
    "mono": "'Roboto Mono', monospace",
    "mono_space": "'Space Mono', monospace",
    
    "login_title": SIZES["display_lg"],
    "admin_title": SIZES["display_md"],
    "workspace_title": SIZES["display_sm"],
    "section_title": SIZES["heading_sm"],
    
    "body_large": SIZES["body_lg"],
    "body_default": SIZES["body_md"],
    "body_small": SIZES["body_sm"],
    "body_xs": SIZES["body_xs"],
    
    "rss_title": SIZES["body_lg"],
    "rss_date": SIZES["body_sm"],
    "input_label": SIZES["label"],
    "button_text": SIZES["button"],
    "button_responsive": SIZES["button_responsive"],
    "button_small": SIZES["button_sm"],
    
    "info_header": SIZES["info_header"],
    "info_body": SIZES["info_body"],
    "info_clamp": SIZES["body_md"],
    "disclaimer": SIZES["body_md"],
    "sidebar_title": SIZES["heading_sm"],
    "sidebar_info": SIZES["body_md"],
    
    "login_subtitle": SIZES["subtitle"],
    "workspace_subtitle": SIZES["subtitle"],
    "terms_text": SIZES["terms"],
}

# SPACING
SPACING = {
    "xs": "4px",
    "sm": "8px",
    "md": "12px",
    "lg": "16px",
    "xl": "20px",
    "2xl": "24px",
    "3xl": "32px",
    "4xl": "40px",
    "5xl": "60px",
}

# BORDER RADIUS
RADIUS = {
    "none": "0px",
    "sm": "4px",
    "md": "8px",
    "lg": "12px",
    "full": "9999px",
}

# SHADOWS
SHADOWS = {
    "sm": "0 2px 4px " + COLORS["shadow_light"],
    "md": "0 4px 6px " + COLORS["shadow_light"],
    "lg": "0px 10px 30px " + COLORS["shadow_darker"],
    "push": "6px 6px 0px 0px",
}

# COMMON STYLE DICTIONARIES

# Buttons
BUTTON_STYLES = {
    "push_button": {
        "border": "none",
        "border_radius": RADIUS["md"],
        "padding": f"{SIZES['button_padding_v']} {SIZES['button_padding_h']}",
        "transition": "none",
        "text_transform": "none",
        "cursor": "pointer",
        "position": "relative",
        "top": "0",
        "font_size": SIZES["button"],
    },
    "push_button_sm": {
        "border": "none",
        "border_radius": RADIUS["md"],
        "padding": f"{SIZES['button_padding_sm']} {SIZES['button_padding_sm_h']}",
        "transition": "none",
        "text_transform": "none",
        "cursor": "pointer",
        "position": "relative",
        "top": "0",
        "font_size": SIZES["button_sm"],
    },
    "action_btn": {
        "background_color": COLORS["primary"],
        "color": COLORS["text_white"],
        "box_shadow": f"0px 6px 0px 0px {COLORS['primary_dark']}",
    },
    "toggle_btn": {
        "background_color": COLORS["bg_white"],
        "color": COLORS["text_primary"],
        "box_shadow": f"0px 6px 0px 0px {COLORS['border_light']}",
    },
    "red_btn": {
        "background_color": COLORS["error"],
        "color": COLORS["text_white"],
        "box_shadow": f"0px 6px 0px 0px {COLORS['error_dark']}",
        "border": f"1px solid {COLORS['error_dark']}",
    },
}

# Input Fields
INPUT_STYLES = {
    "default": {
        "line_height": "28px",
        "padding": "1rem",
        "width": "100%",
        "border": "2px solid transparent",
        "border_radius": RADIUS["md"],
        "outline": "none",
        "background_color": COLORS["bg_light"],
        "box_shadow": f"0 0.4rem {COLORS['border_default']}",
        "transition": "transform 0.2s ease, box-shadow 0.2s ease",
    },
    "hover": {
        "transform": "translateY(-6px)",
        "box_shadow": f"0 0.8rem {COLORS['border_default']}",
    },
}

# Cards & Containers
CARD_STYLES = {
    "info_container": {
        "background": COLORS["bg_lighter"],
        "padding": "20px",
        "border": f"6px solid {COLORS['primary_dark']}",
        "box_shadow": f"12px 12px 0 {COLORS['primary_dark']}",
        "margin_bottom": "35px",
        "transition": "transform 0.3s, box-shadow 0.3s",
    },
    "disclaimer_container": {
        "background": COLORS["primary"],
        "padding": "20px",
        "border": f"6px solid {COLORS['primary_dark']}",
        "box_shadow": f"12px 12px 0 {COLORS['primary_dark']}",
        "margin_bottom": "20px",
        "transition": "transform 0.3s, box-shadow 0.3s",
    },
    "modal_content": {
        "background_color": COLORS["bg_white"],
        "padding": "40px",
        "border_radius": RADIUS["lg"],
        "width": "50%",
        "min_width": "400px",
        "max_width": "600px",
        "border": f"2px solid {COLORS['primary']}",
        "box_shadow": SHADOWS["lg"],
        "display": "flex",
        "flex_direction": "column",
        "gap": "20px",
        "max_height": "80vh",
        "overflow_y": "auto",
        "text_align": "justify",
    },
}

# Layout
LAYOUT_STYLES = {
    "workspace": {
        "width": "75%",
        "height": "100vh",
        "background_color": COLORS["bg_workspace"],
        "flex_grow": "1",
        "padding": "40px 60px",
        "display": "flex",
        "flex_direction": "column",
        "align_items": "center",
        "overflow_y": "auto",
    },
    "form_container": {
        "width": "60%",
        "min_width": "450px",
        "display": "flex",
        "flex_direction": "column",
        "gap": "20px",
        "margin_top": "20px",
        "padding": "10px",
    },
    "sidebar_open": {
        "width": "25%",
        "padding": "20px 20px",
        "transition": "0.3s",
    },
    "sidebar_closed": {
        "width": "0%",
        "padding": "0px",
        "overflow": "hidden",
        "transition": "0.3s",
    },
}

# Modal
MODAL_OVERLAY_STYLE = {
    "position": "fixed",
    "top": "0",
    "left": "0",
    "width": "100vw",
    "height": "100vh",
    "background_color": COLORS["bg_overlay"],
    "z_index": "9999",
    "display": "flex",
    "justify_content": "center",
    "align_items": "center",
    "backdrop_filter": "blur(4px)",
}
