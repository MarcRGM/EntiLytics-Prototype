import sys
sys.dont_write_bytecode = True

import solara
from theme import (
    COLORS, FONTS, SPACING, RADIUS, SHADOWS, SIZES,
    BUTTON_STYLES, INPUT_STYLES, CARD_STYLES, LAYOUT_STYLES,
    MODAL_OVERLAY_STYLE
)

from state import current_user, current_role, current_view, is_checking_session
from components import SessionRestorer, LoginScreen, DashboardScreen, AdminPage


# MASTER PAGE (INJECTS CSS ONCE)
@solara.component
def Page():
    solara.Title("Entilytics - News Information Management System")

    # SEO Meta Tags
    solara.HTML(tag="meta", attributes={
        "name": "description",
        "content": "EntiLytics is a web-based news information management system that automatically extracts entities, ranks their importance, maps relationships, and generates entity-focused summaries from English online news articles using advanced NLP."
    })
    
    solara.HTML(tag="meta", attributes={
        "name": "keywords",
        "content": "news analysis, entity extraction, NLP, information management, news summarization, entity ranking, relationship mapping"
    })
    
    solara.HTML(tag="meta", attributes={
        "name": "author",
        "content": "EntiLytics"
    })
    
    solara.HTML(tag="meta", attributes={
        "property": "og:title",
        "content": "EntiLytics - News Information Management System"
    })
    
    solara.HTML(tag="meta", attributes={
        "property": "og:description",
        "content": "Understand news articles better with AI-powered entity extraction, ranking, and relationship mapping."
    })
    
    solara.HTML(tag="meta", attributes={
        "name": "viewport",
        "content": "width=device-width, initial-scale=1.0"
    })

    solara.HTML(tag="meta", attributes={
        "property": "og:type",
        "content": "website"
    })

    solara.HTML(tag="meta", attributes={
        "property": "og:image",
        "content": "data:image/png;base64,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"
    })

    solara.HTML(tag="meta", attributes={
        "http-equiv": "Set-Cookie",
        "content": "cross-site-cookie=1; SameSite=None; Secure"
    })

    with solara.Div(style={"display": "none"}):
        solara.HTML(tag="script", unsafe_innerHTML=f"""
            document.querySelectorAll("link[rel*='icon']").forEach(el => el.remove());
            var link = document.createElement('link');
            link.rel = 'icon';
            link.type = 'image/png';
            link.href = 'data:image/png;base64,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';
            document.head.appendChild(link);
        """)
    
    solara.Style(f"""
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500&display=swap');
                 
        /* FONT CLASSES */
        .space-mono-regular {{ font-family: {FONTS['mono_space']}; font-weight: 400; }}
        .space-mono-bold {{ font-family: {FONTS['mono_space']}; font-weight: 700; }}
        .roboto-mono-light {{ font-family: {FONTS['mono']}; font-weight: 300; }}
        .roboto-mono-regular {{ font-family: {FONTS['mono']}; font-weight: 400; }}
        .roboto-mono-medium {{ font-family: {FONTS['mono']}; font-weight: 500; }}
        
        /* BUTTONS */
        .push-button {{ 
            font-size: {FONTS['button_text']}!important; 
            border: none !important; 
            border-radius: {RADIUS['md']} !important; 
            padding: 10px 20px !important; 
            transition: none !important; 
            text-transform: none !important; 
            cursor: pointer; 
            position: relative; 
            top: 0; 
        }}
        .push-button:active {{ transform: translateY(6px) !important; box-shadow: none !important; }} 
        
        .action-btn {{ 
            background-color: {COLORS['primary']} !important; 
            color: {COLORS['text_white']} !important; 
            box-shadow: 0px 6px 0px 0px {COLORS['primary_dark']} !important; 
        }} 
        .toggle-btn, .google-auth {{ 
            background-color: {COLORS['bg_white']} !important; 
            color: {COLORS['text_primary']} !important; 
            box-shadow: 0px 6px 0px 0px {COLORS['border_light']} !important; 
        }}
        
        .red-btn {{ 
            background-color: {COLORS['error']} !important; 
            color: {COLORS['text_white']} !important; 
            box-shadow: 0px 6px 0px 0px {COLORS['error_dark']} !important; 
            border: 1px solid {COLORS['error_dark']} !important; 
        }}
                 
        /* TYPOGRAPHY */
        .login-title {{ font-size: {FONTS['login_title']} !important; }}
        .login-subtitle {{ font-size: {FONTS['login_subtitle']} !important; }}
        .login-btn {{ font-size: {FONTS['button_text']} !important; }}
        .login-terms {{ font-size: {FONTS['terms_text']} !important; }}
                 
        .admin-title {{ font-size: {FONTS['admin_title']} !important; }}
                 
        /* LAYOUT */
        .dashboard-container {{ 
            display: flex; 
            height: 100vh; 
            width: 100vw; 
            margin: 0; 
            overflow: hidden; 
            animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1); 
        }}
        @keyframes slideUp {{ 0% {{ transform: translateY(100vh); }} 100% {{ transform: translateY(0); }} }}
        
        .sidebar {{ 
            background: linear-gradient(180deg, {COLORS['primary_dark']} 0%, {COLORS['primary_darker']} 100%);
            color: {COLORS['text_white']}; 
            display: flex; 
            flex-direction: column; 
            justify-content: space-between; 
            transition: width 0.3s ease, padding 0.3s ease; 
            overflow: hidden; 
            white-space: nowrap; 
            z-index: 1000;
            box-shadow: 4px 0 16px {COLORS['shadow_dark']};
        }}
        .sidebar-open {{ width: 25%; padding: 20px 20px; transition: 0.3s; }}
        .sidebar-closed {{ width: 0%; padding: 0px; overflow: hidden; transition: 0.3s; }}
        .sidebar ::-webkit-scrollbar {{ width: 6px; }}
        .sidebar ::-webkit-scrollbar-track {{ background: rgba(255,255,255,0.05); border-radius: 10px; }}
        .sidebar ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.2); border-radius: 10px; }}
        .sidebar ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.3); }}

        .article-btn-text {{ 
            white-space: nowrap; 
            overflow: hidden !important; 
            font-size: {FONTS['body_small']} !important; 
        }}
        .article-btn-text .v-btn__content {{ 
            width: 100%; 
            display: block !important; 
            white-space: nowrap !important; 
            overflow: hidden !important; 
            text-overflow: ellipsis !important; 
            text-align: left !important; 
        }}
        
        .sidebar-title {{ font-size: {FONTS['sidebar_title']} !important; }}
        .sidebar-info {{ font-size: {FONTS['sidebar_info']} !important; }}
        .sidebar-logout {{ font-size: {FONTS['button_text']} !important; width: fit-content; }}
        
        .sidebar-logout-pad {{
            padding: clamp(0.5rem, 1vw + 0.3rem, 0.75rem) clamp(0.75rem, 1.5vw + 0.5rem, 1.125rem) !important;
        }}
        
        .logout-confirm-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            background-color: transparent;
        }}
        
        .workspace {{ 
            width: 75%; 
            height: 100vh; 
            background-color: {COLORS['bg_workspace']}; 
            flex-grow: 1; 
            padding: 40px 60px; 
            display: flex; 
            flex-direction: column; 
            align-items: center; 
            overflow-y: auto; 
        }}
        .form-container {{ 
            width: 60%; 
            min-width: 450px; 
            display: flex; 
            flex-direction: column; 
            gap: 20px; 
            margin-top: 20px; 
            padding: 10px; 
        }}
        
        .workspace-title-container {{
            text-align: center;
            width: 100%;
            margin-bottom: 20px;
            position: relative;
            padding-top: 50px;
        }}
        .workspace-title {{ font-size: {FONTS['workspace_title']} !important; color: {COLORS['primary']} }}
        .workspace-subtitle {{ font-size: {FONTS['workspace_subtitle']} !important; color: {COLORS['text_secondary']} }}
                 
        .form-action-row {{ 
            margin-top: clamp(1.25rem, 3vw, 1.875rem) !important; 
            gap: clamp(0.625rem, 2vw, 1.25rem) !important; 
            flex-wrap: wrap; 
        }}

        .form-btn-text {{ font-size: {FONTS['button_small']} !important; }}

        .menu-btn {{ 
            position: absolute !important; 
            top: 20px; 
            left: 20px;
            z-index: 100;
         }}
        .help-btn {{ 
            position: absolute !important; 
            top: 20px; 
            right: 20px;
            z-index: 100;
         }}
        
        .back-btn {{ 
            color: {COLORS['text_secondary']} !important; 
            background-color: {COLORS['bg_deep']} !important; 
            box-shadow: 0px 6px 0px 0px {COLORS['text_secondary']} !important; 
        }}
                 
        .input {{
            line-height: 28px;
            padding: 1rem;
            width: 100%;
            border: 2px solid transparent;
            border-radius: {RADIUS['md']};
            outline: none;
            background-color: {COLORS['bg_light']};
            box-shadow: 0 0.4rem {COLORS['border_default']};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
                 
        .input:hover {{
            transform: translateY(-6px);
            box-shadow: 0 0.8rem {COLORS['border_default']};
        }}

        /* RSS & INFO SECTIONS */
        .rss-info-header {{
            display: block;
            color: {COLORS['primary_dark']};
            margin-bottom: 0.75rem;
            font-size: {FONTS['info_header']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .rss-info-body {{
            color: {COLORS['text_primary']};
            line-height: 1.5;
            font-size: {FONTS['info_body']} !important;
            text-align: justify;
            hyphens: auto;
            overflow: hidden;
            cursor: help;
            padding-right: 40px;
        }}

        .rss-info-body b {{
            color: {COLORS['primary']};
        }}

        .info-container {{
            padding: 20px;
            border: 2px solid transparent;
            border-radius: {RADIUS['md']};
            outline: none;
            background-color: {COLORS['bg_light']};
            box-shadow: 0 0.4rem {COLORS['border_default']};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 35px;
        }}
                 
        .info-container:hover {{
            transform: translateY(-6px);
            box-shadow: 0 0.8rem {COLORS['border_default']};
        }}
                 
        .info-clamp-text {{
            display: -webkit-box;
            -webkit-box-orient: vertical; 
            overflow: hidden;
            font-family: {FONTS['mono']};
            text-align: justify;
            hyphens: auto;
            color: {COLORS['text_secondary']};
            line-height: 1.6;
            font-size: {FONTS['info_clamp']} !important;
        }}
                 
        .info-clamp-text:hover {{
            cursor: help;
        }}
                 
        .disclaimer-container {{
            padding: 20px;
            border: 2px solid transparent;
            border-radius: {RADIUS['md']};
            outline: none;
            background-color: {COLORS['primary']};
            box-shadow: 0 0.4rem {COLORS['primary_dark']};
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            margin-bottom: 20px;
        }}
                 
        .disclaimer-container:hover {{
            transform: translateY(-6px);
            box-shadow: 0 0.8rem {COLORS['primary_dark']};
        }}
                 
        .disclaimer-text {{
            font-size: {FONTS['disclaimer']} !important;
            font-family: {FONTS['mono']};
            text-align: justify;
            line-height: 1.5;
        }}
                 

                 
        .results-top-container {{
            padding: 20px;
            align-items: center; 
            display: flex; 
            justify-content: space-between;
            flex-direction: row;
        }}

        .mobile-close-btn {{ display: none !important; }}   
                       
        /* TOGGLE & CONTROLS */
        .segmented-control .v-btn-toggle {{ 
            background-color: {COLORS['bg_deep']} !important; 
            border-radius: {RADIUS['lg']} !important; 
            padding: 4px !important; 
            border-bottom: 6px solid {COLORS['text_secondary']} !important; 
        }}
        .segmented-control .v-btn {{ 
            border-radius: {RADIUS['lg']} !important; 
            text-transform: none !important; 
            font-family: {FONTS['mono']} !important; 
            letter-spacing: 0 !important; 
            border: none !important; 
            color: {COLORS['text_secondary']} !important; 
        }}
        .segmented-control .v-btn--active {{ 
            background-color: {COLORS['primary']} !important; 
            color: {COLORS['text_white']} !important; 
            box-shadow: 0 2px 4px {COLORS['shadow_medium']} !important; 
        }}
                          
        /* MODAL */
        .modal-overlay {{ 
            position: fixed;
            top: 0; 
            left: 0; 
            width: 100vw; 
            height: 100vh;
            background-color: {COLORS['bg_overlay']};
            z-index: 9999; 
            display: flex;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(4px); 
        }}
        .modal-content {{ 
            background-color: {COLORS['bg_white']}; 
            padding: 40px;
            border-radius: {RADIUS['lg']}; 
            width: 50%; 
            min-width: 400px; 
            max-width: 600px; 
            border: 2px solid {COLORS['primary']}; 
            box-shadow: {SHADOWS['lg']}; 
            display: flex; 
            flex-direction: column; 
            gap: 20px; 
            max-height: 80vh; 
            overflow-y: auto; 
            text-align: justify;
        }}
        
        /* RESPONSIVE GRID */
        .left-column-results {{ 
            width: calc(67% - 20px) !important; 
        }}
        .right-column-analytics {{ 
            width: 32% !important; 
        }}
                 
        @keyframes slideDown {{
            0% {{ transform: translateY(-100vh); }}
            100% {{ transform: translateY(0); }}
        }}
        
        /* RSS LIST */
        .rss-item-row {{ 
            transition: background-color 0.2s; 
            border-radius: {RADIUS['lg']}; 
            margin-bottom: 5px; 
        }} 
        .rss-item-row:hover {{ 
            background-color: rgba(28, 110, 164, 0.1) !important; 
        }}
        .analyze-btn {{ opacity: 0; transition: opacity 0.2s; }}
        .rss-item-row:hover .analyze-btn {{ opacity: 1; }}
                 
        /* UTILITIES */
        div[style*="bottom: 0px"][style*="position: absolute"] {{ display: none !important; }}
        
        /* RESPONSIVE BREAKPOINTS */
        @media (max-width: 1024px) {{ 
            .sidebar-open {{ width: 35%; }}
            .workspace {{ width: 65%; padding: 30px 40px; }}
            .form-container {{ width: 80%; min-width: unset; }}
            
            .analysis-grid {{ display: block !important; width: 100% !important; }}
            .relationship-map-container, 
            .notes-section-container {{
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                margin-bottom: 20px !important;
            }}
                 
            .left-column-results, 
            .right-column-analytics {{
                width: 100% !important;
                flex: 0 0 100% !important;
                max-width: 100% !important;
                margin-bottom: 20px !important;
            }}
        }}

        @media (max-width: 768px) {{
            .push-button {{
                font-size: {SIZES['button_sm']} !important;
                padding: {SIZES['button_padding_sm']} {SIZES['button_padding_sm_h']} !important;
            }}
            .form-btn-text {{
                font-size: {SIZES['button_sm']} !important;
            }}
            .sidebar-logout-pad {{
                padding: {SIZES['button_padding_sm']} {SIZES['button_padding_sm_h']} !important;
            }}
        }}
                 
        @media (max-width: 750px) {{
            .results-top-container {{
                flex-direction: column;
                padding-top: 20px;
                gap: 20px;
            }}
        }}
        
        @media (max-width: 600px) {{
            .mobile-close-btn {{ display: block !important; margin-bottom: 10px; }}
            .sidebar {{ position: fixed; top: 0; left: 0; height: 100vh; width: 100vw; z-index: 2000; transition: transform 0.3s ease; }}
            .sidebar-closed {{ transform: translateX(-100vw); width: 100vw; }}
            .sidebar-open {{ transform: translateX(0); width: 100vw; padding: 20px; }}
            .workspace {{ width: 100vw; padding: 16px 12px; }}
            .form-container {{ width: 100%; min-width: unset; }}
            .modal-content {{ width: 92%; min-width: unset; padding: 20px; }}
            
            .push-button {{ font-size: {FONTS['button_small']} !important; padding: 8px 12px !important; }}
            .form-btn-text {{ font-size: {FONTS['button_small']} !important; }}
            .login-title {{ font-size: {SIZES['display_md']} !important; }}
            .workspace-title {{ font-size: {SIZES['display_sm']} !important; }}
        }}

        @media (max-width: 480px) {{
            .push-button {{
                font-size: {SIZES['body_sm']} !important;
                padding: {SIZES['button_padding_sm']} {SIZES['button_padding_sm_h']} !important;
            }}
        }}
    """)

    SessionRestorer()
    
    print(f"DEBUG: checking={is_checking_session.value}, user={'LOGGED_IN' if current_user.value else 'NONE'}")
    
    if is_checking_session.value:
        with solara.Column(style={"min-height": "100vh", "justify-content": "center", "align-items": "center", "background-color": COLORS["bg_workspace"]}):
             solara.ProgressLinear(color=COLORS["primary"])
             solara.Text("Verifying Session...", classes=["roboto-mono-medium"], style={"margin-top": "20px", "color": COLORS["primary"]})
    
    if current_user.value is None:
        LoginScreen()
    else:
        if current_role.value == "admin":
            if current_view.value == "dashboard":
                DashboardScreen()
            else:
                AdminPage()
        else:
            DashboardScreen()