import sys
sys.dont_write_bytecode = True

import solara

from state import current_user, current_role, current_view, is_checking_session
from components import SessionRestorer, LoginScreen, DashboardScreen, AdminPage


# MASTER PAGE (INJECTS CSS ONCE)
@solara.component
def Page():
    solara.Title("Entilytics")
    with solara.Div(style={"display": "none"}):
        solara.HTML(tag="script", unsafe_innerHTML="""
            document.querySelectorAll("link[rel*='icon']").forEach(el => el.remove());
            var link = document.createElement('link');
            link.rel = 'icon';
            link.type = 'image/png';
            link.href = 'data:image/png;base64,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';
            document.head.appendChild(link);
        """)
    solara.Style("""
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@300;400;500&display=swap');
                 
        .space-mono-regular { font-family: "Space Mono", monospace; font-weight: 400; }
        .space-mono-bold { font-family: "Space Mono", monospace; font-weight: 700; }
        .roboto-mono-light { font-family: "Roboto Mono", monospace; font-weight: 300; }
        .roboto-mono-regular { font-family: "Roboto Mono", monospace; font-weight: 400; }
        .roboto-mono-medium { font-family: "Roboto Mono", monospace; font-weight: 500; }
        
        .push-button { border: none !important; border-radius: 8px !important; padding: 10px 20px !important; transition: none !important; text-transform: none !important; cursor: pointer; position: relative; top: 0; }
        .push-button:active { transform: translateY(6px) !important; box-shadow: none !important; } 
        
        .action-btn { background-color: #1C6EA4 !important; color: #FFFFFF !important; box-shadow: 0px 6px 0px 0px #113F67 !important; border: 1px solid #113F67 !important; }
        .toggle-btn, .google-auth { background-color: #FFFFFF !important; color: #444444 !important; box-shadow: 0px 6px 0px 0px #DDDDDD !important; border: 1px solid #DDDDDD !important; }
        
        .red-btn { background-color: #CD5656 !important; color: #FFFFFF !important; box-shadow: 0px 6px 0px 0px #AF3E3E !important; border: 1px solid #AF3E3E !important; }

        @keyframes slideUp { 0% { transform: translateY(100vh); } 100% { transform: translateY(0); } }
                 
        .login-title { font-size: clamp(2.25rem, 7vw + 1rem, 4.5rem) !important; }
        .login-subtitle { font-size: clamp(0.875rem, 3vw + 0.5rem, 1.125rem) !important; }
        .login-btn { font-size: clamp(0.875rem, 2.5vw + 0.5rem, 1rem) !important; }
        .login-terms { font-size: clamp(0.65rem, 1.8vw + 0.4rem, 0.75rem) !important; }
                 
        .dashboard-container { display: flex; height: 100vh; width: 100vw; margin: 0; overflow: hidden; animation: slideUp 0.8s cubic-bezier(0.16, 1, 0.3, 1); }
        .sidebar { background-color: #113F67; color: white; display: flex; flex-direction: column; justify-content: space-between; transition: width 0.3s ease, padding 0.3s ease; overflow: hidden; white-space: nowrap; z-index: 1000;}
        .sidebar-open { width: 25%; padding: 20px 20px; transition: 0.3s; }
        .sidebar-closed { width: 0%; padding: 0px; overflow: hidden; transition: 0.3s; }
        .sidebar ::-webkit-scrollbar { width: 5px; }
        .sidebar ::-webkit-scrollbar-track { background: transparent; }
        .sidebar ::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 10px; }
        .sidebar ::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.4); }   
        
        .workspace { width: 75%; height: 100vh; background-color: #FADA7A; flex-grow: 1; padding: 40px 60px; display: flex; flex-direction: column; align-items: center; overflow-y: auto; }
        .form-container { width: 60%; min-width: 450px; display: flex; flex-direction: column; gap: 15px; margin-top: 20px; padding: 10px; }
        
        .workspace-title {
            font-size: clamp(2rem, 4vw + 1rem, 3rem) !important; /* Scales from 32px to 48px */
        }
        
        .workspace-subtitle {
            font-size: clamp(0.875rem, 2vw + 0.5rem, 1.125rem) !important; /* Scales from 14px to 18px */
        }
                 
        .form-action-row {
            margin-top: clamp(1.25rem, 3vw, 1.875rem) !important;
            gap: clamp(0.625rem, 2vw, 1.25rem) !important;
            flex-wrap: wrap;
        }

        .form-btn-text {
            font-size: clamp(0.75rem, 2vw + 0.4rem, 1rem) !important;
        }

        .menu-btn { position: absolute !important; top: 30px; left: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 1.75rem !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .menu-btn:hover { color: #578FCA !important; }
                 
        .help-btn { position: absolute !important; top: 30px; right: 30px; background-color: transparent !important; color: #1C6EA4 !important; font-size: 1.75rem !important; min-width: 0 !important; padding: 0 !important; box-shadow: none !important; }
        .help-btn:hover { color: #578FCA !important; }

        /* Saved articles */
        .article-btn-text { white-space: nowrap; overflow: hidden !important; font-size: clamp(0.75rem, 0.56vw + 0.54rem, 0.9rem) !important; }
        .article-btn-text .v-btn__content { width: 100%; display: block !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important; text-align: left !important; }
        
        /* Responsive Sidebar Text using clamp() */
        .sidebar-title { 
            font-size: clamp(1rem, 0.75vw + 0.72rem, 1.2rem) !important; 
        }
        .sidebar-info { 
            font-size: clamp(0.75rem, 0.47vw + 0.7rem, 1rem) !important; 
        }
        .sidebar-logout { 
            font-size: clamp(0.875rem, 0.47vw + 0.7rem, 1rem) !important; 
        }    
                 
        .sidebar-logout-pad {
            padding: clamp(0.1rem, 0.2vw + 0.05rem, 0.15rem) clamp(0.4rem, 0.5vw + 0.3rem, 0.625rem) !important;
        }
                 
        .logout-confirm-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 10px;
            background-color: transparent;
        }
                 
        .info-clamp-text {
            display: -webkit-box;
            -webkit-box-orient: vertical; 
            overflow: hidden;
            font-family: 'Roboto Mono', monospace;
            text-align: justify;
            hyphens: auto;
            color: #555;
            line-height: 1.6;
            font-size: clamp(10px, 1.1vw, 11.5px) !important;
        }
                 
        .info-clamp-text:hover {
            cursor: help;
        }
                 
        .disclaimer-text {
            font-size: clamp(10px, 1.1vw, 11px) !important;
            font-family: 'Roboto Mono', monospace;
            text-align: justify;
            line-height: 1.6;
        }

        /* Hidden on desktop, shown on mobile */
        .mobile-close-btn { display: none !important; }   
                       
        /* Toggle Button */
        .segmented-control .v-btn-toggle { background-color: #f0f0f0 !important; border-radius: 12px !important; padding: 4px !important; border: none !important; }
        .segmented-control .v-btn { border-radius: 12px !important; text-transform: none !important; font-family: 'Roboto Mono', monospace !important; letter-spacing: 0 !important; border: none !important; color: #666 !important; }
        .segmented-control .v-btn--active { background-color: #3674B5 !important; color: white !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; }
                 
        /* Custom Modal CSS */
        .modal-overlay { position: fixed;top: 0; left: 0; width: 100vw; height: 100vh;background-color: rgba(28, 110, 164, 0.4); /* dark blue with transparency */z-index: 9999; /* Force to the front */display: flex;justify-content: center;align-items: center;backdrop-filter: blur(4px); /* frosted glass effect */}
        .modal-content { background-color: #FFFFFF; padding: 40px;border-radius: 12px; width: 50%; min-width: 400px; max-width: 600px; border: 2px solid #1C6EA4; box-shadow: 0px 10px 30px rgba(0,0,0,0.2); display: flex; flex-direction: column; gap: 20px; max-height: 80vh; overflow-y: auto;}
        
        /* Using calc to account for the 20px gap */
        .left-column-results { 
            width: calc(67% - 20px) !important; 
        }
        .right-column-analytics { 
            width: 32% !important; 
        }
        
        /* RSS List Hover Effects */
        .rss-item-row { transition: background-color 0.2s; border-radius: 12px; margin-bottom: 5px; } .rss-item-row:hover { background-color: rgba(28, 110, 164, 0.1) !important; }
        .analyze-btn { opacity: 0; transition: opacity 0.2s; }
        .rss-item-row:hover .analyze-btn { opacity: 1; }
                 
        /* Remove solara footer*/
        div[style*="bottom: 0px"][style*="position: absolute"] { display: none !important; }
        
        /* TABLET BEHAVIOR */
        @media (max-width: 1024px) { 
            .sidebar-open { width: 35%; }
            
            /* Adjust workspace to take up the remaining space */
            .workspace { width: 65%; padding: 30px 40px; }
            
            /* Make the form container wider to fit the smaller workspace */
            .form-container { width: 80%; min-width: unset; }
            
            .sidebar-open { width: 35%; }
                 
            .workspace { width: 65%; padding: 30px 40px; }
            .form-container { width: 80%; min-width: unset; }
            
            /* Stack the row into a column */
            .analysis-grid {
                display: block !important;
                width: 100% !important;
            }

            /* Force sections to full width */
            .relationship-map-container, 
            .notes-section-container {
                display: block !important;
                width: 100% !important;
                max-width: 100% !important;
                margin-bottom: 20px !important;
            }
                 
            .left-column-results, 
            .right-column-analytics {
                width: 100% !important;
                flex: 0 0 100% !important;
                max-width: 100% !important;
                margin-bottom: 20px !important;
            }
        }
        
        /* MOBILE BEHAVIOR */
        @media (max-width: 600px) {
            /* Show close button inside sidebar */
            .mobile-close-btn { display: block !important; margin-bottom: 10px; }
                 
            /* Sidebar covers full screen */
            .sidebar { position: fixed; top: 0; left: 0; height: 100vh; width: 100vw; z-index: 2000; transition: transform 0.3s ease; }
            .sidebar-closed { transform: translateX(-100vw); width: 100vw; }
            .sidebar-open { transform: translateX(0); width: 100vw; padding: 20px; }
            
            /* Workspace takes full width, reduced padding */
            .workspace { width: 100vw; padding: 16px 12px; }

            /* Form fills screen, no min-width overflow */
            .form-container { width: 100%; min-width: unset; }

            /* Modal fits mobile screen */
            .modal-content { width: 92%; min-width: unset; padding: 20px; }
            
            
        }
    """)

    SessionRestorer()
    
    print(f"DEBUG: checking={is_checking_session.value}, user={'LOGGED_IN' if current_user.value else 'NONE'}")
    
    # TRAFFIC CONTROLLER WITH LOADING GATE
    if current_user.value is None:
        LoginScreen()
    else:
        # Redirect based on role
        if current_role.value == "admin":
            # If admin has clicked 'View Dashboard', show dashboard; else show Admin Console
            if current_view.value == "dashboard":
                DashboardScreen()
            else:
                AdminPage()
        else:
            DashboardScreen()