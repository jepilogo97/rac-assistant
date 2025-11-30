"""
Estilos CSS para la aplicación
"""
import streamlit as st

def apply_custom_css():
    """Aplicar estilos CSS modernos basados en el diseño React con Tailwind"""
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    /* ───────── Design System Variables (basados en React app) ───────── */
    :root {
        --background: hsl(220, 17%, 97%);
        --foreground: hsl(220, 13%, 13%);
        --card: hsl(0, 0%, 100%);
        --card-foreground: hsl(220, 13%, 13%);
        --primary: hsl(221, 71%, 54%);
        --primary-foreground: hsl(0, 0%, 100%);
        --primary-glow: hsl(221, 71%, 64%);
        --secondary: hsl(220, 17%, 95%);
        --secondary-foreground: hsl(220, 13%, 13%);
        --muted: hsl(220, 14%, 96%);
        --muted-foreground: hsl(220, 9%, 46%);
        --accent: hsl(221, 83%, 53%);
        --accent-foreground: hsl(0, 0%, 100%);
        --success: hsl(142, 76%, 36%);
        --success-foreground: hsl(0, 0%, 100%);
        --warning: hsl(38, 92%, 50%);
        --warning-foreground: hsl(0, 0%, 100%);
        --destructive: hsl(0, 84%, 60%);
        --destructive-foreground: hsl(0, 0%, 100%);
        --border: hsl(220, 13%, 91%);
        --input: hsl(220, 13%, 91%);
        --ring: hsl(221, 71%, 54%);
        --radius: 0.75rem;
    }

    /* ───────── Global Reset & Typography ───────── */
    .stApp {
        background-color: var(--background);
        font-family: 'Inter', sans-serif;
        color: var(--foreground);
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.025em;
        color: var(--foreground);
    }

    /* ───────── Cards & Containers ───────── */
    .stCard {
        background-color: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        padding: 1.5rem;
        transition: all 0.2s ease-in-out;
    }
    
    .stCard:hover {
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        border-color: var(--primary-glow);
    }

    /* ───────── Buttons (Primary & Secondary) ───────── */
    .stButton > button {
        border-radius: var(--radius) !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
        border: 1px solid transparent !important;
    }

    /* Primary Button - Blue Theme (Override Streamlit's red default) */
    .stButton > button[kind="primary"],
    .stButton > button:not([kind]),
    button[kind="primary"],
    .stButton button {
        background-color: #3b82f6 !important;
        color: white !important;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1) !important;
    }
    
    .stButton > button[kind="primary"]:hover,
    .stButton > button:not([kind]):hover,
    button[kind="primary"]:hover,
    .stButton button:hover {
        background-color: #2563eb !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1) !important;
    }

    /* Secondary Button */
    .stButton > button[kind="secondary"] {
        background-color: var(--secondary) !important;
        color: var(--secondary-foreground) !important;
        border: 1px solid var(--border) !important;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: var(--muted) !important;
        color: var(--foreground) !important;
    }

    /* ───────── Inputs & Selects ───────── */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > div {
        border-radius: var(--radius);
        border-color: var(--input);
        background-color: var(--card);
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > div:focus-within {
        border-color: var(--ring);
        box-shadow: 0 0 0 2px var(--background), 0 0 0 4px var(--ring);
    }

    /* ───────── Metrics & Stats ───────── */
    [data-testid="stMetricValue"] {
        font-weight: 700;
        color: var(--primary);
    }
    
    [data-testid="stMetricLabel"] {
        font-weight: 500;
        color: var(--muted-foreground);
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.05em;
    }

    /* ───────── Dataframes & Tables ───────── */
    .stDataFrame {
        border: 1px solid var(--border);
        border-radius: var(--radius);
        overflow: hidden;
    }
    
    /* ───────── Custom Components ───────── */
    .feature-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1.5rem;
        height: 100%;
        transition: all 0.3s ease;
    }
    
    .feature-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
        border-color: var(--primary);
    }

    .step-indicator {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding: 0.75rem;
        background: var(--secondary);
        border-radius: var(--radius);
        border: 1px solid var(--border);
    }
    
    .step-number {
        background: var(--primary);
        color: white;
        width: 2rem;
        height: 2rem;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.875rem;
    }

    /* ───────── Animations ───────── */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .animate-fade-in {
        animation: fadeIn 0.5s ease-out forwards;
    }
    
    /* ───────── Sidebar ───────── */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid var(--border);
    }
    
    </style>
    """, unsafe_allow_html=True)

