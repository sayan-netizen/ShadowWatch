import re
import urllib.parse
import math

def calculate_entropy(string):
    """Calculate the Shannon entropy of a string."""
    prob = [float(string.count(c)) / len(string) for c in dict.fromkeys(list(string))]
    entropy = - sum(p * math.log(p) / math.log(2.0) for p in prob)
    return entropy

def analyze_url_heuristics(url):
    """
    Performs heuristic analysis on a given URL to determine phishing risk.
    Returns a score (0-100), risk level, and a list of identified indicators.
    """
    score = 0
    indicators = []
    
    # 1. Parse URL
    try:
        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc
        path = parsed_url.path
    except Exception:
        return 100, "Critical", ["Invalid URL format"]

    # 2. Check for IP address in domain
    ip_pattern = re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    if ip_pattern.search(domain):
        score += 40
        indicators.append("Uses IP address instead of domain name")

    # 3. Check for suspicious keywords in domain or path
    suspicious_keywords = [
        'login', 'secure', 'account', 'update', 'verify', 'bank', 
        'support', 'service', 'auth', 'signin', 'paypal', 'apple', 'microsoft'
    ]
    for keyword in suspicious_keywords:
        if keyword in domain.lower() or keyword in path.lower():
            score += 15
            indicators.append(f"Suspicious keyword found: '{keyword}'")

    # 4. Check for unusually long URL
    if len(url) > 75:
        score += 10
        indicators.append("Unusually long URL length")
        
    # 5. Check for multiple subdomains
    if domain.count('.') > 3:
        score += 20
        indicators.append("Multiple subdomains detected")

    # 6. Check for URL shorteners
    shorteners = ['bit.ly', 'goo.gl', 't.co', 'tinyurl', 'is.gd', 'cli.gs', 't.me']
    for shortener in shorteners:
        if shortener in domain.lower():
            score += 30
            indicators.append("Uses a known URL shortener")

    # 7. Check HTTPS
    if parsed_url.scheme != 'https':
        score += 20
        indicators.append("Connection is not HTTPS")

    # 8. Punycode / IDNA Attack Detection
    if 'xn--' in domain.lower():
        score += 50
        indicators.append("Suspicious Punycode (IDNA) domain detected")
        
    # 9. Suspicious TLDs
    suspicious_tlds = ['.xyz', '.top', '.pw', '.tk', '.ml', '.ga', '.cf', '.gq', '.zip']
    if any(domain.lower().endswith(tld) for tld in suspicious_tlds):
        score += 30
        indicators.append("Uses a high-risk Top Level Domain (TLD)")

    # 10. URL Entropy Analysis (Detect random generated strings)
    if calculate_entropy(domain) > 4.0:
        score += 15
        indicators.append("High domain entropy (looks randomly generated)")

    # Cap score at 100
    score = min(score, 100)
    
    # Determine risk level
    if score >= 70:
        risk_level = "High"
    elif score >= 40:
        risk_level = "Medium"
    elif score > 0:
        risk_level = "Low"
    else:
        risk_level = "Safe"
        indicators.append("No suspicious indicators detected")
        
    return score, risk_level, indicators
