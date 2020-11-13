import sys, os, getopt
import json
import numpy as np
from google.cloud import firestore
from google.api_core.exceptions import NotFound

db = firestore.Client(project='cl-syd-botanicals')


def precache_morphs(seed_strings):
    print("precache_morphs...")
    print(" - - - - - - - - -")

    # We want to ensure that all seeds with ‘precomputed=True’ have morphs with all other seeds that have ‘precomputed=True’
    fs_seeds = db.collection(u'seeds')

    prev_seed = None
    for seed_untrimmed in seed_strings:
        seed = seed_untrimmed.strip()
        # print("Precaching '" + seed + "'...")

        # 1- Get the document on Firstore with the appropriate seed name...
        doc_ref = fs_seeds.document(seed)
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
        precomputed_seeds = fs_seeds.where(u'precomputed', u'==', True).stream()
        precomp_seed_index = 0
        for precomp_seed in precomputed_seeds:
            # print(f'   Precomputed seed {precomp_seed_index}: {precomp_seed.id}')

            # TODO: Fire a morph request
            createMorph(seed, precomp_seed.id)

            precomp_seed_index += 1

        # - - - - - - - - - - - - - - - - - - - - - - - - - - -
        # print(f'precomp_seed_index: {precomp_seed_index}, prev_seed: {prev_seed}')
        if precomp_seed_index < 1 and prev_seed is not None:
            print("      Creating FIRST morph")
            createMorph(prev_seed, seed)

            # TODO: Update the seed row of the prev_seed, setting 'precomputed' to True
            fs_seeds.document(prev_seed).update({ u'precomputed': True })
            doc_ref.update({ u'precomputed': True })
        # - - - - - - - - - - - - - - - - - - - - - - - - - - -

        # 4-  Add/update the seed row, setting ‘precomputed’ to True
        if precomp_seed_index > 0:
            doc_ref.update({ u'precomputed': True })

        # 5- Also update the array of ‘morphs’???

        prev_seed = seed
    
    print("precache_morphs COMPLETE")
    print(" - - - - - - - - -")

# =============================================

def createMorph(seed1, seed2):
    print(f'CREATE MORPH::{seed1}::{seed2}')

# =============================================
# =============================================

def reset_all_precomputed_flags():
    print("reset_all_precomputed_flags...")

    fs_seeds = db.collection(u'seeds')

    precomputed_seeds = fs_seeds.where(u'precomputed', u'==', True).stream()
    for precomp_seed in precomputed_seeds:
        fs_seeds.document(precomp_seed.id).update({ u'precomputed': False })

    print("----------------------------------")

def main(argv):
    inputtextfile = ''
    try:
        opts, args = getopt.getopt(argv,"hi:o:",["ifile="])
    except getopt.GetoptError:
        print ('precache_morphs.py -i <input-textfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print ('precache_morphs.py -i <input-textfile>')
            sys.exit()
        elif opt in ("-i", "--itxtfile"):
            inputtextfile = arg
    print ('Input file is ', inputtextfile)
    # ----------------------------------

    if os.path.exists(inputtextfile) == False:
        print(inputtextfile + " DOESN'T EXIST")
        return

    with open(inputtextfile) as f:
        content = f.readlines()
        print (content)

        reset_all_precomputed_flags()
        precache_morphs(content)


if __name__ == "__main__":
   main(sys.argv[1:])