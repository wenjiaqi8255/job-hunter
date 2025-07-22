import json
import itertools

def parse_and_prepare_insights_for_template(insights_str):
    if not insights_str or insights_str == 'N/A':
        return [] 
    
    pros = []
    cons = []
    # Normalize: remove leading/trailing whitespace, then split by '*'
    # Each item will be like " Pro: text" or " Con: text" or empty string
    items = [item.strip() for item in insights_str.strip().split('*') if item.strip()]
    
    for item in items:
        if item.startswith("Pro:"):
            pros.append(item[len("Pro:"):].strip())
        elif item.startswith("Con:"):
            cons.append(item[len("Con:"):].strip())
        # else:
            # Optionally handle items that don't fit the Pro/Con format
            # print(f"Warning: Unrecognized insight format: {item}")
            
    # Ensure we have at least one pro or con to make a table
    if not pros and not cons:
        return []

    return list(itertools.zip_longest(pros, cons, fillvalue=None))

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


def parse_tips_string(tips_str):
    """
    将类似 '* tip1. * tip2. * tip3.' 的字符串解析为列表。
    """
    if not tips_str:
        return []
    # 以 * 分割，去除空项和前后空格
    items = [item.strip() for item in tips_str.split('*') if item.strip()]
    return items
