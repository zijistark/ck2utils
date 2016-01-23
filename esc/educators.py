educators = [
    'ambitious cruel shy envious slothful charitable',

    'lustful patient slothful deceitful gluttonous cynical',
    'zealous humble charitable deceitful',
    'arbitrary patient content brave gregarious',
    'ambitious proud gregarious paranoid craven',
    'diligent gluttonous wroth honest gregarious',
    'charitable deceitful brave humble',

    'arbitrary chaste trusting zealous patient',
    'humble content craven temperate charitable deceitful',
    'greedy envious patient deceitful gluttonous',
    'arbitrary lustful zealous gluttonous',
    'honest slothful brave zealous greedy',
    'greedy gluttonous gregarious wroth content',

    'chaste paranoid proud deceitful zealous content',
    'chaste gregarious diligent cynical',
    'gluttonous charitable kind',
    'kind charitable proud content brave',
    'gluttonous just content charitable',
    'arbitrary humble wroth chaste deceitful',

    'diligent wroth lustful deceitful kind',
    'content proud wroth cruel',
    'wroth gregarious just zealous',
    'lustful deceitful greedy arbitrary gluttonous',
    'shy charitable brave',
    'ambitious cruel shy envious slothful charitable'
]

score = {
    'diligent': 40.39,
    'kind': 34.81,
    'temperate': 30.15,
    'proud': 23.44,
    'just': 23.19,
    'brave': 13.06,
    'ambitious': 8.61,
    'honest': 7.13,
    'charitable': 6.04,
    'gregarious': 4.36,
    'patient': 2.9,
    'lustful': 0.05,
    'paranoid': 0,
    'trusting': -0.08,
    'chaste': -0.67,
    'content': -2.48,
    'cynical': -3.86,
    'zealous': -4.28,
    'humble': -5.54,
    'shy': -11.45,
    'deceitful': -12.15,
    'envious': -14.32,
    'greedy': -14.8,
    'craven': -18.5,
    'wroth': -23.82,
    'cruel': -26.38,
    'arbitrary': -29.35,
    'gluttonous': -29.85,
    'slothful': -47.43
}

import pprint
results = []
for i, edu in enumerate(educators):
    total = sum(score[t] for t in edu.split())
    results.append((total, (i, edu)))
results.sort()
pprint.pprint(results)
