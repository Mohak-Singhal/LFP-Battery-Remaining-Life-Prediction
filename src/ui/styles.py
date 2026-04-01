import streamlit as st

def inject_styles():
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(252,191,73,0.22), transparent 28%),
                radial-gradient(circle at top right, rgba(42,157,143,0.18), transparent 26%),
                linear-gradient(180deg, #fffaf1 0%, #f5f1e8 45%, #eef3f6 100%);
            color: #14213d;
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1320px;
        }
        h1, h2, h3 {
            font-family: Georgia, "Times New Roman", serif !important;
            color: #0f172a;
            letter-spacing: -0.02em;
        }
        .hero-shell {
            background: linear-gradient(135deg, rgba(0,48,73,0.96), rgba(20,33,61,0.92));
            border-radius: 26px;
            padding: 28px 30px;
            box-shadow: 0 20px 60px rgba(20, 33, 61, 0.18);
            margin-bottom: 1.2rem;
            color: #fdfaf3;
        }
        .hero-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #fcbf49;
            margin-bottom: 0.4rem;
            font-weight: 700;
        }
        .hero-title {
            font-size: 2.4rem;
            font-weight: 700;
            line-height: 1.05;
            margin-bottom: 0.4rem;
        }
        .hero-subtitle {
            max-width: 760px;
            color: rgba(255,255,255,0.78);
            font-size: 1rem;
        }
        .hero-card {
            background: rgba(255,255,255,0.82);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255,255,255,0.55);
            border-radius: 22px;
            padding: 18px 18px 16px 18px;
            box-shadow: 0 14px 34px rgba(20,33,61,0.08);
            min-height: 132px;
        }
        .hero-label {
            color: #5f6c7b;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.6rem;
        }
        .hero-value {
            color: #0f172a;
            font-size: 2rem;
            line-height: 1;
            font-weight: 800;
            margin-bottom: 0.55rem;
        }
        .hero-caption {
            color: #5f6c7b;
            font-size: 0.95rem;
        }
        .section-shell {
            background: rgba(255,255,255,0.72);
            border: 1px solid rgba(255,255,255,0.65);
            border-radius: 24px;
            padding: 16px 18px 18px 18px;
            box-shadow: 0 10px 28px rgba(20,33,61,0.06);
            margin-bottom: 1rem;
        }
        .mini-note {
            color: #54606f;
            font-size: 0.92rem;
            margin-top: -0.35rem;
            margin-bottom: 0.8rem;
        }
        div[data-testid="stMetric"] {
            background: rgba(255,255,255,0.7);
            border-radius: 18px;
            border: 1px solid rgba(255,255,255,0.55);
            padding: 12px 14px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
