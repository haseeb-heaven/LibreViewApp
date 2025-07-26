# streamlit_app.py
"""
Streamlit application for LibreView glucose data analysis using multiple AI models via LiteLLM.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import pandas as pd
import json
import xml.etree.ElementTree as ET
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv
import litellm
from libreapp.clients.libre_view import LibreCGMClient, ApiConfig
from libreapp.utils.data_masking import DefaultDataMasker
from libreapp.utils.logger import setup_logger

# Set up loggers
console_log, file_log = setup_logger()

class EnvironmentLoader:
    def __init__(self):
        self.console_log = console_log
        self.file_log = file_log

    def load_defaults(self) -> dict:
        self.file_log.debug("Loading environment variables from .env file")
        load_dotenv()

        return {
            "libre_email": os.getenv("LIBREVIEW_EMAIL", ""),
            "libre_password": os.getenv("LIBREVIEW_PASSWORD", ""),
            "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "gemini_api_key": os.getenv("GEMINI_API_KEY", ""),
            "cohere_api_key": os.getenv("COHERE_API_KEY", ""),
            "replicate_api_key": os.getenv("REPLICATE_API_KEY", ""),
            "libre_version": os.getenv("LIBRE_VERSION", "4.7"),
            "libre_product": os.getenv("LIBRE_PRODUCT", "llu.ios"),
            "default_model": os.getenv("DEFAULT_MODEL", "gpt-4")
        }

class LibreClientManager:
    def __init__(self, email: str, password: str, version: str, product: str):
        self.email = email
        self.password = password
        self.version = version
        self.product = product
        self.client: Optional[LibreCGMClient] = None
        self.connections: List[Dict[str, Any]] = []

    def connect(self) -> bool:
        try:
            config = ApiConfig(version=self.version, product=self.product)
            self.client = LibreCGMClient(
                email=self.email,
                password=self.password,
                config=config,
                data_masker=DefaultDataMasker()
            )
            
            auth_data = self.client.authenticate()
            if auth_data.get('status') != 0:
                st.toast(f"Authentication failed with status: {auth_data.get('status')}", icon="❌")
                file_log.error(f"Authentication failed with status: {auth_data.get('status')}")
                return False
                
            connections_data = self.client.list_connections()
            self.connections = connections_data.get('data', [])
            file_log.info("Successfully connected to LibreView")
            return True
        except Exception as connection_error:
            st.toast(f"Failed to connect to LibreView: {str(connection_error)}", icon="❌")
            file_log.error(f"Failed to connect to LibreView: {str(connection_error)}")
            return False

    def get_patient_data(self, patient_id: str) -> Optional[List[Dict[str, Any]]]:
        try:
            if not self.client:
                return None
            graph_data = self.client.get_patient_graph(patient_id)
            data = graph_data.get('data', {})
            return data.get('graphData', [])
        except Exception as data_error:
            st.toast(f"Failed to fetch glucose  {str(data_error)}", icon="❌")
            file_log.error(f"Failed to fetch glucose data for patient {patient_id}: {str(data_error)}")
            return None

class DataFormatter:
    @staticmethod
    def process_readings(readings: List[Dict[str, Any]], 
                        low_threshold: float, 
                        high_threshold: float) -> List[Dict[str, Any]]:
        processed = []
        seen_timestamps = set()
        
        for reading in readings:
            timestamp = reading.get('Timestamp')
            if timestamp in seen_timestamps:
                continue
            seen_timestamps.add(timestamp)
            
            try:
                value = float(reading.get('Value', 0))
                reading['isLow'] = value < low_threshold
                reading['isHigh'] = value > high_threshold
            except (ValueError, TypeError):
                reading['isLow'] = False
                reading['isHigh'] = False
            
            if 'MeasureMent' in reading:
                reading['MeasurementType'] = reading.pop('MeasureMent')
                
            processed.append(reading)
        
        return processed

    @staticmethod
    def to_csv(readings: List[Dict[str, Any]]) -> str:
        if not readings:
            return "No data available"
        df = pd.DataFrame(readings)
        return df.to_csv(index=False)

    @staticmethod
    def to_json(readings: List[Dict[str, Any]]) -> str:
        return json.dumps(readings, indent=2)

    @staticmethod
    def to_xml(readings: List[Dict[str, Any]]) -> str:
        root = ET.Element("GlucoseReadings")
        for reading in readings:
            item = ET.SubElement(root, "Reading")
            for key, value in reading.items():
                child = ET.SubElement(item, key)
                child.text = str(value) if value is not None else ""
        return ET.tostring(root, encoding='unicode')

    @staticmethod
    def to_dataframe(readings: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(readings)

class ChartGenerator:
    @staticmethod
    def create_glucose_chart(readings: List[Dict[str, Any]], chart_type: str, settings: Dict[str, Any]) -> Optional[go.Figure]:
        if not readings:
            return None
            
        df = pd.DataFrame(readings)
        if df.empty:
            return None
            
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
        df = df.sort_values('Timestamp')
        
        # Apply glucose range filtering if enabled
        if settings.get('filter_by_range', False):
            min_val = settings.get('glucose_min', 0)
            max_val = settings.get('glucose_max', 300)
            df = df[(df['Value'] >= min_val) & (df['Value'] <= max_val)]
        
        if chart_type == "line":
            fig = px.line(df, x='Timestamp', y='Value', title='Glucose Levels Over Time')
            fig.update_traces(line=dict(width=2))
        elif chart_type == "scatter":
            fig = px.scatter(df, x='Timestamp', y='Value', title='Glucose Readings Scatter Plot')
        elif chart_type == "bar":
            fig = px.bar(df, x='Timestamp', y='Value', title='Glucose Levels Bar Chart')
        elif chart_type == "histogram":
            fig = px.histogram(df, x='Value', title='Glucose Value Distribution', nbins=30)
        elif chart_type == "box":
            fig = px.box(df, y='Value', title='Glucose Value Distribution Box Plot')
        elif chart_type == "area":
            fig = px.area(df, x='Timestamp', y='Value', title='Glucose Levels Area Chart')
        elif chart_type == "heatmap":
            df['Date'] = df['Timestamp'].dt.date
            df['Time'] = df['Timestamp'].dt.hour
            pivot_df = df.pivot_table(values='Value', index='Time', columns='Date', aggfunc='mean')
            fig = px.imshow(pivot_df, title='Glucose Heatmap (Hour vs Date)')
        else:
            return None
            
        fig.update_layout(
            xaxis_title="Time" if chart_type not in ["histogram", "box", "heatmap"] else "Date" if chart_type == "heatmap" else "",
            yaxis_title="Glucose Level (mg/dL)" if chart_type != "heatmap" else "Glucose Level",
            hovermode="x unified" if chart_type not in ["histogram", "box", "heatmap"] else "closest"
        )
        return fig

class AIAnalyzer:
    def __init__(self, api_keys: Dict[str, str]):
        self.api_keys = api_keys
        if self.api_keys.get("openai_api_key"):
            litellm.openai_key = self.api_keys["openai_api_key"]
        if self.api_keys.get("anthropic_api_key"):
            litellm.anthropic_key = self.api_keys["anthropic_api_key"]
        if self.api_keys.get("gemini_api_key"):
            litellm.gemini_key = self.api_keys["gemini_api_key"]
        if self.api_keys.get("cohere_api_key"):
            litellm.cohere_key = self.api_keys["cohere_api_key"]
        if self.api_keys.get("replicate_api_key"):
            litellm.replicate_key = self.api_keys["replicate_api_key"]

    def analyze(self, readings: List[Dict[str, Any]], query: str, model: str) -> str:
        valid_readings = [r for r in readings if r.get('Value')]
        values = [float(r['Value']) for r in valid_readings]
        
        if not values:
            return "No valid glucose readings found for analysis."
        
        glucose_data = "\n".join([
            f"Time: {reading.get('Timestamp', 'N/A')}, "
            f"Value: {reading.get('Value')} {reading.get('GlucoseUnits', 'N/A')}"
            for reading in valid_readings
        ])
        
        prompt = f"""
        You are a medical data analyst specializing in glucose monitoring. Here is a set of glucose readings:

        Glucose Data:
        {glucose_data}

        Basic Statistics:
        - Number of readings: {len(values)}
        - Average glucose: {sum(values)/len(values):.1f}
        - Minimum: {min(values)}
        - Maximum: {max(values)}

        From User Query "{query}" provide clear and concise output.
        If the user requests a chart, table, or structured format, generate the appropriate visualization code or data structure.
        For charts, use Plotly syntax. For tables, use markdown table format.
        """
        
        try:
            response = litellm.completion(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as model_error:
            error_message = f"Error analyzing data with {model}: {str(model_error)}"
            file_log.error(error_message)
            return error_message

def validate_credentials(email: str, password: str) -> Tuple[bool, str]:
    if not email:
        return False, "Email is required"
    if "@" not in email:
        return False, "Invalid email format"
    if not password:
        return False, "Password is required"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, ""

def validate_api_keys(api_keys: Dict[str, str]) -> Tuple[bool, str]:
    if not any(api_keys.values()):
        return False, "At least one API key is required"
    return True, ""

def show_toast(message: str, success: bool = True):
    icon = "✅" if success else "❌"
    st.toast(message, icon=icon)

def main():
    st.set_page_config(page_title="LibreView Glucose Analyzer", layout="wide")
    st.title("🩸 LibreView Glucose Data Analyzer with Multi-AI")
    
    env_loader = EnvironmentLoader()
    defaults = env_loader.load_defaults()

    with st.sidebar:
        st.header("⚙️ Configuration")
        
        with st.expander("Account Settings", expanded=True):
            email = st.text_input("LibreView Email", value=defaults["libre_email"])
            password = st.text_input("LibreView Password", value=defaults["libre_password"], type="password")
            
            if st.button("Validate LibreView Credentials"):
                is_valid, message = validate_credentials(email, password)
                if is_valid:
                    show_toast("Credentials are valid!")
                    st.session_state['temp_credentials'] = {
                        'email': email,
                        'password': password
                    }
                else:
                    show_toast(message, success=False)
        
        with st.expander("AI Model Settings", expanded=True):
            openai_api_key = st.text_input("OpenAI API Key", value=defaults["openai_api_key"], type="password")
            anthropic_api_key = st.text_input("Anthropic API Key", value=defaults["anthropic_api_key"], type="password")
            gemini_api_key = st.text_input("Gemini API Key", value=defaults["gemini_api_key"], type="password")
            cohere_api_key = st.text_input("Cohere API Key", value=defaults["cohere_api_key"], type="password")
            replicate_api_key = st.text_input("Replicate API Key", value=defaults["replicate_api_key"], type="password")
            
            available_models = [
                "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo",
                "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
                "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash",
                "command-nightly", "command",
                "replicate/meta/llama-2-70b-chat:02e509c789964a7ea8736978a43525956ef40397be9033abf9fd2badfe68c9e3"
            ]
            selected_model = st.selectbox(
                "Select Default AI Model",
                options=available_models,
                index=available_models.index(defaults["default_model"]) if defaults["default_model"] in available_models else 0
            )
        
        with st.expander("LibreView Settings", expanded=False):
            libre_version = st.text_input("API Version", value=defaults["libre_version"])
            libre_product = st.selectbox(
                "Product",
                options=["llu.ios", "llu.android"],
                index=0 if defaults["libre_product"] == "llu.ios" else 1
            )
        
        with st.expander("Data Display Settings", expanded=False):
            glucose_min, glucose_max = st.slider(
                "Glucose Range (mg/dL)",
                min_value=0,
                max_value=500,
                value=(70, 180),
                step=1
            )
            st.info(f"Readings below {glucose_min} will be marked as LOW\nReadings above {glucose_max} will be marked as HIGH")
            
            data_formats = ["Table", "CSV", "JSON", "XML"]
            selected_format = st.selectbox(
                "Select Data Format",
                options=data_formats,
                index=0
            )
            
            # Chart settings
            st.subheader("Chart Settings")
            enable_charts = st.checkbox("Enable Chart Generation", value=True)
            if enable_charts:
                available_charts = ["line", "scatter", "bar", "histogram", "box", "area", "heatmap"]
                selected_charts = st.multiselect(
                    "Select Chart Types",
                    options=available_charts,
                    default=["line"]
                )
                filter_by_range = st.checkbox("Filter Charts by Glucose Range", value=False)
            else:
                selected_charts = []
                filter_by_range = False
        
        if st.button("💾 Save Settings"):
            api_keys = {
                "openai_api_key": openai_api_key,
                "anthropic_api_key": anthropic_api_key,
                "gemini_api_key": gemini_api_key,
                "cohere_api_key": cohere_api_key,
                "replicate_api_key": replicate_api_key
            }
            
            is_valid, message = validate_api_keys(api_keys)
            if not is_valid:
                show_toast(message, success=False)
                return
            
            st.session_state['app_settings'] = {
                'email': email,
                'password': password,
                'libre_version': libre_version,
                'libre_product': libre_product,
                'api_keys': api_keys,
                'selected_model': selected_model,
                'glucose_min': glucose_min,
                'glucose_max': glucose_max,
                'selected_format': selected_format,
                'enable_charts': enable_charts,
                'selected_charts': selected_charts,
                'filter_by_range': filter_by_range
            }
            show_toast("Settings saved successfully!")
            file_log.info("Application settings saved")
        
        if st.button("🔄 Connect to LibreView"):
            if 'app_settings' not in st.session_state:
                show_toast("Please save settings first!", success=False)
                return
                
            settings = st.session_state['app_settings']
            is_valid, message = validate_credentials(settings['email'], settings['password'])
            if not is_valid:
                show_toast(message, success=False)
                return
                
            with st.spinner("Connecting to LibreView..."):
                client_manager = LibreClientManager(
                    settings['email'], 
                    settings['password'], 
                    settings['libre_version'], 
                    settings['libre_product']
                )
                if client_manager.connect():
                    st.session_state['client_manager'] = client_manager
                    st.session_state['connections'] = client_manager.connections
                    show_toast("Connected successfully!")
                else:
                    show_toast("Failed to connect", success=False)
    
    if 'client_manager' not in st.session_state:
        st.info("👈 Please configure your settings, save them, and connect to LibreView in the sidebar")
        return
    
    client_manager = st.session_state['client_manager']
    connections = st.session_state.get('connections', [])
    settings = st.session_state.get('app_settings', {})
    
    if not connections:
        st.warning("No patient connections found")
        return
    
    patient_names = [conn.get('firstName', 'Unknown') + " " + conn.get('lastName', 'Patient') 
                     for conn in connections]
    selected_patient_idx = st.selectbox(
        "Select Patient",
        range(len(patient_names)),
        format_func=lambda x: patient_names[x]
    )
    
    selected_connection = connections[selected_patient_idx]
    patient_id = selected_connection.get('patientId')
    
    if not patient_id:
        show_toast("Invalid patient selection", success=False)
        return
    
    # Fetch patient data only if not already in session or patient changed
    if ('current_patient_data' not in st.session_state or 
        st.session_state.get('current_patient_id') != patient_id):
        with st.spinner("Fetching glucose data..."):
            raw_readings = client_manager.get_patient_data(patient_id)
            if raw_readings:
                formatter = DataFormatter()
                processed_readings = formatter.process_readings(
                    raw_readings, 
                    settings.get('glucose_min', 70), 
                    settings.get('glucose_max', 180)
                )
                st.session_state['current_patient_data'] = processed_readings
                st.session_state['current_patient_id'] = patient_id
                st.session_state['raw_readings'] = raw_readings
                file_log.info(f"Fetched and cached data for patient {patient_id}")
            else:
                st.warning("No glucose data available for this patient")
                return
    else:
        processed_readings = st.session_state['current_patient_data']
        file_log.debug("Using cached patient data")
    
    st.subheader("📊 Glucose Data")
    
    selected_format = settings.get('selected_format', 'Table')
    if selected_format == "Table":
        df = DataFormatter.to_dataframe(processed_readings)
        st.dataframe(df, use_container_width=True)
    elif selected_format == "CSV":
        csv_data = DataFormatter.to_csv(processed_readings)
        st.code(csv_data, language="csv")
    elif selected_format == "JSON":
        json_data = DataFormatter.to_json(processed_readings)
        st.code(json_data, language="json")
    elif selected_format == "XML":
        xml_data = DataFormatter.to_xml(processed_readings)
        st.code(xml_data, language="xml")
    
    # Chart generation section
    if settings.get('enable_charts', True):
        st.subheader("📈 Glucose Charts")
        selected_charts = settings.get('selected_charts', ['line'])
        
        if selected_charts and processed_readings:
            tabs = st.tabs([chart.title() for chart in selected_charts])
            
            for i, chart_type in enumerate(selected_charts):
                with tabs[i]:
                    try:
                        fig = ChartGenerator.create_glucose_chart(
                            processed_readings, 
                            chart_type, 
                            settings
                        )
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.warning(f"Could not generate {chart_type} chart")
                    except Exception as chart_error:
                        st.warning(f"Error generating {chart_type} chart: {str(chart_error)}")
                        file_log.error(f"Chart generation error for {chart_type}: {str(chart_error)}")
        elif not processed_readings:
            st.info("No data available to generate charts")
    
    st.subheader("🧠 AI Data Analysis")
    
    user_query = st.text_area(
        "Enter your question about the glucose data",
        height=100,
        placeholder="e.g., What are the average glucose levels? Show me a chart of glucose trends..."
    )
    
    if st.button("🔍 Analyze Data"):
        if not user_query:
            show_toast("Please enter a question", success=False)
            return
            
        if 'app_settings' not in st.session_state:
            show_toast("Settings not found. Please save settings first.", success=False)
            return
            
        with st.spinner(f"Analyzing data with {settings['selected_model']}..."):
            analyzer = AIAnalyzer(settings.get('api_keys', {}))
            analysis_result = analyzer.analyze(processed_readings, user_query, settings['selected_model'])
            st.markdown("### Analysis Results")
            st.markdown(analysis_result)

if __name__ == "__main__":
    try:
        main()
    except Exception as application_error:
        st.toast(f"Application error: {str(application_error)}", icon="❌")
        file_log.critical(f"Unhandled application error: {str(application_error)}")
        raise