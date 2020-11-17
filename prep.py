# pip install --upgrade google-cloud-firestore
import json
import numpy as np
from google.cloud import firestore
from google.api_core.exceptions import NotFound

db = firestore.Client(project='cl-syd-botanicals')

def generate_zs_from_seeds(seeds):
    zs = []
    for seed in seeds:
        rnd = np.random.RandomState(seed)
        z = rnd.randn(1, 512)[0].tolist()
        name = "seed"+str(seed).zfill(4)+".png"
        zs.append((name, z))
    return zs

def process_seed_pngs(seed_scores, seed_predictions_dict):
    # Accidently deleted seed13056
    count = 20000
    r = list(range(0,count))
    zs = generate_zs_from_seeds(r)
    doc_ref = db.collection(u'seeds')
    i = 0
    for item in zs:
        name, z  = item
        
        seed_score = 0
        if name in seed_scores: seed_score = seed_scores[name]

        seed_predictions = {}
        if name in seed_predictions_dict: seed_predictions = seed_predictions_dict[name]

        data = {
            u'morphs': [],
            u'zVector': z,
            u'predictionScore': seed_score,
            u'predictions': seed_predictions,
            u'precomputed': False
        }
        progress = i / count
        print( "{0}".format(progress), end="\r" )
        try:
            doc_ref.document(name).update(data)
        except NotFound:
            doc_ref.document(name).set(data)
        i += 1
    print( "COMPLETE!" )

def load_seed_score_dict():
    try:
        with open('seed_scores.json') as f:
            seed_scores = json.load(f)
            return seed_scores
    except IOError as e:
        print ('Operation failed: %s' % e.strerror)
    return None

def load_seeded_saved_dict():
    try:
        with open('seeded_saved.json') as f:
            seed_scores = json.load(f)
            return seed_scores
    except IOError as e:
        print ('Operation failed: %s' % e.strerror)
    return None

# # Add a new doc in collection 'cities' with ID 'LA'
# db.collection(u'cities').document(u'LA').set(data)

seed_scores = load_seed_score_dict()
if seed_scores is None: exit
# print (seed_scores)

seeded_saved_dict = load_seeded_saved_dict()
if seeded_saved_dict is None: exit

process_seed_pngs(seed_scores, seeded_saved_dict)