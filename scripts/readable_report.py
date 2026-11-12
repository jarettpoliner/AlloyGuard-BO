"""Presentation-only spacing, preserving URLs, DOIs, identifiers and code verbatim."""
import re
PROTECTED=re.compile(r'(```[\s\S]*?```|`[^`\n]*`|https?://[^\s<>]+|10\.\d{4,9}/[^\s<>]+|\bG[1-8]\b)')
def readable(text):
    parts=PROTECTED.split(text)
    for i in range(0,len(parts),2):
        value=parts[i]
        value=re.sub(r'([A-Za-zÀ-ÿ])(\d)',r'\1 \2',value)
        value=re.sub(r'(\d)([A-Za-zÀ-ÿ])',r'\1 \2',value)
        value=re.sub(r'([A-Za-z]),(?=\d)',r'\1, ',value)
        value=re.sub(r'%(?=[A-Za-z])','% ',value)
        value=value.replace('et al.(', 'et al. (').replace('DOI:', 'DOI: ')
        parts[i]=value
    return ''.join(parts)
