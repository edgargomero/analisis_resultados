# 🚀 Streamlit Cloud Deployment Guide for CEAPSI PCF

## 📋 Prerequisites

1. **GitHub Repository**: Your code must be in a public or private GitHub repository
2. **Streamlit Cloud Account**: Sign up at [streamlit.io/cloud](https://streamlit.io/cloud)
3. **Requirements File**: `requirements.txt` with all dependencies

## 🏗️ Project Structure for Streamlit Cloud

```
analisis_resultados/
└── pcf_scripts/                    # Main app directory
    ├── app.py                      # ⭐ MAIN FILE (Entry point)
    ├── requirements.txt            # Dependencies
    ├── .streamlit/                 # Streamlit configuration
    │   ├── config.toml            # App configuration
    │   └── secrets.toml           # Secrets (NOT in repo)
    ├── src/                       # Source code modules
    │   ├── api/                   # API integrations
    │   ├── auth/                  # Authentication
    │   ├── core/                  # Core functionality
    │   ├── models/                # ML models
    │   ├── services/              # Business logic
    │   ├── ui/                    # UI components
    │   └── utils/                 # Utilities
    ├── assets/                    # Static assets
    │   └── data/                  # Data files
    └── docs/                      # Documentation
```

## 🔧 Streamlit Cloud Configuration

### 1. **Main App Path**
When deploying to Streamlit Cloud, specify:
- **Main file path**: `pcf_scripts/app.py`

### 2. **Python Version**
Streamlit Cloud uses Python 3.9 by default. To specify a version, create:

```toml
# runtime.txt
python-3.9
```

### 3. **Secrets Management**

In Streamlit Cloud dashboard:
1. Go to your app settings
2. Click on "Secrets"
3. Add your secrets in TOML format:

```toml
# Paste contents from .streamlit/secrets.toml.example
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_KEY = "your-service-role-key"
SUPABASE_ANON_KEY = "your-anon-key"

RESERVO_API_URL = "https://api.reservo.cl"
RESERVO_API_KEY = "your-api-key"
RESERVO_CLIENT_ID = "your-client-id"
```

## 📝 Step-by-Step Deployment

### 1. **Prepare Your Repository**

```bash
# Ensure app.py is in pcf_scripts root
ls pcf_scripts/app.py

# Check requirements.txt
cat pcf_scripts/requirements.txt

# Verify .streamlit/config.toml exists
ls pcf_scripts/.streamlit/config.toml
```

### 2. **Deploy on Streamlit Cloud**

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click "New app"
3. Fill in:
   - **Repository**: `edgargomero/analisis_resultados`
   - **Branch**: `main`
   - **Main file path**: `pcf_scripts/app.py`
4. Click "Deploy"

### 3. **Configure Secrets**

After deployment:
1. Click on "Settings" → "Secrets"
2. Copy contents from `.streamlit/secrets.toml.example`
3. Replace with your actual values
4. Save

## 🐛 Common Issues and Solutions

### Issue: "Main module does not exist"
**Solution**: Ensure `app.py` is in the path specified:
- Correct: `pcf_scripts/app.py`
- Wrong: `pcf_scripts/src/app.py`

### Issue: Import errors
**Solution**: Update imports in `app.py`:
```python
# Add src to path
current_dir = Path(__file__).parent.absolute()
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
```

### Issue: Missing dependencies
**Solution**: Ensure all imports are in `requirements.txt`:
```txt
streamlit>=1.32.0
pandas>=2.0.3
supabase==2.8.0
python-dotenv==1.0.1
```

### Issue: Secrets not loading
**Solution**: Access secrets correctly:
```python
# Correct way in Streamlit Cloud
import streamlit as st
supabase_url = st.secrets["SUPABASE_URL"]

# NOT this way
from dotenv import load_dotenv
load_dotenv()  # This won't work in Streamlit Cloud
```

## 🔒 Security Best Practices

1. **Never commit secrets.toml** to version control
2. Use **service role keys** only for backend operations
3. Enable **Row Level Security** in Supabase
4. Use **environment checks**:
   ```python
   if st.secrets.get("ENVIRONMENT") == "production":
       # Production settings
   ```

## 📊 Monitoring and Logs

### View Logs
1. Go to your app on Streamlit Cloud
2. Click "Manage app" → "Logs"
3. Monitor for errors and warnings

### Debug Mode
Add to your app for development:
```python
if st.secrets.get("DEBUG_MODE", False):
    st.sidebar.write("Debug Info")
    st.sidebar.write(f"Python: {sys.version}")
    st.sidebar.write(f"Streamlit: {st.__version__}")
```

## 🔄 Continuous Deployment

Streamlit Cloud automatically redeploys when you:
1. Push changes to the main branch
2. Update secrets in the dashboard
3. Manually trigger redeployment

## 📈 Performance Optimization

1. **Cache data loading**:
   ```python
   @st.cache_data
   def load_data():
       return pd.read_csv("data.csv")
   ```

2. **Use session state**:
   ```python
   if 'data' not in st.session_state:
       st.session_state.data = load_data()
   ```

3. **Limit resource usage**:
   - Max 1GB RAM for free tier
   - Consider data sampling for large datasets

## 🎯 Deployment Checklist

- [ ] `app.py` is in `pcf_scripts/` root
- [ ] `requirements.txt` includes all dependencies
- [ ] `.streamlit/config.toml` is configured
- [ ] Secrets are added to Streamlit Cloud dashboard
- [ ] Imports reference `src/` directory correctly
- [ ] Data files are in `assets/data/`
- [ ] No hardcoded secrets in code
- [ ] Error handling for missing dependencies

## 🆘 Support

- **Streamlit Forums**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **Documentation**: [docs.streamlit.io](https://docs.streamlit.io)
- **CEAPSI Support**: soporte@ceapsi.cl

---

**Last Updated**: 2025-01-23  
**Version**: 1.0.0  
**Maintainer**: CEAPSI DevOps Team