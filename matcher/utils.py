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

def _role_key_to_display_name(role_key):
    """
    将API返回的role key转换为用户友好的显示名称
    """
    role_mapping = {
        'legal_assistant': 'Legal Assistant',
        'office_administrator': 'Office Administrator', 
        'hr_specialist': 'HR Specialist',
        'business_consultant': 'Business Consultant',
        'operations_specialist': 'Operations Specialist',
        'operations_manager': 'Operations Manager',
        'education_trainer': 'Education Trainer',
        'customer_support_specialist': 'Customer Support Specialist',
        'auditor': 'Auditor',
        'pre_sales_consultant': 'Pre-sales Consultant',
        'housekeeping_staff': 'Housekeeping Staff',
        'logistics_specialist': 'Logistics Specialist',
        'cybersecurity_specialist': 'Cybersecurity Specialist',
        'cloud_engineer': 'Cloud Engineer',
        'data_scientist': 'Data Scientist',
        'digital_marketing_specialist': 'Digital Marketing Specialist',
        'backend_developer': 'Backend Developer',
        'devops_engineer': 'DevOps Engineer',
        'frontend_web_developer': 'Frontend Web Developer',
        'media_designer': 'Media Designer',
        'content_creator': 'Content Creator',
    }
    return role_mapping.get(role_key, role_key.replace('_', ' ').title())

def parse_anomaly_analysis(analysis_data):
    """
    解析anomaly analysis数据（JSON或dict）并返回结构化的数据用于模板展示。
    返回包含职位相似性、语义异常和基准组成的完整分析。
    """
    if not analysis_data:
        return {
            'job_basic_info': {},
            'top_similar_roles': [],
            'top_anomalies': [],
            'baseline_composition': []
        }
    
    # 如果analysis_data是字符串，解析为JSON
    if isinstance(analysis_data, str):
        try:
            analysis_data = json.loads(analysis_data)
        except json.JSONDecodeError:
            print("Error: Could not parse anomaly analysis JSON")
            return None

    if not isinstance(analysis_data, dict):
        return {
            'job_basic_info': {},
            'top_similar_roles': [],
            'top_anomalies': [],
            'baseline_composition': []
        }

    # 解析基本信息
    job_basic_info = {
        'job_id': analysis_data.get('job_id', 'N/A'),
        'primary_role': analysis_data.get('role', 'unknown'),
        'industry': analysis_data.get('industry', 'unknown'),
        'job_title': analysis_data.get('job_title', 'N/A'),
        'company_name': analysis_data.get('company_name', 'N/A')
    }

    # 解析职位相似性分析 - 取前3个
    role_similarity = analysis_data.get('role_similarity_analysis', {})
    top_similar_roles = []
    if role_similarity:
        # 如果role_similarity是字符串，尝试解析为JSON
        if isinstance(role_similarity, str):
            try:
                role_similarity = json.loads(role_similarity)
            except json.JSONDecodeError:
                print("Warning: Could not parse role_similarity_analysis JSON string")
                role_similarity = {}
        
        if isinstance(role_similarity, dict):
            # 按相似度降序排序并取前3个
            sorted_roles = sorted(role_similarity.items(), key=lambda x: x[1], reverse=True)[:3]
            for role_key, similarity in sorted_roles:
                top_similar_roles.append({
                    'role': role_key,
                    'similarity': round(similarity * 100, 1),  # 转换为百分比
                    'display_name': _role_key_to_display_name(role_key)
                })

    # 解析语义异常 - 取前3个
    semantic_anomalies = analysis_data.get('semantic_anomalies', [])
    top_anomalies = []
    if semantic_anomalies:
        # 如果semantic_anomalies是字符串，尝试解析为JSON
        if isinstance(semantic_anomalies, str):
            try:
                semantic_anomalies = json.loads(semantic_anomalies)
            except json.JSONDecodeError:
                print("Warning: Could not parse semantic_anomalies JSON string")
                semantic_anomalies = []
        
        if isinstance(semantic_anomalies, list):
            for anomaly in semantic_anomalies[:3]:  # 只取前3个异常
                if isinstance(anomaly, dict):
                    top_anomalies.append({
                        'chunk': anomaly.get('chunk', 'N/A'),
                        'type': anomaly.get('type', 'Unknown'),
                        'similarity_to_primary': round(anomaly.get('similarity_to_primary_role', 0) * 100, 1),
                        'related_role': anomaly.get('related_to_role', 'unknown'),
                        'related_similarity': round(anomaly.get('related_role_similarity', 0) * 100, 1),
                        'display_related_role': _role_key_to_display_name(anomaly.get('related_to_role', 'unknown'))
                    })

    # 解析基准组成
    baseline_composition = analysis_data.get('baseline_composition', {})
    baseline_roles = []
    if baseline_composition:
        # 如果baseline_composition是字符串，尝试解析为JSON
        if isinstance(baseline_composition, str):
            try:
                baseline_composition = json.loads(baseline_composition)
            except json.JSONDecodeError:
                print("Warning: Could not parse baseline_composition JSON string")
                baseline_composition = {}
        
        if isinstance(baseline_composition, dict):
            for role_key, percentage in baseline_composition.items():
                baseline_roles.append({
                    'role': role_key,
                    'percentage': round(percentage * 100, 1),  # 转换为百分比
                    'display_name': _role_key_to_display_name(role_key)
                })
            # 按百分比降序排序
            baseline_roles.sort(key=lambda x: x['percentage'], reverse=True)

    return {
        'job_basic_info': job_basic_info,
        'top_similar_roles': top_similar_roles,
        'top_anomalies': top_anomalies,
        'baseline_composition': baseline_roles
    }


def parse_tips_string(tips_str):
    """
    将类似 '* tip1. * tip2. * tip3.' 的字符串解析为列表。
    """
    if not tips_str:
        return []
    # 以 * 分割，去除空项和前后空格
    items = [item.strip() for item in tips_str.split('*') if item.strip()]
    return items
