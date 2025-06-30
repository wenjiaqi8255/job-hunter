import json

def parse_and_prepare_insights_for_template(insights_text):
    """
    Parses the insights string into pairs for pro/con template display.
    Returns list of tuples (pro_insight, con_insight).
    """
    if not insights_text:
        return []
    
    lines = [line.strip().lstrip('* ').strip() for line in insights_text.strip().split('\n') if line.strip()]
    
    # Group lines into pairs for pro/con display
    pairs = []
    for i in range(0, len(lines), 2):
        pro = lines[i] if i < len(lines) else ""
        con = lines[i + 1] if i + 1 < len(lines) else ""
        pairs.append((pro, con))
    
    return pairs

def parse_anomaly_analysis(analysis_data):
    """
    Parses the anomaly analysis data (JSON or dict) into a list of strings for the template.
    """
    if not analysis_data:
        return []
    
    anomalies = []
    
    # If analysis_data is a string, parse it as JSON
    if isinstance(analysis_data, str):
        try:
            analysis_data = json.loads(analysis_data)
        except json.JSONDecodeError:
            return ["Error parsing anomaly data."]

    if isinstance(analysis_data, dict) and 'semantic_anomalies' in analysis_data:
        for anomaly in analysis_data.get('semantic_anomalies', []):
            anomaly_type = anomaly.get('type', 'N/A')
            chunk = anomaly.get('chunk', 'N/A')
            anomalies.append(f"{anomaly_type}: {chunk}")
            
    return anomalies
