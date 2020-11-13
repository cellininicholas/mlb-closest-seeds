# pip install --upgrade google-cloud-firestore
import json

try:
    with open('seeded_indexed.json') as f2: #, open('seeded_saved.json') as f1:
        # seed_2_kgids = json.load(f1)
        kgid_2_seeds = json.load(f2)
        seed_scores = {}

        for score_dict in kgid_2_seeds.values():
            # print(score_dict)
            for seed, score in score_dict.items():
                running_score = 0
                if seed in seed_scores:
                    running_score = seed_scores[seed]
                seed_scores[seed] = running_score + score

        # print (seed_scores)

        with open('seed_scores.json', 'w') as outfile:
            json.dump(seed_scores, outfile)

except IOError as e:
    print ('Operation failed: %s' % e.strerror)

# import numpy as np
# from google.cloud import firestore
# from google.api_core.exceptions import NotFound

# db = firestore.Client(project='cl-syd-botanicals')


# def generate_zs_from_seeds(seeds):
#     zs = []
#     for seed in seeds:
#         rnd = np.random.RandomState(seed)
#         z = rnd.randn(1, 512)[0].tolist()
#         name = "seed"+str(seed).zfill(4)+".png"
#         zs.append((name, z))
#     return zs

# def process_seed_pngs():
#     r = list(range(0,2))
#     zs = generate_zs_from_seeds(r)
#     doc_ref = db.collection(u'seeds')
#     for item in zs:
#         name, z  = item
#         data = {
#             u'morphs': [],
#             u'zVector': z,
#         }
#         try:
#             doc_ref.document(name).update(data)
#         except NotFound:
#             doc_ref.document(name).set(data)



# # # Add a new doc in collection 'cities' with ID 'LA'
# # db.collection(u'cities').document(u'LA').set(data)

# process_seed_pngs()