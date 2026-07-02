from app.parser.jd_parser import JDParser

s='We need 5+ years in python, docker, aws. Work in fintech and AI. Bangalore or remote.'
print(JDParser().parse(s).to_dict())
