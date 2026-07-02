from load_candidates import load_candidates
from feature_extractor import extract_features

candidates = load_candidates(limit=1)

features = extract_features(candidates[0])

print(features)