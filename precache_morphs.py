import sys, os, getopt
import json
import numpy as np
from google.cloud import firestore
from google.api_core.exceptions import NotFound

import requests
import time

db = firestore.Client(project='cl-syd-botanicals')


def precache_morphs(seed_strings, isDevEnv):
    frame_count = 64 # 36, 49, 64
    base_url = "https://stylegan-router-dev-dot-cl-syd-botanicals.ts.r.appspot.com" if isDevEnv else "http://0.0.0.0:5050"

    print(f"precache_morphs at {base_url}")
    print(" - - - - - - - - -")

    # We want to ensure that all seeds with ‘precomputed=True’ have morphs with all other seeds that have ‘precomputed=True’
    # fs_seeds = db.collection(u'seeds')

    prev_seed = None
    for seed_untrimmed in seed_strings:
        seed = seed_untrimmed.strip()
        # print("Precaching '" + seed + "'...")

        # 1- Get the document on Firstore with the appropriate seed name...
        doc_ref = db.collection(u'seeds').document(seed)
        doc = doc_ref.get()
        if doc.exists != True:
            print(u'No such document: ' + seed)
            prev_seed = seed
            continue
        seed_dict = doc.to_dict()
        # print(f'Document data: {seed_dict}')

        # 2- Check if the seed entry has already been pre-cached
        if 'precomputed' in seed_dict and seed_dict['precomputed'] == True:
            print(u'Seed already precomputed: ' + seed)
            prev_seed = seed
            continue

        # 3- Iterate through all the already computed seeds in the DB and fire a morph request for each, waiting for the result.
        #precomputed_seeds = db.collection(u'seeds').where(u'precomputed', u'==', True).stream()
        precomputed_seeds = [s for s in db.collection(u'seeds').where(u'precomputed', u'==', True).stream()]

        precomp_seed_index = 0
        morph_url = None
        print(f"Iterating through {len(precomputed_seeds)} pre-computed morphs for '{seed}'...")
        for precomp_seed in precomputed_seeds:
            # print(f'   Precomputed seed {precomp_seed_index}: {precomp_seed.id}')
            
            # Fire a morph request
            print (f"   {precomp_seed_index+1}- Requesting morph with {seed} and {precomp_seed.id}")
            morph_url = createMorph(seed, precomp_seed.id, frame_count, base_url)
            db.collection(u'seeds').document(seed).update({ 'morphURLs.'+precomp_seed.id.replace('.',''): morph_url })
            db.collection(u'seeds').document(precomp_seed.id).update({ 'morphURLs.'+seed.replace('.',''): morph_url })

            precomp_seed_index += 1

        # - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # print(f'precomp_seed_index: {precomp_seed_index}, prev_seed: {prev_seed}')
        if precomp_seed_index < 1 and prev_seed is not None:
            print("      Creating FIRST morph")
            morph_url = createMorph(prev_seed, seed, frame_count, base_url)

            # Update the seed row of the prev_seed, setting 'precomputed' to True
            db.collection(u'seeds').document(prev_seed).update({ u'precomputed': True, 
                             'morphURLs.'+seed.replace('.',''): morph_url })
            doc_ref.update({ u'precomputed': True,
                             'morphURLs.'+prev_seed.replace('.',''): morph_url })
        # - - - - - - - - - - - - - - - - - - - - - - - - - - -

        # 4-  Add/update the seed row, setting ‘precomputed’ to True
        if precomp_seed_index > 0 and morph_url is not None:
            doc_ref.update({ u'precomputed': True })

        # 5- Also update the array of ‘morphs’???

        prev_seed = seed
    
    print("precache_morphs COMPLETE")
    print(" - - - - - - - - -")

# =============================================

def createMorph(seed1, seed2, frame_count, base_url):
    # print(f'CREATE MORPH::{seed1}::{seed2}')

    json_dat = {'image1':seed1, 'image2':seed2, 'frame_count': frame_count, 'no_cache':False, 'seeded': True}
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain; charset=utf-8'}
    # pprint.pprint(json_dat)
    
    # print (f"   Requesting morph::{seed1}::{seed2}")
    start = time.time()
    response = requests.post(base_url + "/stylegan/morph", json=json_dat, headers=headers)
    if response.status_code != 200: return None
    end = time.time()

    seed_str = response.text
    print (f"         Returned in [{end - start}s]: {seed_str}")
    if isinstance(seed_str, str):
        return seed_str
    return None


# =============================================
# =============================================

def reset_all_precomputed_flags():
    print("reset_all_precomputed_flags...")

    fs_seeds = db.collection(u'seeds')

    precomputed_seeds = fs_seeds.where(u'precomputed', u'==', True).stream()
    for precomp_seed in precomputed_seeds:
        fs_seeds.document(precomp_seed.id).update({ u'precomputed': False, u'frameCount': None, u'morphURLs': None })

    print("----------------------------------")

def main(argv):
    inputtextfile = ''
    isDevEnv = True
    try:
        opts, args = getopt.getopt(argv,"hi:e:",["help","ifile=","env="])
    except getopt.GetoptError:
        print ('precache_morphs.py -i <input-textfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ('precache_morphs.py -i <input-textfile>')
            sys.exit()
        elif opt in ("-i", "--itxtfile"):
            inputtextfile = arg
        elif opt in ("-e", "--env"):
            isDevEnv = not (arg.lower() == 'prod' or arg.lower() == 'production')
    print ('Input file is ', inputtextfile)
    print (f'isDevEnv: {isDevEnv}')
    # ----------------------------------

    if os.path.exists(inputtextfile) == False:
        print(inputtextfile + " DOESN'T EXIST")
        return

    with open(inputtextfile) as f:
        content = f.readlines()
        #print (content)

        #reset_all_precomputed_flags()
        precache_morphs(content, isDevEnv)


if __name__ == "__main__":
   main(sys.argv[1:])